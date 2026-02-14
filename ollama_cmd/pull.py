#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "rich",
# ]
# ///
"""pull command -- Pull a model from the Ollama registry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
from rich.console import Console
from rich.progress import BarColumn, DownloadColumn, Progress, TextColumn, TimeRemainingColumn

# ---------------------------------------------------------------------------
# Ensure the package root is importable when run as a script
# ---------------------------------------------------------------------------
api_dir = Path(__file__).resolve().parent.parent
if str(api_dir) not in sys.path:
    sys.path.insert(0, str(api_dir))

from api.config import get_config  # noqa: E402

version = "0.1.0"
console = Console()


def handle_pull(args: argparse.Namespace) -> None:
    """Pull a model from the Ollama registry."""
    model_name: str | None = getattr(args, "model_name", None)
    if not model_name:
        console.print("[red]Error:[/red] No model name provided.")
        console.print("Usage: [bold]cli-ollama pull <model>[/bold]")
        console.print("Example: [bold]cli-ollama pull llama3.2[/bold]")
        sys.exit(1)

    cfg = get_config()
    url = f"{cfg.ollama_host}/api/pull"
    payload = {"name": model_name, "stream": True}

    console.print(f"Pulling [bold cyan]{model_name}[/bold cyan]...")

    try:
        with httpx.stream("POST", url, json=payload, timeout=None) as response:
            response.raise_for_status()
            _stream_pull_progress(response, model_name)
    except httpx.ConnectError:
        console.print(f"[red]Error:[/red] Cannot connect to Ollama at {cfg.ollama_host}")
        console.print("Make sure Ollama is running: [bold]ollama serve[/bold]")
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]Error:[/red] HTTP {exc.response.status_code} from Ollama API")
        sys.exit(1)


def _stream_pull_progress(response: httpx.Response, model_name: str) -> None:
    """Display streaming pull progress with a Rich progress bar."""
    import json

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TimeRemainingColumn(),
        console=console,
    )

    task_id = None
    current_status = ""
    current_total = 0

    with progress:
        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue

            status = data.get("status", "")
            total = data.get("total", 0)
            completed = data.get("completed", 0)

            if status != current_status:
                current_status = status
                if task_id is not None:
                    progress.update(task_id, completed=current_total or 0)
                current_total = total
                task_id = progress.add_task(status, total=total or None)

            if task_id is not None and total > 0:
                current_total = total
                progress.update(task_id, completed=completed, total=total)

            if status == "success":
                if task_id is not None:
                    progress.update(task_id, completed=current_total or 0)
                break

    console.print(f"[green]✓[/green] Successfully pulled [bold]{model_name}[/bold]")


def build_parser() -> argparse.ArgumentParser:
    """Build the pull command argument parser."""
    parser = argparse.ArgumentParser(
        prog="cli-ollama pull",
        description="Pull a model from the Ollama registry",
    )
    parser.add_argument("model_name", nargs="?", type=str, help="Model to pull")
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_pull(args)
