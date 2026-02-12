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
    from . import (
        accelerate,  # noqa: F401
        install,  # noqa: F401
        rdma,  # noqa: F401
    )
except ImportError:
    pass  # New commands may not be available in some environments

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
VERSION = "0.1.0"
_INTERACTIVE_COMMANDS = frozenset({"interactive", "i", "chat"})

console = Console()

# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------


def print_banner() -> None:
    """Print a startup banner showing current config."""
    cfg = get_config()
    compact_status = "on" if cfg.auto_compact else "off"
    console.print(f"[bold cyan]ollama-cli[/bold cyan] v{VERSION}")
    console.print(f"  provider : [green]{cfg.provider}[/green]")
    console.print(f"  model    : [green]{cfg.ollama_model}[/green]")
    console.print(f"  context  : [green]{cfg.context_length}[/green] tokens")
    console.print(
        f"  compact  : auto-compact [green]{compact_status}[/green] (threshold {int(cfg.compact_threshold * 100)}%)"
    )
    console.print()


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


def cmd_chat(args: argparse.Namespace) -> None:
    """Start interactive chat session with a model (alias for interactive)."""
    cmd_interactive(args)


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


def cmd_pull(args: argparse.Namespace) -> None:
    """Pull a model from the registry."""
    from .pull import handle_pull

    handle_pull(args)


def cmd_show(args: argparse.Namespace) -> None:
    """Show model details."""
    from .show import handle_show

    handle_show(args)


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


def cmd_config(args: argparse.Namespace) -> None:
    """Show or set provider configuration."""
    from .config import handle_config

    handle_config(args)


def cmd_status(args: argparse.Namespace) -> None:
    """Show current session status, server status, and configuration summary."""
    from .status import handle_status

    handle_status(args)


def cmd_version(_args: argparse.Namespace) -> None:
    """Show CLI version."""
    print(f"ollama-cli v{VERSION}")


def cmd_interactive(args: argparse.Namespace) -> None:
    """Start the interactive REPL mode."""
    # Import here to avoid circular imports
    from model.session import Session

    from .interactive import InteractiveMode

    cfg = get_config()

    # Resume the most recent session if --resume was passed
    session = None
    if getattr(args, "resume", False):
        latest_id = _find_latest_session()
        if latest_id:
            try:
                session = Session.load(latest_id)
                console.print(f"[green]Resumed session:[/green] {latest_id}")
            except Exception as exc:
                console.print(f"[yellow]Could not resume session ({exc}), starting new one.[/yellow]")

    if session is None:
        session = Session(model=cfg.ollama_model, provider=cfg.provider)

    async def _run() -> None:
        await session.start()
        repl = InteractiveMode(session)
        await repl.run()

    import asyncio

    asyncio.run(_run())


def cmd_run_prompt(args: argparse.Namespace) -> None:
    """Run a one-shot prompt and print the response.

    Routes through :class:`Session` / :class:`ProviderRouter` so that the
    ``--provider``, ``--model``, and ``--output-format`` flags are honoured.
    """
    cfg = get_config()
    prompt_text = getattr(args, "prompt", None)
    if not prompt_text:
        console.print("[red]Error:[/red] No prompt provided.")
        sys.exit(1)

    from model.session import Session

    session = Session(model=cfg.ollama_model, provider=cfg.provider)

    import asyncio

    async def _run() -> dict:
        await session.start()
        if getattr(args, "system_prompt", None):
            session.context_manager.add_message("system", args.system_prompt)
        result = await session.send(prompt_text)
        await session.end()
        return result

    try:
        result = asyncio.run(_run())
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    content = result.get("content", "")
    output_fmt = cfg.output_format or "text"

    if output_fmt == "json" or getattr(args, "json", False):
        print(json.dumps(result, indent=2))
    elif output_fmt == "markdown":
        print(content)
    else:
        print(content)


# ---------------------------------------------------------------------------
# stubs for new Ollama commands
# ---------------------------------------------------------------------------


def cmd_create(args: argparse.Namespace) -> None:
    """Create a model from a Modelfile."""
    from .create import handle_create

    handle_create(args)


def cmd_rm(args: argparse.Namespace) -> None:
    """Delete a local model."""
    from .rm import handle_rm

    handle_rm(args)


def cmd_cp(args: argparse.Namespace) -> None:
    """Copy a local model."""
    from .cp import handle_cp

    handle_cp(args)


def cmd_ps(args: argparse.Namespace) -> None:
    """List running models."""
    from .ps import handle_ps

    handle_ps(args)


def cmd_stop(args: argparse.Namespace) -> None:
    """Stop a running model."""
    from .stop import handle_stop

    handle_stop(args)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="ollama-cli",
        usage="ollama-cli [options] [command] [prompt]",
        description=(
            "Ollama CLI - an AI coding assistant powered by Ollama. "
            "Starts an interactive session by default. "
            "Use -p/--print for non-interactive output."
        ),
    )

    # Global flags
    parser.add_argument("-v", "--version", action="version", version=f"ollama-cli v{VERSION}")
    parser.add_argument("--model", type=str, default=None, help="Override model")
    parser.add_argument(
        "--provider",
        type=str,
        choices=["ollama", "claude", "gemini", "codex"],
        default=None,
        help="Override provider",
    )
    parser.add_argument(
        "-p",
        "--print",
        action="store_true",
        default=False,
        dest="print_mode",
        help="Print response and exit (non-interactive mode)",
    )
    parser.add_argument(
        "-r",
        "--resume",
        action="store_true",
        default=False,
        help="Resume the most recent conversation",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["text", "json", "markdown"],
        default=None,
        help="Output format (text, json, markdown)",
    )
    parser.add_argument(
        "--allowed-tools",
        type=str,
        default=None,
        help="Comma-separated list of allowed tool names (e.g. file_read,grep_search)",
    )
    parser.add_argument("--json", action="store_true", default=False, help="JSON output mode")
    parser.add_argument("--verbose", action="store_true", default=False, help="Verbose output")
    parser.add_argument("--no-hooks", action="store_true", default=False, help="Disable hooks")
    parser.add_argument("--system-prompt", type=str, default=None, help="System prompt to use")

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
    except (ImportError, AttributeError):
        # AttributeError: register_commands may call methods not available
        # on the subparsers action (pre-existing issue in accelerate.py).
        pass

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

COMMAND_MAP = {
    "chat": cmd_chat,
    "run": cmd_run_prompt,
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


def _extract_prompt_args(argv: list[str]) -> tuple[list[str], str | None]:
    """Separate a direct prompt from CLI arguments.

    If the first non-flag argument is not a known subcommand, treat all
    remaining positional tokens as a direct prompt.  Returns the filtered
    argv (flags only) and the extracted prompt string (or *None*).
    """
    known_commands = set(COMMAND_MAP.keys())
    flags: list[str] = []
    positionals: list[str] = []

    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("-"):
            flags.append(arg)
            # Consume the next token if this flag expects a value
            if arg in (
                "--model",
                "--provider",
                "--system-prompt",
                "--output-format",
                "--allowed-tools",
            ) and i + 1 < len(argv):
                i += 1
                flags.append(argv[i])
        else:
            positionals.append(arg)
            # Collect everything after first positional
            positionals.extend(argv[i + 1 :])
            break
        i += 1

    if positionals and positionals[0] not in known_commands:
        return flags, " ".join(positionals)
    return argv, None


def _find_latest_session() -> str | None:
    """Find the most recently saved session file.

    Returns
    -------
    The session ID of the latest session, or ``None`` if none exist.
    """
    sessions_dir = Path(".ollama/sessions")
    if not sessions_dir.is_dir():
        return None

    session_files = sorted(sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not session_files:
        return None

    return session_files[0].stem


def main() -> None:
    """Entry point."""
    parser = build_parser()

    raw_args = sys.argv[1:]

    # Support piped stdin: `echo "fix this" | ollama-cli`
    # Only treat piped stdin as a prompt when no explicit subcommand is present.
    piped_input = None
    if (
        not sys.stdin.isatty()
        and not any(a in raw_args for a in _INTERACTIVE_COMMANDS)
        and not any(arg in COMMAND_MAP for arg in raw_args)
    ):
        piped_input = sys.stdin.read().strip()

    filtered_args, direct_prompt = _extract_prompt_args(raw_args)

    if direct_prompt is not None or piped_input:
        # Parse only the flags (no subcommand)
        args = parser.parse_args(filtered_args)
        args.prompt = direct_prompt or piped_input
        _apply_global_flags(args)
        cmd_run_prompt(args)
        return

    args = parser.parse_args()
    _apply_global_flags(args)

    command = args.command
    if not command:
        if args.print_mode:
            console.print("[red]Error:[/red] --print requires a prompt.")
            console.print('Usage: ollama-cli -p "your prompt here"')
            sys.exit(1)
        # Default to interactive mode
        command = "interactive"

    if command not in COMMAND_MAP:
        parser.print_help()
        sys.exit(1)

    COMMAND_MAP[command](args)


def _apply_global_flags(args: argparse.Namespace) -> None:
    """Apply global CLI flags to the config singleton."""
    cfg = get_config()
    if args.model:
        cfg.ollama_model = args.model
    if args.provider:
        cfg.provider = args.provider
    if args.no_hooks:
        cfg.hooks_enabled = False
    if getattr(args, "output_format", None):
        cfg.output_format = args.output_format
    if getattr(args, "json", False) and not getattr(args, "output_format", None):
        cfg.output_format = "json"
    allowed = getattr(args, "allowed_tools", None)
    if allowed:
        cfg.allowed_tools = [t.strip() for t in allowed.split(",")]


if __name__ == "__main__":
    main()
