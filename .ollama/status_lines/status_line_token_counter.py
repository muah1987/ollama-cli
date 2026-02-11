#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Status Line: Token Counter - Token usage display for Ollama CLI.

GOTCHA/ATLAS: Execution Layer status line.
Displays model name, token counts, generation speed, and a color-coded
context window progress bar.

Format: [llama3.2] tok: 1,234/4,096 (30%) | 42.3 tok/s | ctx: 30% ████░░░░░░

Reads from stdin JSON:
{
    "model": "llama3.2",
    "tokens": {
        "prompt": 100,
        "completion": 200,
        "total": 300,
        "per_second": 42.3
    },
    "context": {
        "used": 300,
        "max": 4096,
        "percentage": 7.3
    }
}
"""

import sys
from pathlib import Path

# Add status_lines directory to path for status_utils import
sys.path.insert(0, str(Path(__file__).resolve().parent))
from status_utils import (
    BOLD,
    CYAN,
    DIM,
    GREEN,
    MAGENTA,
    RED,
    RESET,
    YELLOW,
    colorize,
    format_speed,
    format_tokens,
    progress_bar,
    safe_read_stdin,
)


def get_context_color(percentage: float) -> str:
    """Return ANSI color code based on context usage percentage."""
    if percentage < 50:
        return GREEN
    elif percentage < 75:
        return YELLOW
    elif percentage < 90:
        return MAGENTA
    else:
        return RED


def generate_status_line(data: dict) -> str:
    """Generate the token counter status line."""
    # Model name
    model = data.get("model", "unknown")

    # Token data
    tokens = data.get("tokens", {}) or {}
    total = tokens.get("total", 0) or 0
    per_second = tokens.get("per_second", 0) or 0

    # Context data
    context = data.get("context", {}) or {}
    ctx_used = context.get("used", 0) or 0
    ctx_max = context.get("max", 0) or 0
    ctx_pct = context.get("percentage", 0) or 0

    # Format token counts
    total_str = format_tokens(total)
    max_str = format_tokens(ctx_max)
    pct_int = int(ctx_pct)

    # Speed
    speed_str = format_speed(per_second)

    # Context bar with color coding
    ctx_color = get_context_color(ctx_pct)
    bar = progress_bar(ctx_used, ctx_max)

    # Build the line
    model_part = colorize(f"[{model}]", CYAN + BOLD)
    tok_part = f"{DIM}tok:{RESET} {total_str}/{max_str} ({pct_int}%)"
    speed_part = colorize(speed_str, GREEN)
    ctx_part = f"{DIM}ctx:{RESET} {ctx_color}{pct_int}% {bar}{RESET}"

    return f"{model_part} {tok_part} {DIM}|{RESET} {speed_part} {DIM}|{RESET} {ctx_part}"


def main() -> None:
    try:
        data = safe_read_stdin()
        line = generate_status_line(data)
        print(line)
    except Exception:
        print("token counter unavailable")

    sys.exit(0)


if __name__ == "__main__":
    main()
