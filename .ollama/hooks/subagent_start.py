#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
SubagentStart hook: logs when a subagent spawns.

GOTCHA Layer: Orchestration + Transparency
ATLAS Phase: Architect (delegation)

Reads agent_id, agent_type, and session_id from stdin JSON.
Logs subagent spawn details to logs/subagent_start.json.
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


def log_subagent_start(payload: dict) -> None:
    """Log subagent start event."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "subagent_start.json"
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
    """Read stdin, log subagent start, output JSON."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    log_subagent_start(payload)

    result = {
        "status": "subagent_started",
        "agent_id": payload.get("agent_id", "unknown"),
        "agent_type": payload.get("agent_type", "unknown"),
        "session_id": payload.get("session_id", "unknown"),
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
