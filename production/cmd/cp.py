#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "rich",
# ]
# ///
"""cp command -- Copy a local model.

GOTCHA Tools layer, ATLAS Assemble phase.
"""

from __future__ import annotations

import argparse
import asyncio
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
version = "0.1.0"
console = Console()


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------


async def handle_cp_async(args: argparse.Namespace) -> None:
    """Copy a local model."""
    cfg = get_config()
    source = args.source
    destination = args.destination

    console.print(f"Copying model: [cyan]{source}[/cyan] -> [cyan]{destination}[/cyan]")

    url = f"{cfg.ollama_host}/api/copy"
    payload = {"source": source, "destination": destination}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result.get("error"):
                console.print(f"[red]Error:[/red] {result['error']}")
                sys.exit(1)

        console.print(f"[green]Success:[/green] Copied [cyan]{source}[/cyan] to [cyan]{destination}[/cyan]")

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            console.print(f"[red]Error:[/red] Source model '{source}' not found.")
            console.print("List available models with: ollama-cli list")
        elif exc.response.status_code == 409:
            console.print(f"[red]Error:[/red] Destination model '{destination}' already exists.")
            console.print("Use a different destination name or delete the existing model first.")
        else:
            console.print(f"[red]Error:[/red] HTTP {exc.response.status_code}: {exc.response.text}")
        sys.exit(1)
    except httpx.ConnectError:
        console.print(f"[red]Error:[/red] Cannot connect to Ollama at {cfg.ollama_host}")
        console.print("Make sure Ollama is running: [bold]ollama serve[/bold]")
        sys.exit(1)


def handle_cp(args: argparse.Namespace) -> None:
    """Copy a model (sync wrapper)."""
    asyncio.run(handle_cp_async(args))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the cp command argument parser."""
    parser = argparse.ArgumentParser(
        prog="ollama-cli cp",
        description="Copy a local model",
        epilog="""
Examples:
  ollama-cli cp llama3.2 my-llama3.2
  ollama-cli cp my-model my-model-backup
        """,
    )
    parser.add_argument("source", help="Source model name")
    parser.add_argument("destination", help="Destination model name")
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_cp(args)