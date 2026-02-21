#!/usr/bin/env bash
# GeoClaw post-install configuration menu
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
VENV_BIN="$PROJECT_ROOT/.venv/bin"
PYTHON_BIN="$VENV_BIN/python3"

info()    { printf "\033[0;34m[Geoclaw]\033[0m %s\n" "$1"; }
success() { printf "\033[0;32m[Geoclaw]\033[0m %s\n" "$1"; }
warn()    { printf "\033[0;33m[Geoclaw]\033[0m %s\n" "$1"; }

# activate venv if available
if [[ -f "$VENV_BIN/activate" ]]; then
  # shellcheck disable=SC1090
  source "$VENV_BIN/activate"
fi

ensure_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    if [[ -f "$PROJECT_ROOT/.env.example" ]]; then
      cp "$PROJECT_ROOT/.env.example" "$ENV_FILE"
    else
      touch "$ENV_FILE"
    fi
    info "Created $ENV_FILE"
  fi
}

write_env() {
  ensure_env
  local key="$1" val="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i.bak "s|^${key}=.*|${key}=${val}|" "$ENV_FILE" && rm -f "${ENV_FILE}.bak"
  else
    echo "${key}=${val}" >> "$ENV_FILE"
  fi
}

configure_wizard() {
  info "Launching configuration wizard..."
  "$PYTHON_BIN" "$PROJECT_ROOT/configure.py"
}

setup_local_model() {
  if ! command -v ollama &>/dev/null; then
    warn "Ollama is not installed."
    echo ""
    echo "  Install it first:"
    echo "    macOS:  brew install ollama"
    echo "    Linux:  curl -fsSL https://ollama.com/install.sh | sh"
    return
  fi

  echo ""
  echo "  Recommended local models:"
  echo "  [1] qwen2.5:14b-instruct-q4_K_M  — Best overall  (~9 GB) ★"
  echo "  [2] phi4:14b-q4_K_M              — Best reasoning (~9 GB)"
  echo "  [3] qwen2.5-coder:7b             — Fast code help (~5 GB)"
  echo "  [4] deepseek-r1:1.5b             — Ultra-fast     (~1 GB)"
  echo ""
  INSTALLED=$(ollama list 2>/dev/null | tail -n +2 | awk '{print $1}' | tr '\n' ' ')
  [[ -n "$INSTALLED" ]] && info "Already installed: $INSTALLED"
  echo ""
  read -rp "  Select [1-4]: " choice

  case "$choice" in
    1) MODEL="qwen2.5:14b-instruct-q4_K_M" ;;
    2) MODEL="phi4:14b-q4_K_M" ;;
    3) MODEL="qwen2.5-coder:7b" ;;
    4) MODEL="deepseek-r1:1.5b" ;;
    *) read -rp "  Enter model name: " MODEL ;;
  esac

  if ! ollama list 2>/dev/null | grep -q "^${MODEL}"; then
    info "Downloading $MODEL..."
    ollama pull "$MODEL"
  else
    success "$MODEL already installed."
  fi

  write_env "OPENAI_API_KEY" "ollama"
  write_env "BASE_URL"       "http://localhost:11434/v1"
  write_env "MODEL_NAME"     "$MODEL"
  write_env "GEOCLAW_MODEL_PROVIDER" "ollama"
  success "Local model ready: $MODEL"
}

show_status() {
  echo ""
  if [[ -f "$ENV_FILE" ]]; then
    info "Current .env:"
    while IFS='=' read -r key val; do
      [[ -z "$key" || "$key" == \#* ]] && continue
      if [[ "$key" == *KEY* && "$val" != "ollama" && "$val" != "YOUR_API_KEY_HERE" ]]; then
        val="****${val: -4}"
      fi
      printf "  %-30s %s\n" "$key" "$val"
    done < "$ENV_FILE"
  else
    warn ".env not found."
  fi
  echo ""
}

while true; do
  echo ""
  echo "════════════ GeoClaw Configuration ════════════"
  echo " [1] Full setup wizard (cloud API or local model)"
  echo " [2] Quick: set up local model via Ollama"
  echo " [3] Show current config (.env)"
  echo " [4] Exit"
  echo "═══════════════════════════════════════════════"
  read -rp " Select [1-4]: " choice

  case "$choice" in
    1) configure_wizard ;;
    2) setup_local_model ;;
    3) show_status ;;
    4) success "Done! Run: python tui.py"; break ;;
    *) warn "Invalid option" ;;
  esac
done
