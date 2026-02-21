#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="python3"
ENV_FILE="$PROJECT_ROOT/.env"

# ── helpers ────────────────────────────────────────────────────────────────────
info()    { printf "\033[0;34m[Geoclaw]\033[0m %s\n" "$1"; }
success() { printf "\033[0;32m[Geoclaw]\033[0m %s\n" "$1"; }
warn()    { printf "\033[0;33m[Geoclaw]\033[0m %s\n" "$1"; }
error()   { printf "\033[0;31m[Geoclaw]\033[0m %s\n" "$1" >&2; }
line()    { printf "\033[0;34m%s\033[0m\n" "──────────────────────────────────────────"; }

MINIMAL=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --minimal) MINIMAL=true; shift ;;
    *) error "Unknown option: $1"; exit 1 ;;
  esac
done

# ── python check ───────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  error "python3 is required but not found. Install it from https://python.org"
  exit 1
fi

# ── venv + deps ────────────────────────────────────────────────────────────────
info "Setting up Python environment..."
$PYTHON_BIN -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r "$PROJECT_ROOT/requirements.txt" -q
success "Dependencies installed."
line

# ── minimal mode: skip wizard ──────────────────────────────────────────────────
if [[ "$MINIMAL" == "true" ]]; then
  info "Minimal mode — run scripts/postinstall_menu.sh when ready to configure."
  info "Done! Activate: source .venv/bin/activate  |  Run: python tui.py"
  exit 0
fi

# ── welcome ────────────────────────────────────────────────────────────────────
echo ""
echo "  🐝  Welcome to GeoClaw Enterprise v3.0"
echo "  ─────────────────────────────────────"
echo "  Autonomous agents for geo-intelligence and OSINT."
echo ""
line

# ── choose mode ────────────────────────────────────────────────────────────────
echo ""
echo "  How do you want to run GeoClaw?"
echo ""
echo "  [1] ☁️   Cloud API   — connect to OpenAI, DeepSeek, or OpenRouter"
echo "             Fastest responses. Requires an API key. May cost money."
echo ""
echo "  [2] 🖥️   Local model — download and run AI on your machine"
echo "             100% free, private, works offline. Needs ~10 GB disk."
echo ""
echo "  [3] ⏩  Skip for now — I'll configure later"
echo ""
read -rp "  Select [1/2/3]: " MODE_CHOICE
MODE_CHOICE=${MODE_CHOICE:-1}
line

# ── ensure .env exists ─────────────────────────────────────────────────────────
if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
    cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
  else
    touch "$ENV_FILE"
  fi
fi

write_env() {
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i.bak "s|^${key}=.*|${key}=${val}|" "$ENV_FILE" && rm -f "${ENV_FILE}.bak"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

# ══════════════════════════════════════════════════════════════════════════════
# MODE 1 — Cloud API
# ══════════════════════════════════════════════════════════════════════════════
if [[ "$MODE_CHOICE" == "1" ]]; then
  echo ""
  echo "  Choose your cloud provider:"
  echo ""
  echo "  [1] OpenAI       — GPT-4o, GPT-4o-mini  (https://platform.openai.com)"
  echo "  [2] DeepSeek     — deepseek-chat  (https://platform.deepseek.com)  ← cheapest"
  echo "  [3] OpenRouter   — access 100+ models (https://openrouter.ai)"
  echo "  [4] Custom       — any OpenAI-compatible API"
  echo ""
  read -rp "  Select provider [1-4]: " PROVIDER_CHOICE
  PROVIDER_CHOICE=${PROVIDER_CHOICE:-1}
  echo ""

  case "$PROVIDER_CHOICE" in
    1)
      PROVIDER_NAME="openai"
      BASE_URL="https://api.openai.com/v1"
      DEFAULT_MODEL="gpt-4o-mini"
      KEY_HINT="Get your key at: https://platform.openai.com/api-keys"
      ;;
    2)
      PROVIDER_NAME="deepseek"
      BASE_URL="https://api.deepseek.com/v1"
      DEFAULT_MODEL="deepseek-chat"
      KEY_HINT="Get your key at: https://platform.deepseek.com"
      ;;
    3)
      PROVIDER_NAME="openrouter"
      BASE_URL="https://openrouter.ai/api/v1"
      DEFAULT_MODEL="openrouter/auto"
      KEY_HINT="Get your key at: https://openrouter.ai/keys"
      ;;
    4)
      PROVIDER_NAME="custom"
      read -rp "  Base URL (e.g. http://localhost:8080/v1): " BASE_URL
      DEFAULT_MODEL="your-model-name"
      KEY_HINT="Enter the API key for your custom provider"
      ;;
    *)
      warn "Invalid choice, defaulting to OpenAI."
      PROVIDER_NAME="openai"
      BASE_URL="https://api.openai.com/v1"
      DEFAULT_MODEL="gpt-4o-mini"
      KEY_HINT="Get your key at: https://platform.openai.com/api-keys"
      ;;
  esac

  echo "  $KEY_HINT"
  read -rsp "  Paste your API key (hidden): " API_KEY
  echo ""

  if [[ -z "$API_KEY" ]]; then
    warn "No API key entered. You can set it later in .env (OPENAI_API_KEY=...)."
    API_KEY="YOUR_API_KEY_HERE"
  fi

  read -rp "  Model name [$DEFAULT_MODEL]: " MODEL_NAME
  MODEL_NAME=${MODEL_NAME:-$DEFAULT_MODEL}

  write_env "OPENAI_API_KEY"         "$API_KEY"
  write_env "BASE_URL"               "$BASE_URL"
  write_env "MODEL_NAME"             "$MODEL_NAME"
  write_env "GEOCLAW_MODEL_PROVIDER" "$PROVIDER_NAME"

  success "Cloud API configured: $PROVIDER_NAME / $MODEL_NAME"

# ══════════════════════════════════════════════════════════════════════════════
# MODE 2 — Local model via Ollama
# ══════════════════════════════════════════════════════════════════════════════
elif [[ "$MODE_CHOICE" == "2" ]]; then
  echo ""
  # check Ollama
  if ! command -v ollama &>/dev/null; then
    warn "Ollama is not installed."
    echo ""
    echo "  Install it first:"
    echo "    macOS:  brew install ollama"
    echo "    Linux:  curl -fsSL https://ollama.com/install.sh | sh"
    echo "    Or visit: https://ollama.com/download"
    echo ""
    read -rp "  Once installed, press Enter to continue (or Ctrl+C to exit)..." _
    if ! command -v ollama &>/dev/null; then
      error "Ollama still not found. Re-run install.sh after installing Ollama."
      exit 1
    fi
  fi

  # start Ollama if not running
  if ! curl -s http://localhost:11434 &>/dev/null; then
    info "Starting Ollama service..."
    ollama serve &>/dev/null &
    sleep 3
  fi

  success "Ollama is ready."
  echo ""
  echo "  Recommended local models for GeoClaw:"
  echo ""
  echo "  [1] qwen2.5:14b-instruct-q4_K_M  — Best overall  (~9 GB) ★ Recommended"
  echo "  [2] phi4:14b-q4_K_M              — Best reasoning (~9 GB)"
  echo "  [3] qwen2.5-coder:7b             — Fast code help (~5 GB)"
  echo "  [4] deepseek-r1:1.5b             — Ultra-fast, minimal (~1 GB)"
  echo "  [5] Custom                       — Enter a model name manually"
  echo ""

  # show already-installed models
  INSTALLED=$(ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' | tr '\n' ' ')
  if [[ -n "$INSTALLED" ]]; then
    info "Already installed on this machine: $INSTALLED"
  fi
  echo ""

  read -rp "  Select model [1-5]: " MODEL_CHOICE
  MODEL_CHOICE=${MODEL_CHOICE:-1}

  case "$MODEL_CHOICE" in
    1) LOCAL_MODEL="qwen2.5:14b-instruct-q4_K_M" ;;
    2) LOCAL_MODEL="phi4:14b-q4_K_M" ;;
    3) LOCAL_MODEL="qwen2.5-coder:7b" ;;
    4) LOCAL_MODEL="deepseek-r1:1.5b" ;;
    5)
      read -rp "  Enter model name (e.g. llama3.2:3b): " LOCAL_MODEL
      ;;
    *)
      warn "Invalid choice, defaulting to qwen2.5:14b-instruct-q4_K_M"
      LOCAL_MODEL="qwen2.5:14b-instruct-q4_K_M"
      ;;
  esac

  # pull if not already installed
  if ollama list 2>/dev/null | grep -q "^${LOCAL_MODEL}"; then
    success "$LOCAL_MODEL is already installed — skipping download."
  else
    echo ""
    info "Downloading $LOCAL_MODEL (this may take a few minutes)..."
    ollama pull "$LOCAL_MODEL"
    success "$LOCAL_MODEL downloaded."
  fi

  write_env "OPENAI_API_KEY"         "ollama"
  write_env "BASE_URL"               "http://localhost:11434/v1"
  write_env "MODEL_NAME"             "$LOCAL_MODEL"
  write_env "GEOCLAW_MODEL_PROVIDER" "ollama"

  success "Local model configured: $LOCAL_MODEL (via Ollama)"

# ══════════════════════════════════════════════════════════════════════════════
# MODE 3 — Skip
# ══════════════════════════════════════════════════════════════════════════════
else
  warn "Skipped. Edit .env manually or run: scripts/postinstall_menu.sh"
fi

# ── verify .env is usable ──────────────────────────────────────────────────────
line
echo ""
if [[ -f "$ENV_FILE" ]]; then
  MODEL_SET=$(grep "^MODEL_NAME=" "$ENV_FILE" 2>/dev/null | cut -d= -f2 || true)
  if [[ -n "$MODEL_SET" && "$MODEL_SET" != "YOUR_MODEL_HERE" ]]; then
    success "Configuration looks good. Model: $MODEL_SET"
  else
    warn "MODEL_NAME not set in .env — run scripts/postinstall_menu.sh to configure."
  fi
fi

echo ""
echo "  ✅ GeoClaw is ready!"
echo ""
echo "  Activate env :  source .venv/bin/activate"
echo "  Launch TUI   :  python tui.py"
echo "  Headless mode:  python main.py --skills-dir skills"
echo "  Reconfigure  :  scripts/postinstall_menu.sh"
echo ""
line
