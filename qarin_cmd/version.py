#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""version command -- Show CLI version."""

from __future__ import annotations

import argparse

VERSION = "0.1.0"


def handle_version(_args: argparse.Namespace) -> None:
    """Show CLI version."""
    print(f"qarin v{VERSION}")


def build_parser() -> argparse.ArgumentParser:
    """Build the version command argument parser."""
    parser = argparse.ArgumentParser(
        prog="qarin version",
        description="Show CLI version",
    )
    return parser


if __name__ == "__main__":
    parser = build_parser()
    args = parser.parse_args()
    handle_version(args)
