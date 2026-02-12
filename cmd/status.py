#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
#     "rich",
# ]
# ///
"""status command -- Show current session and server status."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ---------------------------------------------------------------------------
# Ensure the package root is importable when run as a script
# ---------------------------------------------------------------------------
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from api.config import get_config  # noqa: E402

version = "0.1.0"
console = Console()


def handle_status(args: argparse.Namespace) -> None:
    """Show current session and server status."""
    cfg = get_config()
    use_json: bool = getattr(args, "json", False)

    # Gather server status
    server_ok = False
    model_count = 0
    running_models: list[dict[str, object]] = []

    try:
        resp = httpx.get(f"{cfg.ollama_host}/api/tags", timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        model_count = len(data.get("models", []))
        server_ok = True
    except (httpx.ConnectError, httpx.HTTPStatusError):
        pass

    # Try to get running models
    if server_ok:
        try:
            ps_resp = httpx.get(f"{cfg.ollama_host}/api/ps", timeout=10.0)
            ps_resp.raise_for_status()
            ps_data = ps_resp.json()
            running_models = ps_data.get("models", [])
        except (httpx.ConnectError, httpx.HTTPStatusError):
            pass

    # Gather session info
    sessions_dir = Path(".ollama/sessions")
    session_count = len(list(sessions_dir.glob("*.json"))) if sessions_dir.is_dir() else 0

    status_data = {
        "server": {
            "status": "running" if server_ok else "offline",
            "host": cfg.ollama_host,
            "models_available": model_count,
            "models_running": len(running_models),
        },
        "config": {
            "provider": cfg.provider,
            "model": cfg.ollama_model,
            "context_length": cfg.context_length,
            "auto_compact": cfg.auto_compact,
            "compact_threshold": cfg.compact_threshold,
            "hooks_enabled": cfg.hooks_enabled,
        },
        "sessions": {
            "saved_sessions": session_count,
        },
    }

    if use_json:
        print(json.dumps(status_data, indent=2))
        return

    # Server status panel
    server_status = "[green]● Running[/green]" if server_ok else "[red]● Offline[/red]"
    server_text = Text()
    server_text.append(f"Host:             {cfg.ollama_host}\n")
    server_text.append(f"Models available: {model_count}\n")
    server_text.append(f"Models running:   {len(running_models)}")
    console.print(Panel(server_text, title=f"[bold]Server {server_status}[/bold]"))

    # Running models table
    if running_models:
        table = Table(title="Running Models")
        table.add_column("Name", style="cyan")
        table.add_column("Size", justify="right", style="green")
        table.add_column("Expires", style="yellow")
        for m in running_models:
            name = str(m.get("name", "unknown"))
            size_bytes = int(m.get("size", 0))
            if size_bytes >= 1_073_741_824:
                size_str = f"{size_bytes / 1_073_741_824:.1f} GB"
            elif size_bytes >= 1_048_576:
                size_str = f"{size_bytes / 1_048_576:.1f} MB"
            else:
                size_str = f"{size_bytes} B"
            expires = str(m.get("expires_at", "unknown"))
            expires_display = expires.split("T")[0] if isinstance(expires, str) and "T" in expires else expires
            table.add_row(name, size_str, expires_display)
        console.print(table)

    # Config panel
    config_text = Text()
    config_text.append(f"Provider:          {cfg.provider}\n")
    config_text.append(f"Model:             {cfg.ollama_model}\n")
    config_text.append(f"Context length:    {cfg.context_length}\n")
    compact_status = "on" if cfg.auto_compact else "off"
    config_text.append(f"Auto-compact:      {compact_status} ({int(cfg.compact_threshold * 100)}% threshold)\n")
    config_text.append(f"Hooks:             {'enabled' if cfg.hooks_enabled else 'disabled'}")
    console.print(Panel(config_text, title="[bold]Configuration[/bold]"))

    # Sessions
    if session_count > 0:
        console.print(f"  Saved sessions: [cyan]{session_count}[/cyan]")


def build_parser() -> argparse.ArgumentParser:
    """Build the status command argument parser."""
    parser = argparse.ArgumentParser(
        prog="ollama-cli status",
        description="Show current session and server status",
    )
    parser.add_argument("--json", action="store_true", default=False, help="JSON output mode")
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_status(args)
