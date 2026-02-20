# Cloud / VPS Deployment

1. **Create VM** (Ubuntu 22.04 LTS recommended, 2 vCPU, 2 GB RAM).
2. **SSH in** and clone the repo:
   ```bash
   git clone https://github.com/nadavsimba24/geoclaw-enterprise.git
   cd geoclaw-enterprise
   ```
3. **Run the installer**:
   ```bash
   chmod +x install_vps.sh
   ./install_vps.sh
   ```
   - Installs Python, git, creates `.venv`, installs requirements.
4. **Configure secrets**:
   ```bash
   source .venv/bin/activate
   python configure.py
   ```
5. **Run headless**:
   ```bash
   python main.py --persona forager --skills-dir skills
   ```
   or keep the TUI in `tmux`:
   ```bash
   tmux new -s geoclaw "python tui.py --text-only"
   ```
6. **Optional service**: create `/etc/systemd/system/geoclaw.service` with:
   ```ini
   [Unit]
   Description=Geoclaw Agent
   After=network.target

   [Service]
   WorkingDirectory=/home/ubuntu/geoclaw-enterprise
   ExecStart=/home/ubuntu/geoclaw-enterprise/.venv/bin/python main.py
   Restart=on-failure
   Environment=OPENAI_MODEL=gpt-4o-mini

   [Install]
   WantedBy=multi-user.target
   ```
   Then run `sudo systemctl enable --now geoclaw`.

## Firewall Ports
Only outbound HTTPS (443) is required for OpenAI default. If exposing APIs/webhooks, open specific inbound ports as needed.
