#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""status command -- Show current session status."""

from __future__ import annotations

import argparse
from rich.console import Console

version = "0.1.0"
console = Console()


def handle_status(_args: argparse.Namespace) -> None:
    """Show current session status."""
    console.print("[yellow]Status command coming soon...[/yellow]")


def build_parser() -> argparse.ArgumentParser:
    """Build the status command argument parser."""
    parser = argparse.ArgumentParser(
        prog="ollama-cli status",
        description="Show current session status",
    )
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_status(args)