#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///
"""run command -- Generate a response from a prompt.

Executes a one-shot prompt against the configured model with optional streaming
and control parameters.

GOTCHA Tools layer, ATLAS Assemble phase.
"""

from __future__ import annotations

import argparse
import json
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


def handle_run(args: argparse.Namespace) -> None:
    """Run a one-shot prompt against the configured model.

    Parameters
    ----------
    args:
        Parsed command-line arguments.
    """
    cfg = get_config()
    model = args.model or cfg.ollama_model
    prompt = args.prompt

    if not prompt and not args.stdin:
        console.print("[red]Error:[/red] No prompt provided.")
        console.print("Usage: ollama-cli run <prompt>")
        console.print("       echo 'prompt' | ollama-cli run --stdin")
        console.print("       ollama-cli run --model {model} <prompt>")
        sys.exit(1)

    # Read from stdin if --stdin flag is set
    if args.stdin:
        prompt = sys.stdin.read()

    url = f"{cfg.ollama_host}/api/generate"
    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": args.stream,
    }

    # Add optional parameters
    if args.system:
        payload["system"] = args.system
    if args.temperature is not None:
        payload["temperature"] = args.temperature
    if args.top_k is not None:
        payload["top_k"] = args.top_k
    if args.top_p is not None:
        payload["top_p"] = args.top_p
    if args.max_tokens is not None:
        payload["num_predict"] = args.max_tokens

    try:
        with httpx.stream("POST", url, json=payload, timeout=args.timeout) as response:
            response.raise_for_status()

            full_response = ""
            for line in response.iter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    token = data.get("response", "")
                    if token:
                        if args.stream:
                            sys.stdout.write(token)
                            sys.stdout.flush()
                        else:
                            full_response += token
                    if data.get("done"):
                        break
                except json.JSONDecodeError:
                    continue

            if not args.stream:
                print(full_response)
            else:
                print()  # trailing newline

    except httpx.ConnectError:
        console.print(f"[red]Error:[/red] Cannot connect to Ollama at {cfg.ollama_host}")
        console.print("Make sure Ollama is running: [bold]ollama serve[/bold]")
        sys.exit(1)
    except httpx.HTTPStatusError as exc:
        console.print(f"[red]Error:[/red] HTTP {exc.response.status_code} from Ollama API")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the run command argument parser."""
    parser = argparse.ArgumentParser(
        prog="ollama-cli run",
        description="Generate a response from a prompt",
        epilog="""
Examples:
  ollama-cli run "What is the capital of France?"
  ollama-cli run "Tell me a joke" --model llama3.2
  echo "Summarize this" | ollama-cli run --stdin
  ollama-cli run "Code a python function" --temperature 0.7
        """,
    )
    parser.add_argument("prompt", nargs="?", type=str, help="The prompt to send")
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Override model (default: from config)",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        default=False,
        help="Disable streaming output (wait for full response)",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        default=False,
        help="Read prompt from stdin",
    )
    parser.add_argument(
        "--system",
        type=str,
        default=None,
        help="System prompt to override the model's default",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Sampling temperature (0.0 - 1.0, higher = more creative)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=None,
        help="Top-k sampling parameter",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=None,
        help="Top-p (nucleus) sampling parameter",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help="Maximum number of tokens to generate",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Request timeout in seconds (default: 120)",
    )

    # Handle --no-stream as negative for stream flag
    def set_stream_flag(args: argparse.Namespace) -> None:
        args.stream = not args.no_stream

    parser.set_defaults(stream=True)
    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    args.stream = not args.no_stream  # Convert --no-stream to stream flag
    handle_run(args)