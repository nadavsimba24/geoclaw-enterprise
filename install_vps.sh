#!/usr/bin/env bash
# Automated installer for VPS (Ubuntu/Debian/Rocky like systems)
set -euo pipefail

if [[ $EUID -eq 0 ]]; then
  echo "[!] Please run as a non-root user with sudo access." >&2
  exit 1
fi

echo "[Geoclaw] Updating packages..."
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip git

if [[ ! -d .venv ]]; then
  echo "[Geoclaw] Creating virtualenv..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[Geoclaw] Installation complete. Next run:"
echo "source .venv/bin/activate && python configure.py && python main.py"
