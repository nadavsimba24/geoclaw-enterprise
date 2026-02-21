#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="python3"

info() { printf "[Geoclaw] %s\n" "$1"; }

MINIMAL=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --minimal)
      MINIMAL=true
      shift
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

info "Installing Geoclaw Enterprise..."
if [[ ! -x "$(command -v python3)" ]]; then
  echo "python3 is required" >&2
  exit 1
fi

$PYTHON_BIN -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
info "Base install complete."

run_post_install() {
  local script="scripts/postinstall_menu.sh"
  if [[ -x "$script" ]]; then
    "$script"
  else
    info "Post-install script not found ($script)."
  fi
}

if [[ "$MINIMAL" == "true" ]]; then
  info "Minimal flag detected — run scripts/postinstall_menu.sh later to configure."
else
  read -rp "Launch post-install wizard now? [Y/n] " reply
  reply=${reply:-Y}
  if [[ $reply == [Nn]* ]]; then
    info "Skip selected. Run scripts/postinstall_menu.sh when ready."
  else
    run_post_install
  fi
fi

info "Done! Activate with: source .venv/bin/activate"
info "Then run: python main.py --skills-dir skills"
