#!/usr/bin/env bash
# Guided menu for configuring Geoclaw after install
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"
CONFIG_FILE="$PROJECT_ROOT/geoclaw.config.yml"
VENV_BIN="$PROJECT_ROOT/.venv/bin"
PYTHON_BIN="$VENV_BIN/python3"

if [[ -x "$VENV_BIN/activate" ]]; then
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
    echo "Created $ENV_FILE"
  fi
}

configure_keys() {
  if [[ -f "$PROJECT_ROOT/configure.py" ]]; then
    echo "Running python configure.py ..."
    "$PYTHON_BIN" "$PROJECT_ROOT/configure.py"
  else
    echo "configure.py missing. Skipping."
  fi
}

update_model() {
  ensure_env
  read -rp "Model provider [openai]: " provider
  provider=${provider:-openai}
  read -rp "Model name [$1]: " model
  model=${model:-$1}
  python3 - "$ENV_FILE" "$provider" "$model" <<'PY'
import sys
from pathlib import Path
env_path, provider, model = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
lines = []
if env_path.exists():
    lines = env_path.read_text().splitlines()
kv = {k: v for line in lines if (line.strip() and not line.strip().startswith('#'))
      for k, v in [line.split('=', 1)]}
kv['GEOCLAW_MODEL_PROVIDER'] = provider
kv['GEOCLAW_MODEL_NAME'] = model
if 'OPENAI_MODEL' in kv:
    kv['OPENAI_MODEL'] = model
contents = '\n'.join(f"{k}={v}" for k, v in kv.items()) + '\n'
env_path.write_text(contents)
print(f"Updated {env_path} with provider={provider}, model={model}")
PY
}

manage_skills() {
  if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "Missing $CONFIG_FILE"
    return
  fi
  read -rp "Install recommended skill bundle (gemini, weather, nano-pdf, openai-whisper)? [Y/n] " ans
  ans=${ans:-Y}
  if [[ $ans == [Nn]* ]]; then
    return
  fi
  "$PYTHON_BIN" - <<'PY'
from pathlib import Path
import yaml
cfg_path = Path("geoclaw.config.yml")
cfg = yaml.safe_load(cfg_path.read_text())
skills = cfg.get('agent', {}).get('skills') or []
recommended = ["gemini", "weather", "nano-pdf", "openai-whisper"]
for name in recommended:
    if name not in skills:
        skills.append(name)
cfg['agent']['skills'] = skills
cfg_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True))
print("Updated agent.skills with recommended bundle.")
print("Reminder: run 'openclaw skills install <skill>.skill' for any external bundles.")
PY
}

while true; do
  cat <<'MENU'
================ Geoclaw Post-Install ================
1) Configure API keys (python configure.py)
2) Update default model/provider (.env)
3) Install recommended skill bundle (updates geoclaw.config.yml)
4) Skip / finish
MENU
  read -rp "Select option [1-4]: " choice
  case "$choice" in
    1) configure_keys ;;
    2) update_model "gpt-4o-mini" ;;
    3) manage_skills ;;
    4) echo "Post-install complete."; break ;;
    *) echo "Invalid option" ;;
  esac
done
