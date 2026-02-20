# Edge Deployment Guide

These steps keep Geoclaw Enterprise running smoothly on low-power or offline-first hardware.

## 1. Hardware Checklist
- 2+ CPU cores (ARM64 or x86_64)
- 2 GB RAM minimum (512 MB headroom during idle)
- 4 GB free disk (keeps venv + cached data comfortable)
- Optional: GPS dongle / LTE modem for mobile kits

## 2. Install Flow (compressed)
```bash
curl -L https://raw.githubusercontent.com/nadavsimba24/geoclaw-enterprise/main/install.sh -o install.sh
chmod +x install.sh
./install.sh --minimal  # add this flag to skip heavy extras
```

If Python is missing, ship a prebuilt portable interpreter (PyApp, uv, or a zipapp) and drop Geoclaw next to it.

## 3. Runtime Flags
- `python tui.py --text-only` → disables rich tabs, perfect for serial consoles
- `python main.py --skills-dir skills/forager` → load only the essentials
- `OPENAI_MODEL=gpt-4o-mini` (or Claude Haiku) in `.env` for cheaper inference

## 4. Data + Sync Strategy
- Use `memory/` folder (coming soon) or plain JSON to log findings locally.
- Set up a nightly `rsync`/S3 sync job so the hive map stays current even for offline bees.
- Keep secrets in `.env` and rotate with `python configure.py --rotate` (todo).

## 5. Health Checks
- `python main.py --ping` returns 0 if the stack responds.
- Add a cron entry to upload `logs/runtime.log` so HQ can see when a bee disappears.

## 6. Hardening Tips
- Run under a dedicated OS user.
- Use firewall rules (`pf`, `ufw`, Windows Firewall) to limit outbound targets.
- For field kits, enable full-disk encryption and auto-lock after 5 minutes.

With these guardrails a “bee” can run indefinitely on fanless hardware, wake up on schedule, and keep feeding the hive map.
