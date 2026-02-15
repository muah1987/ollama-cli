#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
# ]
# ///
"""serve command -- Check Ollama server status."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
from rich.console import Console

# ---------------------------------------------------------------------------
# Ensure the package root is importable when run as a script
# ---------------------------------------------------------------------------
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from api.config import get_config  # noqa: E402

version = "0.1.0"
console = Console()


def handle_serve(_args: argparse.Namespace) -> None:
    """Check Ollama server status."""
    cfg = get_config()
    url = f"{cfg.ollama_host}/api/tags"

    try:
        resp = httpx.get(url, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        model_count = len(data.get("models", []))
        console.print(f"[green]Ollama is running[/green] at {cfg.ollama_host}")
        console.print(f"  Models available: {model_count}")
    except httpx.ConnectError:
        console.print(f"[red]Ollama is not running[/red] at {cfg.ollama_host}")
        console.print("Start it with: [bold]ollama serve[/bold]")
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        console.print(f"[yellow]Ollama responded with HTTP {exc.response.status_code}[/yellow]")
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    """Build the serve command argument parser."""
    parser = argparse.ArgumentParser(
        prog="qarin serve",
        description="Check Ollama server status",
    )
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_serve(args)
