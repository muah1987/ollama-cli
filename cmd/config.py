#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""config command -- Show/set provider configuration."""

from __future__ import annotations

import argparse

from rich.console import Console

version = "0.1.0"
console = Console()


def handle_config(_args: argparse.Namespace) -> None:
    """Show or set provider configuration."""
    console.print("[yellow]Config command coming soon...[/yellow]")


def build_parser() -> argparse.ArgumentParser:
    """Build the config command argument parser."""
    parser = argparse.ArgumentParser(
        prog="ollama-cli config",
        description="Show/set provider configuration",
    )
    parser.add_argument("action", nargs="?", type=str, help="Action (get/set)")
    parser.add_argument("key", nargs="?", type=str, help="Config key")
    parser.add_argument("value", nargs="?", type=str, help="Config value")
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_config(args)
