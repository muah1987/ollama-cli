#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "httpx",
#     "rich",
# ]
# ///
"""
ollama-cli -- Main CLI entry point.

Provides subcommands for chatting, running prompts, listing models, pulling models,
and managing configuration. Organized to match Ollama's command structure.

Extended with acceleration management (MLX, EXO, RDMA) and installation commands.
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
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from api.config import get_config  # noqa: E402

# Import new command modules (these add their own subparsers)
try:
    from . import install  # noqa: F401
    from . import rdma  # noqa: F401
    from . import accelerate  # noqa: F401
except ImportError:
    pass  # New commands may not be available in some environments

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VERSION = "0.1.0"

console = Console()

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------


def print_banner() -> None:
    """Print a startup banner showing current config."""
    cfg = get_config()
    console.print(f"[bold cyan]ollama-cli[/bold cyan] v{VERSION}")
    console.print(f"  provider : [green]{cfg.provider}[/green]")
    console.print(f"  model    : [green]{cfg.ollama_model}[/green]")
    console.print(f"  context  : [green]{cfg.context_length}[/green] tokens")
    console.print()


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def cmd_chat(_args: argparse.Namespace) -> None:
    """Start interactive chat session with a model."""
    print_banner()
    console.print("[yellow]Chat mode coming soon...[/yellow]")
    console.print("Use the interactive mode for now: [bold]ollama-cli interactive[/bold]")


def cmd_list(args: argparse.Namespace) -> None:
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
        console.print("No models found locally. Pull one with: [bold]ollama-cli pull <model>[/bold]")
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


def cmd_pull(_args: argparse.Namespace) -> None:
    """Pull a model from the registry."""
    console.print("[yellow]Pull command coming soon...[/yellow]")


def cmd_show(_args: argparse.Namespace) -> None:
    """Show model details."""
    console.print("[yellow]Show command coming soon...[/yellow]")


def cmd_serve(_args: argparse.Namespace) -> None:
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


def cmd_config(_args: argparse.Namespace) -> None:
    """Show or set provider configuration."""
    console.print("[yellow]Config command coming soon...[/yellow]")


def cmd_status(_args: argparse.Namespace) -> None:
    """Show current session status."""
    console.print("[yellow]Status command coming soon...[/yellow]")


def cmd_version(_args: argparse.Namespace) -> None:
    """Show CLI version."""
    print(f"ollama-cli v{VERSION}")


def cmd_interactive(_args: argparse.Namespace) -> None:
    """Start the interactive REPL mode."""
    # Import here to avoid circular imports
    from .interactive import InteractiveMode
    from model.session import Session

    cfg = get_config()
    session = Session(model=cfg.ollama_model, provider=cfg.provider)

    async def _run() -> None:
        await session.start()
        repl = InteractiveMode(session)
        await repl.run()

    import asyncio
    asyncio.run(_run())


# ---------------------------------------------------------------------------
# stubs for new Ollama commands
# ---------------------------------------------------------------------------


def cmd_create(_args: argparse.Namespace) -> None:
    """Create a model from a Modelfile."""
    console.print("[yellow]Create command coming soon...[/yellow]")


def cmd_rm(_args: argparse.Namespace) -> None:
    """Delete a local model."""
    console.print("[yellow]Remove command coming soon...[/yellow]")


def cmd_cp(_args: argparse.Namespace) -> None:
    """Copy a local model."""
    console.print("[yellow]Copy command coming soon...[/yellow]")


def cmd_ps(_args: argparse.Namespace) -> None:
    """List running models."""
    console.print("[yellow]PS command coming soon...[/yellow]")


def cmd_stop(_args: argparse.Namespace) -> None:
    """Stop a running model."""
    console.print("[yellow]Stop command coming soon...[/yellow]")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="ollama-cli",
        description="Full-featured AI coding assistant powered by Ollama",
    )

    # Global flags
    parser.add_argument("--model", type=str, default=None, help="Override model")
    parser.add_argument(
        "--provider",
        type=str,
        choices=["ollama", "claude", "gemini", "codex"],
        default=None,
        help="Override provider",
    )
    parser.add_argument("--json", action="store_true", default=False, help="JSON output mode")
    parser.add_argument("--verbose", action="store_true", default=False, help="Verbose output")
    parser.add_argument("--no-hooks", action="store_true", default=False, help="Disable hooks")

    subparsers = parser.add_subparsers(dest="command")

    # chat
    subparsers.add_parser("chat", help="Start interactive chat session")

    # run
    run_parser = subparsers.add_parser("run", help="Run a one-shot prompt")
    run_parser.add_argument("prompt", nargs="?", type=str, help="The prompt to send")

    # list
    subparsers.add_parser("list", help="List available local models")

    # pull
    pull_parser = subparsers.add_parser("pull", help="Pull a model from registry")
    pull_parser.add_argument("model_name", nargs="?", type=str, help="Model to pull")

    # show
    show_parser = subparsers.add_parser("show", help="Show model details")
    show_parser.add_argument("model_name", nargs="?", type=str, help="Model to inspect")

    # serve
    subparsers.add_parser("serve", help="Check Ollama server status")

    # config
    config_parser = subparsers.add_parser("config", help="Show/set provider configuration")
    config_parser.add_argument("action", nargs="?", type=str, help="Action (get/set)")
    config_parser.add_argument("key", nargs="?", type=str, help="Config key")
    config_parser.add_argument("value", nargs="?", type=str, help="Config value")

    # status
    subparsers.add_parser("status", help="Show current session status")

    # version
    subparsers.add_parser("version", help="Show CLI version")

    # interactive
    subparsers.add_parser("interactive", aliases=["i"], help="Start interactive REPL mode")

    # New Ollama commands (stubs for now)
    subparsers.add_parser("create", help="Create a model from a Modelfile")
    rm_parser = subparsers.add_parser("rm", help="Delete a local model")
    rm_parser.add_argument("model_name", help="Model to remove")
    cp_parser = subparsers.add_parser("cp", help="Copy a local model")
    cp_parser.add_argument("source", help="Source model")
    cp_parser.add_argument("destination", help="Destination model name")
    subparsers.add_parser("ps", help="List running models")
    stop_parser = subparsers.add_parser("stop", help="Stop a running model")
    stop_parser.add_argument("model_name", nargs="?", help="Model to stop (optional)")

    # Acceleration commands
    try:
        from .accelerate import register_commands
        register_commands(subparsers)
    except ImportError:
        pass

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

COMMAND_MAP = {
    "chat": cmd_chat,
    "list": cmd_list,
    "pull": cmd_pull,
    "show": cmd_show,
    "serve": cmd_serve,
    "config": cmd_config,
    "status": cmd_status,
    "version": cmd_version,
    "interactive": cmd_interactive,
    "i": cmd_interactive,  # alias
    # New Ollama commands
    "create": cmd_create,
    "rm": cmd_rm,
    "cp": cmd_cp,
    "ps": cmd_ps,
    "stop": cmd_stop,
}


def main() -> None:
    """Entry point."""
    parser = build_parser()
    args = parser.parse_args()

    # Apply global flag overrides to config
    cfg = get_config()
    if args.model:
        cfg.ollama_model = args.model
    if args.provider:
        cfg.provider = args.provider
    if args.no_hooks:
        cfg.hooks_enabled = False

    # Default to interactive if no subcommand given
    command = args.command or "chat"

    if command not in COMMAND_MAP:
        parser.print_help()
        sys.exit(1)

    COMMAND_MAP[command](args)


if __name__ == "__main__":
    main()