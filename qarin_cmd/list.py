#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
# ]
# ///
"""list command -- List available local models."""

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

version = "0.1.0"
console = Console()


def handle_list(args: argparse.Namespace) -> None:
    """List available local models."""
    cfg = get_config()
    url = f"{cfg.ollama_host}/api/tags"

    try:
        resp = httpx.get(url, timeout=10.0)
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
    if not models:
        console.print("No models found locally. Pull one with: [bold]qarin pull <model>[/bold]")
        return

    if args.json:
        print(json.dumps(models, indent=2))
        return

    table = Table(title="Local Models")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Size", justify="right", style="green")
    table.add_column("Modified", style="yellow")

    for m in models:
        name = m.get("name", "unknown")
        size_bytes = m.get("size", 0)
        if size_bytes >= 1_073_741_824:
            size_str = f"{size_bytes / 1_073_741_824:.1f} GB"
        elif size_bytes >= 1_048_576:
            size_str = f"{size_bytes / 1_048_576:.1f} MB"
        else:
            size_str = f"{size_bytes} B"
        modified = m.get("modified_at", "unknown")
        if isinstance(modified, str) and "T" in modified:
            modified = modified.split("T")[0]
        table.add_row(name, size_str, modified)

    console.print(table)


def build_parser() -> argparse.ArgumentParser:
    """Build the list command argument parser."""
    parser = argparse.ArgumentParser(
        prog="qarin list",
        description="List available local models",
    )
    parser.add_argument("--json", action="store_true", default=False, help="JSON output mode")
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_list(args)
