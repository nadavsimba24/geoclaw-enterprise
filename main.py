"""
GeoClaw Enterprise — Core agent engine.

Micro features ported from nanoclaw:
  - Streaming responses (token-by-token via run_stream)
  - Retry with exponential backoff (3 attempts)
  - SQLite session persistence (history survives restarts)
  - Context window auto-truncation (never overflows)
  - Tool call loop (replaces dangerous recursion)
  - Graceful shutdown handler
  - Token estimator
"""
import os, json, time, sqlite3, signal, sys
from pathlib import Path
from typing import Generator
from dotenv import load_dotenv
from openai import OpenAI
from skills import load_skills

load_dotenv()

# ── constants ──────────────────────────────────────────────────────────────────
MAX_HISTORY_MESSAGES = 40   # keep last N user/assistant turns in memory
MAX_TOOL_ROUNDS      = 5    # max tool call loops per run (prevent infinite loops)
RETRY_ATTEMPTS       = 3    # API call retry count
DB_PATH              = Path("geoclaw_session.db")
SYSTEM_PROMPT        = (
    "You are Geo, an enterprise geo-intelligence and OSINT agent. "
    "Be concise, precise, and field-ready. Respond in 1-3 paragraphs max unless asked for more."
)


# ── helpers ────────────────────────────────────────────────────────────────────
def _estimate_tokens(messages: list) -> int:
    """Rough token estimate: ~4 chars per token (no extra deps needed)."""
    return sum(len(str(m.get("content") or "")) for m in messages) // 4


def _shutdown(sig, frame):
    print("\n[Geoclaw] Shutting down gracefully.")
    sys.exit(0)

signal.signal(signal.SIGINT,  _shutdown)
signal.signal(signal.SIGTERM, _shutdown)


# ── database ───────────────────────────────────────────────────────────────────
def _init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                role    TEXT    NOT NULL,
                content TEXT    NOT NULL,
                ts      REAL    DEFAULT (unixepoch('now'))
            )
        """)


def _load_history() -> list:
    _init_db()
    with sqlite3.connect(DB_PATH) as db:
        rows = db.execute(
            "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?",
            (MAX_HISTORY_MESSAGES,)
        ).fetchall()
    return [{"role": r, "content": c} for r, c in reversed(rows)]


def _save_message(role: str, content: str):
    if not content:
        return
    with sqlite3.connect(DB_PATH) as db:
        db.execute("INSERT INTO messages (role, content) VALUES (?, ?)", (role, content))


# ── core ───────────────────────────────────────────────────────────────────────
class GeoclawCore:

    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY", "ollama"),
            base_url=os.getenv("BASE_URL", "http://localhost:11434/v1"),
        )
        self.model  = os.getenv("MODEL_NAME", "qwen2.5:14b-instruct-q4_K_M")
        self.skills = load_skills()
        self.history: list = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.history += _load_history()

    # ── token info ─────────────────────────────────────────────────────────────
    @property
    def token_estimate(self) -> int:
        return _estimate_tokens(self.history)

    # ── context management ─────────────────────────────────────────────────────
    def _trim_history(self):
        """Keep system message + last MAX_HISTORY_MESSAGES entries."""
        non_system = [m for m in self.history if m["role"] != "system"]
        if len(non_system) > MAX_HISTORY_MESSAGES:
            self.history = [self.history[0]] + non_system[-MAX_HISTORY_MESSAGES:]

    # ── API call with retry ────────────────────────────────────────────────────
    def _call_api(self, stream: bool = False, tools: list | None = None):
        kwargs = dict(
            model    = self.model,
            messages = self.history,
            stream   = stream,
        )
        if tools:
            kwargs["tools"] = tools

        last_err = None
        for attempt in range(RETRY_ATTEMPTS):
            try:
                return self.client.chat.completions.create(**kwargs)
            except Exception as e:
                last_err = e
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(2 ** attempt)   # 1s, 2s, 4s backoff
        raise RuntimeError(f"API failed after {RETRY_ATTEMPTS} attempts: {last_err}")

    # ── tool executor ──────────────────────────────────────────────────────────
    def _run_tool(self, name: str, args_json: str) -> str:
        if name not in self.skills:
            return f"[error] Unknown skill: {name}"
        try:
            return str(self.skills[name].handler(**json.loads(args_json)))
        except Exception as e:
            return f"[error] Skill '{name}' failed: {e}"

    # ── blocking run ───────────────────────────────────────────────────────────
    def run(self, txt: str) -> str:
        """Run a full turn and return the final text response."""
        self.history.append({"role": "user", "content": txt})
        _save_message("user", txt)
        self._trim_history()

        tools = [s.to_openai_tool() for s in self.skills.values()] or None

        for _ in range(MAX_TOOL_ROUNDS):
            try:
                res = self._call_api(tools=tools)
                msg = res.choices[0].message

                if not msg.tool_calls:
                    content = msg.content or ""
                    self.history.append({"role": "assistant", "content": content})
                    _save_message("assistant", content)
                    return content

                # execute tool calls
                self.history.append(msg)
                for tc in msg.tool_calls:
                    result = self._run_tool(tc.function.name, tc.function.arguments)
                    self.history.append({
                        "role":        "tool",
                        "tool_call_id": tc.id,
                        "name":        tc.function.name,
                        "content":     result,
                    })

            except Exception as e:
                return f"[error] {e}"

        return "[error] Max tool call depth reached."

    # ── streaming run ──────────────────────────────────────────────────────────
    def run_stream(self, txt: str) -> Generator[str, None, None]:
        """
        Generator: yields text chunks as they arrive from the model.
        Tool calls are executed silently; only final text is streamed.
        Nanoclaw-inspired: show output immediately, don't make user wait.
        """
        self.history.append({"role": "user", "content": txt})
        _save_message("user", txt)
        self._trim_history()

        tools = [s.to_openai_tool() for s in self.skills.values()] or None

        for _ in range(MAX_TOOL_ROUNDS):
            try:
                stream = self._call_api(stream=True, tools=tools)

                full_content   = ""
                tc_buffer: dict[int, dict] = {}  # index → {id, name, args}

                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta  = chunk.choices[0].delta
                    finish = chunk.choices[0].finish_reason

                    # stream text tokens
                    if delta.content:
                        full_content += delta.content
                        yield delta.content

                    # accumulate tool call fragments
                    if delta.tool_calls:
                        for tc in delta.tool_calls:
                            buf = tc_buffer.setdefault(tc.index, {"id": "", "name": "", "args": ""})
                            if tc.id:
                                buf["id"] = tc.id
                            if tc.function:
                                buf["name"] += tc.function.name or ""
                                buf["args"] += tc.function.arguments or ""

                # done streaming this round
                if full_content and not tc_buffer:
                    self.history.append({"role": "assistant", "content": full_content})
                    _save_message("assistant", full_content)
                    return

                if tc_buffer:
                    if full_content:
                        self.history.append({"role": "assistant", "content": full_content})

                    yield "\n\n"
                    for buf in tc_buffer.values():
                        yield f"[tool: {buf['name']}]\n"
                        result = self._run_tool(buf["name"], buf["args"])
                        self.history.append({
                            "role":         "tool",
                            "tool_call_id": buf["id"],
                            "name":         buf["name"],
                            "content":      result,
                        })
                        yield f"→ {result}\n\n"
                    continue   # loop: get final response after tools

            except Exception as e:
                yield f"[error] {e}"
                return

        yield "[error] Max tool call depth reached."
