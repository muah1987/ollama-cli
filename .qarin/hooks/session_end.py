#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Session end hook: generates session summary and updates project context.

GOTCHA Layer: Context + Transparency
ATLAS Phase: Stress-test

Reads session_id, cost, and context_window from stdin JSON.
Generates a session summary and appends learned patterns to QARIN.md.
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


def generate_summary(payload: dict) -> dict:
    """Generate a summary of the session."""
    session_id = payload.get("session_id", "unknown")
    cost = payload.get("cost", 0.0)
    context_window = payload.get("context_window", {})
    tokens_used = context_window.get("tokens_used", 0)
    tokens_max = context_window.get("tokens_max", 0)
    utilization = (tokens_used / tokens_max * 100) if tokens_max > 0 else 0.0

    return {
        "session_id": session_id,
        "cost_usd": cost,
        "tokens_used": tokens_used,
        "tokens_max": tokens_max,
        "utilization_pct": round(utilization, 1),
        "ended_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# QARIN.md updates
# ---------------------------------------------------------------------------


def append_to_qarin_md(summary: dict) -> bool:
    """Append session summary to QARIN.md if it exists."""
    project_dir = os.environ.get(
        "QARIN_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    qarin_md = Path(project_dir) / "QARIN.md"

    if not qarin_md.exists():
        return False

    try:
        content = qarin_md.read_text(encoding="utf-8")

        # Append a session log entry
        session_entry = (
            f"\n\n<!-- Session log: {summary['session_id']} -->\n"
            f"<!-- Ended: {summary['ended_at']} | "
            f"Tokens: {summary['tokens_used']}/{summary['tokens_max']} "
            f"({summary['utilization_pct']}%) | "
            f"Cost: ${summary['cost_usd']:.4f} -->\n"
        )

        # Only append if it won't make the file excessively large
        if len(content) < 50_000:
            qarin_md.write_text(content + session_entry, encoding="utf-8")
            return True
        return False
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def log_session_end(payload: dict, summary: dict, md_updated: bool) -> None:
    """Log session end event."""
    project_dir = os.environ.get(
        "QARIN_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "session_end.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **summary,
        "qarin_md_updated": md_updated,
        "raw_payload": payload,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Read stdin, generate summary, update QARIN.md, log event."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    summary = generate_summary(payload)
    md_updated = append_to_qarin_md(summary)

    # Log the event
    log_session_end(payload, summary, md_updated)

    # Output summary
    result = {
        "status": "session_ended",
        **summary,
        "qarin_md_updated": md_updated,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
