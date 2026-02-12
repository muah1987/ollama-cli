#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "rich",
# ]
# ///
"""create command -- Create a model from a Modelfile.

GOTCHA Tools layer, ATLAS Assemble phase.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

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


async def handle_create_async(args: argparse.Namespace) -> None:
    """Create a model from a Modelfile."""
    cfg = get_config()
    model_name = args.model_name
    modelfile_path = args.modelfile

    # Read Modelfile content
    if modelfile_path:
        modelfile = Path(modelfile_path)
        if not modelfile.exists():
            console.print(f"[red]Error:[/red] Modelfile not found: {modelfile_path}")
            sys.exit(1)
        with open(modelfile) as f:
            modelfile_content = f.read()
    else:
        # Try default Modelfile
        default_modelfile = Path.cwd() / "Modelfile"
        if default_modelfile.exists():
            with open(default_modelfile) as f:
                modelfile_content = f.read()
            console.print(f"Using Modelfile from: [cyan]{default_modelfile}[/cyan]")
        else:
            console.print("[red]Error:[/red] No Modelfile found.")
            console.print("Create a Modelfile or specify --modelfile <path>")
            sys.exit(1)

    # Validate Modelfile content
    if not modelfile_content.strip():
        console.print("[red]Error:[/red] Modelfile is empty.")
        sys.exit(1)

    # Show what we're creating
    console.print(f"Creating model: [cyan]{model_name}[/cyan]")
    if args.verbose:
        console.print("\n[bold]Modelfile contents:[/bold]")
        console.print(modelfile_content)
        console.print()

    # Create the model via Ollama API
    url = f"{cfg.ollama_host}/api/create"
    payload: dict = {"name": model_name, "stream": args.stream}
    if args.modelfile:
        payload["modelfile"] = modelfile_content

    async with httpx.AsyncClient(timeout=300.0) as client:
        if args.stream:
            # Streaming creation with progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Creating model...", total=None)

                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            status = chunk.get("status", "")
                            if status:
                                progress.update(task, description=status)
                            if chunk.get("error"):
                                console.print(f"[red]Error:[/red] {chunk['error']}")
                                sys.exit(1)
                            if chunk.get("digest"):
                                progress.update(task, description=f"Downloaded layers: {chunk['digest'][:12]}...")
                        except json.JSONDecodeError:
                            continue
        else:
            # Non-streaming creation
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            if result.get("error"):
                console.print(f"[red]Error:[/red] {result['error']}")
                sys.exit(1)

    console.print(f"[green]Success:[/green] Model [cyan]{model_name}[/cyan] created successfully!")


def handle_create(args: argparse.Namespace) -> None:
    """Create a model (sync wrapper)."""
    asyncio.run(handle_create_async(args))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the create command argument parser."""
    parser = argparse.ArgumentParser(
        prog="ollama-cli create",
        description="Create a model from a Modelfile",
        epilog="""
Examples:
  ollama-cli create my-model
  ollama-cli create my-model --modelfile ./my-modelfile
  ollama-cli create my-model --stream --verbose
        """,
    )
    parser.add_argument("model_name", help="Name for the new model")
    parser.add_argument(
        "--modelfile",
        type=str,
        help="Path to Modelfile (default: Modelfile in current directory)",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        default=False,
        help="Stream creation progress",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Show detailed output",
    )
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_create(args)
