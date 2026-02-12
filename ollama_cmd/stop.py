#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "rich",
# ]
# ///
"""stop command -- Stop a running model.

GOTCHA Tools layer, ATLAS Assemble phase.
"""

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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_VERSION = "0.1.0"
console = Console()


# ---------------------------------------------------------------------------
# Command handler
# ---------------------------------------------------------------------------


def handle_stop(args: argparse.Namespace) -> None:
    """Stop a running model.

    Ollama's API doesn't have a direct /api/stop endpoint for stopping models.
    Instead, we call a generate request with keep_alive: 0 to unload the model.
    """
    cfg = get_config()
    model_name = args.model_name

    if not model_name:
        # If no model specified, list running models first
        console.print("No model specified. Listing running models:")
        try:
            resp = httpx.get(f"{cfg.ollama_host}/api/ps", timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])

            if not models:
                console.print("No models are currently running.")
                return

            console.print("\nRunning models:")
            for m in models:
                name = m.get("name", "unknown")
                console.print(f"  - {name}")

            console.print("\nSpecify a model to stop with: ollama-cli stop <model-name>")
            return

        except httpx.ConnectError:
            console.print(f"[red]Error:[/red] Cannot connect to Ollama at {cfg.ollama_host}")
            console.print("Make sure Ollama is running: [bold]ollama serve[/bold]")
            sys.exit(1)
        except httpx.HTTPStatusError as exc:
            console.print(f"[red]Error:[/red] HTTP {exc.response.status_code} from Ollama API")
            sys.exit(1)

    console.print(f"Stopping model: [cyan]{model_name}[/cyan]")

    # First check if the model is running
    try:
        resp = httpx.get(f"{cfg.ollama_host}/api/ps", timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        running_models = data.get("models", [])

        running_names = [m.get("name", "") for m in running_models]
        base_name = model_name.split(":")[0]
        is_running = any(base_name in name for name in running_names)

        if not is_running:
            console.print(f"[yellow]Warning:[/yellow] Model '{model_name}' does not appear to be running.")
            console.print("List running models with: ollama-cli ps")
            # Continue anyway to attempt cleanup

    except httpx.ConnectError:
        console.print(f"[red]Error:[/red] Cannot connect to Ollama at {cfg.ollama_host}")
        console.print("Make sure Ollama is running: [bold]ollama serve[/bold]")
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]Error:[/red] HTTP {exc.response.status_code} from Ollama API")
        sys.exit(1)

    # Try to unload the model by calling generate with keep_alive: 0 and empty prompt
    url = f"{cfg.ollama_host}/api/generate"
    payload = {
        "model": model_name,
        "prompt": "",
        "keep_alive": 0,
        "stream": False,
    }

    try:
        resp = httpx.post(url, json=payload, timeout=60.0)

        if resp.status_code == 404:
            console.print(f"[yellow]Warning:[/yellow] Model '{model_name}' not found.")
            console.print("This is expected if the model was already unloaded or doesn't exist.")
        elif resp.status_code == 400:
            # This can happen if the model was never loaded
            console.print(f"[yellow]Warning:[/yellow] Model '{model_name}' was not loaded.")
        else:
            resp.raise_for_status()

        console.print(f"[green]Success:[/green] Model [cyan]{model_name}[/cyan] stopped/unloaded.")

    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            console.print(f"[yellow]Model '{model_name}' not found or already unloaded.[/yellow]")
        elif exc.response.status_code == 400:
            console.print(f"[yellow]Model '{model_name}' was not loaded.[/yellow]")
        else:
            console.print(f"[red]Error:[/red] HTTP {exc.response.status_code}: {exc.response.text}")
            sys.exit(1)
    except httpx.ConnectError:
        console.print(f"[red]Error:[/red] Cannot connect to Ollama at {cfg.ollama_host}")
        console.print("Make sure Ollama is running: [bold]ollama serve[/bold]")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the stop command argument parser."""
    parser = argparse.ArgumentParser(
        prog="ollama-cli stop",
        description="Stop a running model",
        epilog="""
Examples:
  ollama-cli stop llama3.2
  ollama-cli stop                   # List running models
        """,
    )
    parser.add_argument(
        "model_name",
        nargs="?",
        type=str,
        help="Model to stop (optional - if omitted, lists running models)",
    )
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_stop(args)
