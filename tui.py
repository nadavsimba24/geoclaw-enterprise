"""
GeoClaw Enterprise — Terminal UI.

Micro features from nanoclaw:
  - Streaming output (tokens appear as they're generated)
  - Scrollable chat history (RichLog)
  - Token counter in footer
  - Model name display in header
  - Keyboard shortcuts (Ctrl+L clear, Ctrl+N new session)
"""
import os
from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, RichLog, TabbedContent, TabPane, Static
from textual.binding import Binding
from textual import work
from main import GeoclawCore

load_dotenv()

WELCOME = (
    "[bold blue]GeoClaw Enterprise v3.0[/bold blue]  🌍🐝\n"
    "[dim]Type a message and press Enter. Ctrl+L to clear. Ctrl+N for new session.[/dim]\n"
    "─" * 52
)


class GeoclawTUI(App):
    CSS = """
    Screen         { background: #0f172a; color: #e2e8f0; }
    RichLog        { border: solid #1e3a5f; background: #0f172a; padding: 1 2; }
    Input          { dock: bottom; border: solid #1e3a5f; background: #0d1f35; color: #e2e8f0; }
    #status_bar    { dock: bottom; height: 1; background: #1e293b; color: #64748b;
                     padding: 0 2; text-align: right; }
    TabPane        { padding: 0; }
    """

    BINDINGS = [
        Binding("ctrl+l", "clear_chat",   "Clear",       show=True),
        Binding("ctrl+n", "new_session",  "New session", show=True),
        Binding("ctrl+q", "quit",         "Quit",        show=True),
    ]

    def compose(self) -> ComposeResult:
        self.bot = GeoclawCore()
        model_short = os.getenv("MODEL_NAME", "?").split("/")[-1][:24]
        yield Header(show_clock=True)
        with TabbedContent():
            with TabPane("💬 Chat", id="tab_chat"):
                yield RichLog(id="chat_log", markup=True, wrap=True, highlight=True)
                yield Static("", id="status_bar")
                yield Input(placeholder="Message Geo...", id="chat_in")
            with TabPane("🌍 Geo-Intel", id="tab_geo"):
                yield RichLog(id="geo_log", markup=True, wrap=True)
        yield Footer()

    def on_mount(self):
        log = self.query_one("#chat_log", RichLog)
        log.write(WELCOME)
        self._update_status()

    # ── input handler ──────────────────────────────────────────────────────────
    async def on_input_submitted(self, event):
        txt = event.value.strip()
        if not txt:
            return
        event.input.value = ""
        event.input.disabled = True

        log = self.query_one("#chat_log", RichLog)
        log.write(f"\n[bold cyan]You:[/bold cyan] {txt}")
        log.write("[bold green]Geo:[/bold green] ", end="")
        self._stream_response(txt)

    # ── streaming worker ───────────────────────────────────────────────────────
    @work(thread=True)
    def _stream_response(self, txt: str):
        log      = self.query_one("#chat_log", RichLog)
        inp      = self.query_one("#chat_in",  Input)
        first    = True

        for chunk in self.bot.run_stream(txt):
            if first:
                first = False
            # push each chunk to UI from thread
            self.call_from_thread(log.write, chunk, end="")

        # newline after response + re-enable input
        self.call_from_thread(log.write, "\n")
        self.call_from_thread(self._update_status)
        self.call_from_thread(setattr, inp, "disabled", False)
        self.call_from_thread(inp.focus)

    # ── status bar ─────────────────────────────────────────────────────────────
    def _update_status(self):
        model = os.getenv("MODEL_NAME", "?")
        tokens = self.bot.token_estimate
        turns  = max(0, len([m for m in self.bot.history if m["role"] == "user"]))
        self.query_one("#status_bar", Static).update(
            f"model: {model}  │  ~{tokens:,} tokens  │  {turns} turns"
        )

    # ── actions ────────────────────────────────────────────────────────────────
    def action_clear_chat(self):
        log = self.query_one("#chat_log", RichLog)
        log.clear()
        log.write(WELCOME)

    def action_new_session(self):
        import sqlite3
        from main import DB_PATH
        with sqlite3.connect(DB_PATH) as db:
            db.execute("DELETE FROM messages")
        self.bot.history = self.bot.history[:1]   # keep system prompt only
        log = self.query_one("#chat_log", RichLog)
        log.clear()
        log.write(WELCOME)
        log.write("[dim]── New session started ──[/dim]")
        self._update_status()


if __name__ == "__main__":
    GeoclawTUI().run()
