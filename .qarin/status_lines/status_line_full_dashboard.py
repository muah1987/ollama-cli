#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Status Line: Full Dashboard - Combined status display for Qarin CLI.

GOTCHA/ATLAS: Execution Layer status line.
Combines model info, token counter, provider health, and cost into a
single compact dashboard line.

Format: [ollama] codestral:latest | tok: 1.2k/4k (30%) @ 42/s | ● Ollama ○ Claude | $0.00

Reads from stdin JSON with all fields:
{
    "provider": "ollama",
    "model": "codestral:latest",
    "tokens": {
        "prompt": 100,
        "completion": 200,
        "total": 1200,
        "per_second": 42.3
    },
    "context": {
        "used": 1200,
        "max": 4096,
        "percentage": 29.3
    },
    "providers": {
        "ollama": true,
        "claude": false,
        "gemini": false,
        "codex": false
    },
    "cost": 0.0
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
    format_tokens,
    safe_read_stdin,
)

# Provider display order
PROVIDER_NAMES = ["Ollama", "Claude", "Gemini", "Codex"]


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
    """Generate the full dashboard status line."""
    # Provider and model
    provider = data.get("provider", "ollama")
    model = data.get("model", "unknown")

    # Token data
    tokens = data.get("tokens", {}) or {}
    total = tokens.get("total", 0) or 0
    per_second = tokens.get("per_second", 0) or 0

    # Context data
    context = data.get("context", {}) or {}
    ctx_max = context.get("max", 0) or 0
    ctx_pct = context.get("percentage", 0) or 0
    pct_int = int(ctx_pct)

    # Provider health
    providers = data.get("providers", {}) or {}

    # Cost
    cost = data.get("cost", 0) or 0

    # Format compact token counts
    total_str = format_tokens(total)
    max_str = format_tokens(ctx_max)

    # Speed: compact integer format
    speed_int = int(per_second) if per_second else 0

    # Context color
    ctx_color = get_context_color(ctx_pct)

    # Build provider dots (compact)
    dot_parts = []
    for name in PROVIDER_NAMES:
        key = name.lower()
        available = providers.get(key, False)
        if available:
            dot_parts.append(f"{GREEN}\u25cf{RESET} {name}")
        else:
            dot_parts.append(f"{DIM}\u25cb{RESET} {name}")
    providers_str = " ".join(dot_parts)

    # Cost string
    cost_str = f"${float(cost):.2f}"

    # Build the line
    provider_part = colorize(f"[{provider}]", DIM)
    model_part = colorize(model, CYAN + BOLD)
    tok_part = f"{DIM}tok:{RESET} {ctx_color}{total_str}/{max_str} ({pct_int}%){RESET} {DIM}@{RESET} {speed_int}/s"

    return (
        f"{provider_part} {model_part} {DIM}|{RESET} "
        f"{tok_part} {DIM}|{RESET} "
        f"{providers_str} {DIM}|{RESET} "
        f"{GREEN}{cost_str}{RESET}"
    )


def main() -> None:
    try:
        data = safe_read_stdin()
        line = generate_status_line(data)
        print(line)
    except Exception:
        print("dashboard unavailable")

    sys.exit(0)


if __name__ == "__main__":
    main()
