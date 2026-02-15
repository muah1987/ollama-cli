#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "rich",
# ]
# ///
"""show command -- Show model details.

GOTCHA Tools layer, ATLAS Assemble phase.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

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


def handle_show(args: argparse.Namespace) -> None:
    """Show model details."""
    cfg = get_config()
    model_name = args.model_name

    if not model_name:
        # List available models
        try:
            resp = httpx.get(f"{cfg.ollama_host}/api/tags", timeout=30.0)
            resp.raise_for_status()
            data = resp.json()
            models = data.get("models", [])

            if not models:
                console.print("No models found locally.")
                console.print("Pull one with: [bold]qarin pull <model>[/bold]")
                return

            console.print("Available local models:")
            for m in models:
                name = m.get("name", "unknown")
                console.print(f"  - {name}")

            console.print("\nShow details with: qarin show <model-name>")
            return

        except httpx.ConnectError:
            console.print(f"[red]Error:[/red] Cannot connect to Ollama at {cfg.ollama_host}")
            console.print("Make sure Ollama is running: [bold]ollama serve[/bold]")
            sys.exit(1)
        except httpx.HTTPStatusError as exc:
            console.print(f"[red]Error:[/red] HTTP {exc.response.status_code} from Ollama API")
            sys.exit(1)

    # Get model details
    url = f"{cfg.ollama_host}/api/show"
    payload = {"name": model_name}

    try:
        resp = httpx.post(url, json=payload, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
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

    if args.json:
        print(json.dumps(data, indent=2))
        return

    # Display model details nicely
    console.print(f"\n[bold cyan]Model:[/bold cyan] {model_name}")
    console.print()

    # Model information
    license_info = data.get("license") or data.get("license_info", "Unknown")
    modelfile = data.get("modelfile", "")
    details = data.get("details", {})
    parameters = data.get("parameters", {})

    # Show details panel
    if details:
        detail_text = Text()
        detail_lines = []

        if "format" in details:
            detail_lines.append(f"Format: {details['format']}")
        if "family" in details:
            detail_lines.append(f"Family: {details['family']}")
        if "parameter_size" in details:
            param_size = details["parameter_size"]
            detail_lines.append(f"Parameters: {param_size}")
        if "quantization_level" in details:
            q_level = details["quantization_level"]
            detail_lines.append(f"Quantization: {q_level}")
        if "architecture" in details:
            detail_lines.append(f"Architecture: {details['architecture']}")

        parent_model = details.get("parent_model" or "parent")
        if parent_model:
            detail_lines.append(f"Parent: {parent_model}")

        for line in detail_lines:
            detail_text.append(line + "\n")

        if detail_text:
            console.print(Panel(detail_text, title="[bold]Model Details[/bold]"))
            console.print()

    # Show parameters
    if parameters:
        param_text = Text()
        for k, v in sorted(parameters.items()):
            param_text.append(f"{k}: {v}\n")

        console.print(Panel(param_text, title="[bold]Parameters[/bold]"))
        console.print()

    # Show license
    if license_info and license_info != "Unknown":
        license_text = Text(license_info, style="dim")
        console.print(Panel(license_text, title="[bold]License[/bold]"))
        console.print()

    # Show Modelfile if requested
    if args.modelfile and modelfile:
        console.print(Panel(modelfile, title="[bold]Modelfile[/bold]", expand=False))
        console.print()


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the show command argument parser."""
    parser = argparse.ArgumentParser(
        prog="qarin show",
        description="Show model details",
        epilog="""
Examples:
  qarin show llama3.2
  qarin show                   # List available models
  qarin show llama3.2 --json
  qarin show llama3.2 --modelfile
        """,
    )
    parser.add_argument(
        "model_name",
        nargs="?",
        type=str,
        help="Model to inspect (optional - if omitted, lists available models)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="JSON output mode",
    )
    parser.add_argument(
        "--modelfile",
        action="store_true",
        default=False,
        help="Show the Modelfile contents",
    )
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_show(args)
