"""
GeoClaw Enterprise — interactive configuration wizard.
Supports: OpenAI, DeepSeek, OpenRouter, Ollama (local), Custom.
"""
import os
import subprocess
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.table import Table
    from dotenv import set_key, dotenv_values
except ImportError:
    print("Missing dependencies. Run: pip install -r requirements.txt")
    sys.exit(1)

console = Console()
ENV_PATH = Path(".env")

PROVIDERS = {
    "1": {
        "name": "OpenAI",
        "key_name": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
        "key_hint": "https://platform.openai.com/api-keys",
        "needs_key": True,
    },
    "2": {
        "name": "DeepSeek",
        "key_name": "OPENAI_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "key_hint": "https://platform.deepseek.com",
        "needs_key": True,
    },
    "3": {
        "name": "OpenRouter",
        "key_name": "OPENAI_API_KEY",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "openrouter/auto",
        "models": ["openrouter/auto", "google/gemini-flash-1.5", "meta-llama/llama-3.1-70b-instruct"],
        "key_hint": "https://openrouter.ai/keys",
        "needs_key": True,
    },
    "5": {
        "name": "Custom",
        "key_name": "OPENAI_API_KEY",
        "base_url": "",
        "default_model": "",
        "models": [],
        "key_hint": "Any OpenAI-compatible API endpoint",
        "needs_key": True,
    },
}

LOCAL_MODELS = [
    # (id,                             size,     tier,   description)
    ("smollm2:1.7b",                  "~1.0 GB", "TINY",   "Very fast, good quality for size"),
    ("deepseek-r1:1.5b",             "~1.1 GB", "TINY",   "Reasoning model, great for Q&A"),
    ("qwen2.5:1.5b",                 "~1.0 GB", "TINY",   "Compact multilingual"),
    ("llama3.2:3b",                  "~2.0 GB", "LIGHT",  "Meta's latest small model ★"),
    ("qwen2.5:3b",                   "~1.9 GB", "LIGHT",  "Fast, smart, multilingual"),
    ("phi3.5:3.8b",                  "~2.2 GB", "LIGHT",  "Microsoft — punches above weight"),
    ("gemma2:2b",                    "~1.6 GB", "LIGHT",  "Google — clean and reliable"),
    ("qwen2.5-coder:7b",             "~4.7 GB", "LIGHT",  "Best for coding tasks ★"),
    ("qwen2.5:14b-instruct-q4_K_M", "~9.0 GB", "MEDIUM", "Best overall quality ★★"),
    ("phi4:14b-q4_K_M",             "~9.1 GB", "MEDIUM", "Best reasoning & math ★★"),
    ("llama3.1:8b",                  "~4.7 GB", "MEDIUM", "Meta — great all-rounder"),
    ("mistral:7b",                   "~4.1 GB", "MEDIUM", "Fast, instruction-tuned"),
]

TIER_COLORS = {
    "TINY":   "yellow",
    "LIGHT":  "green",
    "MEDIUM": "cyan",
}


def ensure_env():
    if not ENV_PATH.exists():
        ENV_PATH.touch()


def write_env(key: str, value: str):
    ensure_env()
    set_key(str(ENV_PATH), key, value)


def get_installed_ollama_models() -> list[str]:
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        lines = result.stdout.strip().splitlines()[1:]  # skip header
        return [line.split()[0] for line in lines if line.strip()]
    except Exception:
        return []


def ollama_available() -> bool:
    try:
        subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        return True
    except Exception:
        return False


def pull_ollama_model(model: str):
    console.print(f"\n  [blue]Downloading {model}... (this may take a few minutes)[/blue]")
    result = subprocess.run(["ollama", "pull", model])
    if result.returncode != 0:
        console.print(f"  [red]Failed to pull {model}. Check your internet connection.[/red]")
        return False
    console.print(f"  [green]✓ {model} downloaded successfully.[/green]")
    return True


def configure_cloud(provider_id: str):
    p = PROVIDERS[provider_id]
    console.print(f"\n  [blue]Provider:[/blue] {p['name']}")
    console.print(f"  [dim]{p['key_hint']}[/dim]\n")

    # API key
    if p["needs_key"]:
        api_key = Prompt.ask("  API key (input hidden)", password=True)
        if not api_key.strip():
            console.print("  [yellow]No key entered — you can set it later in .env[/yellow]")
            api_key = "YOUR_API_KEY_HERE"
    else:
        api_key = "ollama"

    # base URL (custom only)
    base_url = p["base_url"]
    if provider_id == "5":
        base_url = Prompt.ask("  Base URL", default="http://localhost:8080/v1")

    # model
    if p["models"]:
        table = Table(show_header=False, box=None, padding=(0, 2))
        for i, m in enumerate(p["models"], 1):
            table.add_row(f"[dim]{i})[/dim]", m)
        console.print(table)
        choice = Prompt.ask("  Model", default=p["default_model"])
        try:
            idx = int(choice) - 1
            model = p["models"][idx] if 0 <= idx < len(p["models"]) else choice
        except ValueError:
            model = choice
    else:
        model = Prompt.ask("  Model name", default=p["default_model"])

    write_env("OPENAI_API_KEY", api_key)
    write_env("BASE_URL", base_url)
    write_env("MODEL_NAME", model)
    write_env("GEOCLAW_MODEL_PROVIDER", p["name"].lower().split()[0])

    console.print(f"\n  [green]✓ Configured:[/green] {p['name']} / {model}")


def configure_ollama():
    if not ollama_available():
        console.print("\n  [yellow]Ollama is not installed.[/yellow]")
        console.print("  Install it:")
        console.print("    macOS:  [cyan]brew install ollama[/cyan]")
        console.print("    Linux:  [cyan]curl -fsSL https://ollama.com/install.sh | sh[/cyan]")
        console.print("    Or visit: https://ollama.com/download\n")
        input("  Press Enter once Ollama is installed...")

        if not ollama_available():
            console.print("  [red]Ollama still not found. Install it and re-run configure.py.[/red]")
            return

    installed = get_installed_ollama_models()
    console.print("\n  [bold white]Choose a local model — pick based on your available RAM:[/bold white]\n")

    table = Table(show_header=True, box=None, padding=(0, 2))
    table.add_column("#",      style="dim", width=4)
    table.add_column("Model",  width=36)
    table.add_column("Size",   width=9)
    table.add_column("Tier",   width=8)
    table.add_column("Notes")
    table.add_column("",       width=14)

    current_tier = None
    for i, (mid, size, tier, desc) in enumerate(LOCAL_MODELS, 1):
        if tier != current_tier:
            current_tier = tier
            ram_needed = {"TINY": "< 2 GB RAM", "LIGHT": "2–6 GB RAM", "MEDIUM": "8–16 GB RAM"}[tier]
            table.add_row("", f"[bold {TIER_COLORS[tier]}]── {tier}  ({ram_needed}) ──[/]", "", "", "", "")
        status = f"[green]✓ installed[/green]" if mid in installed else "[dim]not downloaded[/dim]"
        table.add_row(str(i), f"[{TIER_COLORS[tier]}]{mid}[/]", size, tier, desc, status)

    table.add_row("", "[magenta]── CUSTOM ──[/]", "", "", "", "")
    table.add_row(str(len(LOCAL_MODELS) + 1), "[magenta]Custom[/]", "", "", "Enter any Ollama model name", "")

    console.print(table)
    if installed:
        console.print(f"\n  [dim]Already on your machine: {', '.join(installed)}[/dim]")

    default_idx = next((str(i) for i, (m, *_) in enumerate(LOCAL_MODELS, 1)
                        if m == "qwen2.5:14b-instruct-q4_K_M"), "9")
    choice = Prompt.ask("\n  Select model", default=default_idx)

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(LOCAL_MODELS):
            model = LOCAL_MODELS[idx][0]
        else:
            model = Prompt.ask("  Model name")
    except ValueError:
        model = choice

    if model not in installed:
        if Confirm.ask(f"  Download {model} now?", default=True):
            if not pull_ollama_model(model):
                return
    else:
        console.print(f"  [green]✓ {model} already installed — no download needed.[/green]")

    write_env("OPENAI_API_KEY", "ollama")
    write_env("BASE_URL", "http://localhost:11434/v1")
    write_env("MODEL_NAME", model)
    write_env("GEOCLAW_MODEL_PROVIDER", "ollama")

    console.print(f"\n  [green]✓ Local model configured:[/green] {model}")


def show_current_config():
    if not ENV_PATH.exists():
        console.print("  [dim]No .env file yet.[/dim]")
        return
    cfg = dotenv_values(str(ENV_PATH))
    table = Table(show_header=True, box=None, padding=(0, 2))
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    for k, v in cfg.items():
        display = ("*" * 8 + v[-4:]) if ("KEY" in k and v and v != "ollama" and v != "YOUR_API_KEY_HERE") else (v or "[dim]not set[/dim]")
        table.add_row(k, display)
    console.print(table)


def main():
    console.print(Panel.fit(
        "[bold blue]GeoClaw Enterprise — Configuration Wizard[/bold blue]\n"
        "[dim]Set up your AI provider in seconds[/dim]",
        border_style="blue"
    ))

    while True:
        console.print("\n  [bold]What do you want to configure?[/bold]\n")
        console.print("  [1] ☁️   Cloud API  — OpenAI, DeepSeek, OpenRouter, or Custom")
        console.print("  [2] 🖥️   Local model — download & run AI on your machine (free)")
        console.print("  [3] 📋  Show current config")
        console.print("  [4] ⏩  Exit\n")

        action = Prompt.ask("  Select", default="1")

        if action == "1":
            console.print("\n  [bold]Choose provider:[/bold]\n")
            console.print("  [1] OpenAI       (GPT-4o, GPT-4o-mini)")
            console.print("  [2] DeepSeek     (cheapest cloud option)")
            console.print("  [3] OpenRouter   (100+ models, one key)")
            console.print("  [5] Custom       (any OpenAI-compatible API)\n")
            pid = Prompt.ask("  Provider", default="1")
            if pid in ("1", "2", "3", "5"):
                configure_cloud(pid)
            else:
                console.print("  [yellow]Invalid choice.[/yellow]")

        elif action == "2":
            configure_ollama()

        elif action == "3":
            console.print("\n  [bold]Current .env:[/bold]")
            show_current_config()

        elif action == "4":
            console.print("\n  [green]Done! Start GeoClaw with:[/green]")
            console.print("    [cyan]source .venv/bin/activate[/cyan]")
            console.print("    [cyan]python tui.py[/cyan]\n")
            break
        else:
            console.print("  [yellow]Invalid option.[/yellow]")


if __name__ == "__main__":
    main()
