#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
SubagentStop hook: logs when a subagent finishes.

GOTCHA Layer: Orchestration + Transparency
ATLAS Phase: Assemble (completion)

Reads agent_id, agent_type, and session_id from stdin JSON.
Logs subagent completion details to logs/subagent_stop.json.
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


def log_subagent_stop(payload: dict) -> None:
    """Log subagent stop event."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "subagent_stop.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_id": payload.get("agent_id", "unknown"),
        "agent_type": payload.get("agent_type", "unknown"),
        "session_id": payload.get("session_id", "unknown"),
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Read stdin, log subagent stop, output JSON."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    log_subagent_stop(payload)

    result = {
        "status": "subagent_stopped",
        "agent_id": payload.get("agent_id", "unknown"),
        "agent_type": payload.get("agent_type", "unknown"),
        "session_id": payload.get("session_id", "unknown"),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
