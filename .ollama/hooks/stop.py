#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Stop hook: performs final cleanup and prints session summary.

GOTCHA Layer: Orchestration + Transparency
ATLAS Phase: Stress-test (final state)

Reads session_id and cost from stdin JSON.
Performs final cleanup, prints session summary with duration,
tokens used, and cost.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Session summary
# ---------------------------------------------------------------------------

def compute_session_summary(payload: dict) -> dict:
    """Compute final session summary metrics."""
    session_id = payload.get("session_id", "unknown")
    cost = payload.get("cost", 0.0)
    duration_seconds = payload.get("duration_seconds", 0)
    tokens_used = payload.get("tokens_used", 0)
    tokens_input = payload.get("tokens_input", 0)
    tokens_output = payload.get("tokens_output", 0)

    # Format duration
    if duration_seconds > 0:
        minutes, seconds = divmod(int(duration_seconds), 60)
        hours, minutes = divmod(minutes, 60)
        if hours > 0:
            duration_str = f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            duration_str = f"{minutes}m {seconds}s"
        else:
            duration_str = f"{seconds}s"
    else:
        duration_str = "unknown"

    return {
        "session_id": session_id,
        "duration": duration_str,
        "duration_seconds": duration_seconds,
        "tokens_used": tokens_used,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "cost_usd": cost,
        "stopped_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

def perform_cleanup() -> list[str]:
    """Perform any final cleanup tasks. Returns list of actions taken."""
    actions: list[str] = []

    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )

    # Clean up any stale temp files in .tmp/
    tmp_dir = Path(project_dir) / ".tmp"
    if tmp_dir.exists():
        stale_count = 0
        for tmp_file in tmp_dir.iterdir():
            if tmp_file.is_file() and tmp_file.suffix in (".tmp", ".lock"):
                try:
                    tmp_file.unlink()
                    stale_count += 1
                except OSError:
                    pass
        if stale_count > 0:
            actions.append(f"Cleaned {stale_count} stale temp files")

    return actions


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_stop(payload: dict, summary: dict, cleanup_actions: list[str]) -> None:
    """Log the stop event."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "stop.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **summary,
        "cleanup_actions": cleanup_actions,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def print_summary(summary: dict) -> None:
    """Print session summary to stderr."""
    lines = [
        "",
        "-" * 60,
        "  SESSION STOPPED",
        "-" * 60,
        f"  Session:    {summary['session_id']}",
        f"  Duration:   {summary['duration']}",
        f"  Tokens:     {summary['tokens_used']:,} total "
        f"({summary['tokens_input']:,} in / {summary['tokens_output']:,} out)",
        f"  Cost:       ${summary['cost_usd']:.4f}",
        "-" * 60,
        "",
    ]
    print("\n".join(lines), file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Read stdin, cleanup, print summary, log event."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    summary = compute_session_summary(payload)
    cleanup_actions = perform_cleanup()

    # Log the event
    log_stop(payload, summary, cleanup_actions)

    # Print summary to stderr
    print_summary(summary)

    # Output structured result to stdout
    result = {
        "status": "stopped",
        **summary,
        "cleanup_actions": cleanup_actions,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
