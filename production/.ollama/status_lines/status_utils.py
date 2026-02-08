#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Status Line Utilities - Shared functions for Ollama CLI status lines.

GOTCHA/ATLAS: Execution Layer utility module.
Provides ANSI color helpers, progress bar generation, token/speed formatting,
and safe stdin reading for all Ollama CLI status lines.
"""

import json
import sys


# --- ANSI Color Constants ---
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[90m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"


def colorize(text: str, color_code: str) -> str:
    """
    Wrap text in an ANSI color escape sequence.

    Args:
        text: The text to colorize.
        color_code: An ANSI escape code (e.g. RED, GREEN, BOLD).

    Returns:
        The text wrapped with the color code and a RESET suffix.
    """
    return f"{color_code}{text}{RESET}"


def progress_bar(used: int | float, total: int | float, width: int = 10) -> str:
    """
    Generate a Unicode progress bar.

    Args:
        used: Current usage value.
        total: Maximum capacity value.
        width: Character width of the bar (default 10).

    Returns:
        A string like "████░░░░░░" representing the fill ratio.
        Returns an empty bar if total is 0 or inputs are invalid.
    """
    try:
        if total <= 0:
            return "\u2591" * width
        ratio = max(0.0, min(1.0, used / total))
        filled = int(ratio * width)
        empty = width - filled
        return "\u2588" * filled + "\u2591" * empty
    except Exception:
        return "\u2591" * width


def format_tokens(n: int | float) -> str:
    """
    Format a token count for display.

    Args:
        n: Number of tokens.

    Returns:
        Formatted string: "1,234" for values under 10,000,
        "1.2k" for values 10,000+, "0" for zero/invalid.
    """
    try:
        n = int(n)
        if n < 0:
            return "0"
        if n >= 10_000:
            return f"{n / 1000:.1f}k"
        return f"{n:,}"
    except Exception:
        return "0"


def format_speed(tps: float) -> str:
    """
    Format tokens-per-second speed for display.

    Args:
        tps: Tokens per second value.

    Returns:
        Formatted string like "42.3 tok/s". Returns "0.0 tok/s" on error.
    """
    try:
        return f"{float(tps):.1f} tok/s"
    except Exception:
        return "0.0 tok/s"


def safe_read_stdin() -> dict:
    """
    Read JSON from stdin safely.

    Returns:
        Parsed dict from stdin JSON. Returns empty dict on any error
        (no input, invalid JSON, non-dict result, etc.).
    """
    try:
        raw = sys.stdin.read()
        if not raw or not raw.strip():
            return {}
        data = json.loads(raw)
        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}
