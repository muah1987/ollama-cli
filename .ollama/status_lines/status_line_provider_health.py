#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

"""
Status Line: Provider Health - Provider availability indicators for Ollama CLI.

GOTCHA/ATLAS: Execution Layer status line.
Displays which LLM providers are available with colored dot indicators,
plus the active model and context window size.

Format: Ollama ● Claude ○ Gemini ○ Codex ○ | model: codestral | ctx: 4096

Reads from stdin JSON:
{
    "providers": {
        "ollama": true,
        "claude": false,
        "gemini": false,
        "codex": false
    },
    "model": "codestral",
    "context_max": 4096
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
    RESET,
    colorize,
    format_tokens,
    safe_read_stdin,
)

# Provider display order
PROVIDER_NAMES = ["Ollama", "Claude", "Gemini", "Codex"]


def generate_status_line(data: dict) -> str:
    """Generate the provider health status line."""
    providers = data.get("providers", {}) or {}
    model = data.get("model", "unknown")
    context_max = data.get("context_max", 0) or 0

    # Build provider dot indicators
    dot_parts = []
    for name in PROVIDER_NAMES:
        key = name.lower()
        available = providers.get(key, False)
        if available:
            dot_parts.append(f"{name} {GREEN}\u25cf{RESET}")
        else:
            dot_parts.append(f"{name} {DIM}\u25cb{RESET}")
    providers_str = " ".join(dot_parts)

    # Model display
    model_str = f"{DIM}model:{RESET} {colorize(model, CYAN + BOLD)}"

    # Context window size
    ctx_str = f"{DIM}ctx:{RESET} {format_tokens(context_max)}"

    return f"{providers_str} {DIM}|{RESET} {model_str} {DIM}|{RESET} {ctx_str}"


def main() -> None:
    try:
        data = safe_read_stdin()
        line = generate_status_line(data)
        print(line)
    except Exception:
        print("provider health unavailable")

    sys.exit(0)


if __name__ == "__main__":
    main()
