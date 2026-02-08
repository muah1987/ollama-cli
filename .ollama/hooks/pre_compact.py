#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Pre-compact hook: saves context snapshot before compaction.

GOTCHA Layer: Context
ATLAS Phase: (context management)

Reads context_window usage from stdin JSON. Saves a snapshot of the
current context state before compaction occurs and logs the trigger reason.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Context snapshot
# ---------------------------------------------------------------------------

def save_context_snapshot(payload: dict) -> str | None:
    """Save a context snapshot before compaction. Returns the snapshot path."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    snapshots_dir = Path(project_dir) / "logs" / "context_snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    session_id = payload.get("session_id", "unknown")
    snapshot_path = snapshots_dir / f"snapshot_{session_id}_{timestamp}.json"

    snapshot = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "context_window": payload.get("context_window", {}),
        "trigger": determine_trigger_reason(payload),
        "messages_count": payload.get("messages_count", 0),
    }

    try:
        with open(snapshot_path, "w") as f:
            json.dump(snapshot, f, indent=2)
        return str(snapshot_path)
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Trigger reason
# ---------------------------------------------------------------------------

def determine_trigger_reason(payload: dict) -> str:
    """Determine why compaction was triggered."""
    context_window = payload.get("context_window", {})
    tokens_used = context_window.get("tokens_used", 0)
    tokens_max = context_window.get("tokens_max", 0)
    manual = payload.get("manual", False)

    if manual:
        return "manual"

    if tokens_max > 0:
        utilization = tokens_used / tokens_max
        if utilization >= 0.95:
            return f"critical_threshold ({utilization:.0%} utilization)"
        elif utilization >= 0.85:
            return f"auto_threshold ({utilization:.0%} utilization)"
        elif utilization >= 0.70:
            return f"approaching_threshold ({utilization:.0%} utilization)"

    return "unknown"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_pre_compact(payload: dict, trigger_reason: str, snapshot_path: str | None) -> None:
    """Log the pre-compact event."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "pre_compact.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    context_window = payload.get("context_window", {})
    tokens_used = context_window.get("tokens_used", 0)
    tokens_max = context_window.get("tokens_max", 0)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": payload.get("session_id", "unknown"),
        "tokens_used": tokens_used,
        "tokens_max": tokens_max,
        "utilization_pct": round(tokens_used / tokens_max * 100, 1) if tokens_max > 0 else 0.0,
        "trigger_reason": trigger_reason,
        "snapshot_path": snapshot_path,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Read stdin, save snapshot, log compaction trigger."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    trigger_reason = determine_trigger_reason(payload)
    snapshot_path = save_context_snapshot(payload)

    # Log the event
    log_pre_compact(payload, trigger_reason, snapshot_path)

    # Output result
    result = {
        "status": "pre_compact_complete",
        "trigger_reason": trigger_reason,
        "snapshot_saved": snapshot_path is not None,
        "snapshot_path": snapshot_path,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
