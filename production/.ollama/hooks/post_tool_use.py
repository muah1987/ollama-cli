#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Post-tool-use hook: logs tool execution results and tracks usage statistics.

GOTCHA Layer: Tools + Context
ATLAS Phase: Assemble

Reads tool_name, tool_inputs, and tool_output from stdin JSON.
Logs execution details and maintains cumulative tool usage stats.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def get_log_dir() -> Path:
    """Return the logs directory, creating it if needed."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_dir = Path(project_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def log_tool_execution(payload: dict) -> None:
    """Append tool execution details to the post_tool_use log."""
    log_path = get_log_dir() / "post_tool_use.json"

    tool_name = payload.get("tool_name", "unknown")
    tool_inputs = payload.get("tool_inputs", {})
    tool_output = payload.get("tool_output", "")

    # Truncate large outputs for log readability
    output_str = str(tool_output)
    if len(output_str) > 2000:
        output_str = output_str[:2000] + "... [truncated]"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "tool_inputs": tool_inputs,
        "output_length": len(str(tool_output)),
        "output_preview": output_str[:500],
        "success": not _looks_like_error(tool_output),
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def update_usage_stats(payload: dict) -> None:
    """Update cumulative tool usage statistics."""
    stats_path = get_log_dir() / "tool_usage_stats.json"

    # Load existing stats
    stats: dict = {}
    if stats_path.exists():
        try:
            with open(stats_path) as f:
                stats = json.load(f)
        except (json.JSONDecodeError, OSError):
            stats = {}

    tool_name = payload.get("tool_name", "unknown")

    if tool_name not in stats:
        stats[tool_name] = {
            "total_calls": 0,
            "success_count": 0,
            "error_count": 0,
            "first_used": datetime.now(timezone.utc).isoformat(),
            "last_used": None,
        }

    tool_stats = stats[tool_name]
    tool_stats["total_calls"] += 1
    tool_stats["last_used"] = datetime.now(timezone.utc).isoformat()

    if _looks_like_error(payload.get("tool_output", "")):
        tool_stats["error_count"] += 1
    else:
        tool_stats["success_count"] += 1

    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _looks_like_error(output: object) -> bool:
    """Heuristic check if the tool output looks like an error."""
    if output is None:
        return False
    text = str(output).lower()
    error_indicators = [
        "error:",
        "traceback",
        "exception",
        "failed",
        "errno",
        "permission denied",
        "not found",
        "command not found",
    ]
    return any(indicator in text for indicator in error_indicators)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Read stdin, log results, update stats."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    log_tool_execution(payload)
    update_usage_stats(payload)

    # Post-tool hooks typically do not return decision JSON,
    # but we output a confirmation for consistency.
    result = {
        "status": "logged",
        "tool_name": payload.get("tool_name", "unknown"),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
