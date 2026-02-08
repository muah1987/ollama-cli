#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "rich",
# ]
# ///
"""ps command -- List running models.

GOTCHA Tools layer, ATLAS Assemble phase.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.table import Table

# ---------------------------------------------------------------------------
# Ensure the package root is importable when run as a script
# ---------------------------------------------------------------------------
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from api.config import get_config  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_VERSION = "0.1.0"
console = Console()


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------


def handle_ps(args: argparse.Namespace) -> None:
    """List running models."""
    cfg = get_config()
    url = f"{cfg.ollama_host}/api/ps"

    try:
        resp = httpx.get(url, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
    except httpx.ConnectError:
        console.print(f"[red]Error:[/red] Cannot connect to Ollama at {cfg.ollama_host}")
        console.print("Make sure Ollama is running: [bold]ollama serve[/bold]")
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]Error:[/red] HTTP {exc.response.status_code} from Ollama API")
        sys.exit(1)

    models = data.get("models", [])

    if args.json:
        print(json.dumps(models, indent=2))
        return

    if not models:
        console.print("No models are currently running.")
        return

    table = Table(title="Running Models")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("ID", style="dim")
    table.add_column("Size", justify="right", style="green")
    table.add_column("VRAM", justify="right", style="yellow")
    table.add_column("Expiration", style="magenta")

    for m in models:
        name = m.get("name", "unknown")
        model_id = m.get("name", "").split(":")[0] if ":" in m.get("name", "") else name
        size_bytes = m.get("size", {}).get("vram", 0)
        vram_bytes = m.get("size", {}).get("vram", 0)

        # Format size
        if size_bytes >= 1_073_741_824:
            size_str = f"{size_bytes / 1_073_741_824:.1f} GB"
        elif size_bytes >= 1_048_576:
            size_str = f"{size_bytes / 1_048_576:.1f} MB"
        elif size_bytes > 0:
            size_str = f"{size_bytes // 1024} KB"
        else:
            size_str = "N/A"

        # Format VRAM
        if vram_bytes >= 1_073_741_824:
            vram_str = f"{vram_bytes / 1_073_741_824:.1f} GB"
        elif vram_bytes >= 1_048_576:
            vram_str = f"{vram_bytes / 1_048_576:.1f} MB"
        elif vram_bytes > 0:
            vram_str = f"{vram_bytes // 1024} KB"
        else:
            vram_str = "N/A"

        # Expiration is not always present in responses
        expiration = m.get("expires_at", "N/A")
        if isinstance(expiration, str) and "T" in expiration:
            expiration = expiration.split("T")[1][:8]  # Just show time

        table.add_row(name, model_id[:12], size_str, vram_str, expiration)

    console.print(table)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the ps command argument parser."""
    parser = argparse.ArgumentParser(
        prog="ollama-cli ps",
        description="List running models",
        epilog="""
Examples:
  ollama-cli ps
  ollama-cli ps --json
        """,
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="JSON output mode",
    )
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_ps(args)