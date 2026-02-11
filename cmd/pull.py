#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""pull command -- Pull a model from the registry."""

from __future__ import annotations

import argparse

from rich.console import Console

version = "0.1.0"
console = Console()


def handle_pull(_args: argparse.Namespace) -> None:
    """Pull a model from the registry."""
    console.print("[yellow]Pull command coming soon...[/yellow]")


def build_parser() -> argparse.ArgumentParser:
    """Build the pull command argument parser."""
    parser = argparse.ArgumentParser(
        prog="ollama-cli pull",
        description="Pull a model from the registry",
    )
    parser.add_argument("model_name", nargs="?", type=str, help="Model to pull")
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_pull(args)
