#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "rich",
# ]
# ///
"""rm command -- Delete a local model.

GOTCHA Tools layer, ATLAS Assemble phase.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.prompt import Confirm

# ---------------------------------------------------------------------------
# Ensure the package root is importable when run as a script
# ---------------------------------------------------------------------------
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from api.config import get_config  # noqa: E402

# Import bypass permissions
try:
    from permissions.bypass import should_bypass_permissions

    HAS_BYPASS = True
except ImportError:
    HAS_BYPASS = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
version = "0.1.0"
console = Console()


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------


async def handle_rm_async(args: argparse.Namespace) -> None:
    """Delete a local model."""
    cfg = get_config()
    model_name = args.model_name

    # Confirm deletion unless --force is set or bypass is enabled
    should_confirm = not args.force

    # Check if bypass is enabled
    if should_confirm and HAS_BYPASS and should_bypass_permissions():
        console.print(f"[yellow]Bypassing confirmation for model deletion: {model_name}[/yellow]")
        should_confirm = False  # Skip confirmation when bypassing

    if should_confirm:
        if not Confirm.ask(f"Delete model [cyan]{model_name}[/cyan]?"):
            console.print("Aborted.")
            return

    console.print(f"Deleting model: [cyan]{model_name}[/cyan]")

    url = f"{cfg.ollama_host}/api/delete"
    payload = {"name": model_name}

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.delete(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result.get("error"):
                console.print(f"[red]Error:[/red] {result['error']}")
                sys.exit(1)

        console.print(f"[green]Success:[/green] Model [cyan]{model_name}[/cyan] deleted successfully!")

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            console.print(f"[red]Error:[/red] Model '{model_name}' not found.")
            console.print("List available models with: qarin list")
        else:
            console.print(f"[red]Error:[/red] HTTP {exc.response.status_code}: {exc.response.text}")
        sys.exit(1)
    except httpx.ConnectError:
        console.print(f"[red]Error:[/red] Cannot connect to Ollama at {cfg.ollama_host}")
        console.print("Make sure Ollama is running: [bold]ollama serve[/bold]")
        sys.exit(1)


def handle_rm(args: argparse.Namespace) -> None:
    """Delete a model (sync wrapper)."""
    asyncio.run(handle_rm_async(args))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the rm command argument parser."""
    parser = argparse.ArgumentParser(
        prog="qarin rm",
        description="Delete a local model",
        epilog="""
Examples:
  qarin rm llama3.2
  qarin rm my-model --force
        """,
    )
    parser.add_argument("model_name", help="Model to remove (e.g. llama3.2)")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        default=False,
        help="Skip confirmation prompt",
    )
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_rm(args)
