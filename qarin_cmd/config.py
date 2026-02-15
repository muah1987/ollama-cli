#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "rich",
# ]
# ///
"""config command -- Show/set provider configuration."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from rich.console import Console
from rich.table import Table

# ---------------------------------------------------------------------------
# Ensure the package root is importable when run as a script
# ---------------------------------------------------------------------------
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from api.config import QarinCliConfig, get_config, save_config  # noqa: E402

version = "0.1.0"
console = Console()

# Suffixes that identify sensitive config keys (API keys, tokens, secrets)
_SENSITIVE_SUFFIXES = ("_api_key", "_token", "_secret")


def _is_sensitive_key(key: str) -> bool:
    """Return True if the key name matches a sensitive pattern."""
    return any(key.endswith(suffix) for suffix in _SENSITIVE_SUFFIXES)


def handle_config(args: argparse.Namespace) -> None:
    """Show or set provider configuration."""
    cfg = get_config()
    action: str | None = getattr(args, "action", None)
    key: str | None = getattr(args, "key", None)
    value: str | None = getattr(args, "value", None)
    use_json: bool = getattr(args, "json", False)

    if action is None:
        # Show all configuration
        _show_config(cfg, use_json)
        return

    if action == "get":
        if not key:
            _show_config(cfg, use_json)
            return
        _get_config_key(cfg, key, use_json)
        return

    if action == "set":
        if not key or value is None:
            console.print("[red]Error:[/red] Usage: qarin config set <key> <value>")
            sys.exit(1)
        _set_config_key(cfg, key, value)
        return

    # If action looks like a key name (e.g. `qarin config ollama_model`)
    if hasattr(cfg, action):
        _get_config_key(cfg, action, use_json)
        return

    console.print(f"[red]Error:[/red] Unknown action '{action}'. Use 'get' or 'set'.")
    sys.exit(1)


def _show_config(cfg: QarinCliConfig, use_json: bool) -> None:
    """Display the full configuration."""
    data = asdict(cfg)

    # Mask sensitive values by pattern
    for key in data:
        if _is_sensitive_key(key) and data[key]:
            data[key] = "****"

    if use_json:
        print(json.dumps(data, indent=2))
        return

    table = Table(title="Configuration")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="green")

    for key, val in sorted(data.items()):
        table.add_row(key, str(val))

    console.print(table)


def _get_config_key(cfg: QarinCliConfig, key: str, use_json: bool) -> None:
    """Display a single configuration value."""
    if not hasattr(cfg, key):
        console.print(f"[red]Error:[/red] Unknown config key: {key}")
        sys.exit(1)

    val = getattr(cfg, key)
    if _is_sensitive_key(key) and val:
        val = "****"

    if use_json:
        print(json.dumps({key: val}, indent=2))
    else:
        console.print(f"[cyan]{key}[/cyan] = [green]{val}[/green]")


def _set_config_key(cfg: QarinCliConfig, key: str, value: str) -> None:
    """Set a configuration value and save it."""
    if not hasattr(cfg, key):
        console.print(f"[red]Error:[/red] Unknown config key: {key}")
        sys.exit(1)

    if _is_sensitive_key(key):
        console.print(f"[red]Error:[/red] Cannot set sensitive key '{key}' via CLI. Use environment variables.")
        sys.exit(1)

    # Type-coerce the value based on the current type
    current = getattr(cfg, key)

    # Reject non-scalar fields (list, dict) — they cannot be reliably set via a single CLI value
    if isinstance(current, (list, dict)):
        console.print(f"[red]Error:[/red] Cannot set structured key '{key}' via CLI. Edit the config file directly.")
        sys.exit(1)

    if isinstance(current, bool):
        coerced: object = value.lower() in ("1", "true", "yes", "on")
    elif isinstance(current, int):
        try:
            coerced = int(value)
        except ValueError:
            console.print(f"[red]Error:[/red] Expected an integer for '{key}', got '{value}'")
            sys.exit(1)
    elif isinstance(current, float):
        try:
            coerced = float(value)
        except ValueError:
            console.print(f"[red]Error:[/red] Expected a number for '{key}', got '{value}'")
            sys.exit(1)
    else:
        coerced = value

    setattr(cfg, key, coerced)
    save_config(cfg)
    console.print(f"[green]✓[/green] Set [cyan]{key}[/cyan] = [green]{coerced}[/green]")


def build_parser() -> argparse.ArgumentParser:
    """Build the config command argument parser."""
    parser = argparse.ArgumentParser(
        prog="qarin config",
        description="Show/set provider configuration",
        epilog="""
Examples:
  qarin config                         # Show all config
  qarin config get                     # Show all config
  qarin config get ollama_model        # Show specific key
  qarin config set ollama_model llama3  # Set a value
  qarin config --json                  # JSON output
        """,
    )
    parser.add_argument("action", nargs="?", type=str, help="Action (get/set) or config key")
    parser.add_argument("key", nargs="?", type=str, help="Config key")
    parser.add_argument("value", nargs="?", type=str, help="Config value (for set)")
    parser.add_argument("--json", action="store_true", default=False, help="JSON output mode")
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_config(args)
