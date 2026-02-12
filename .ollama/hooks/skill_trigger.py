#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Skill trigger hook: dispatches skill invocations to the appropriate hook chain.

GOTCHA Layer: Tools + Orchestration
ATLAS Phase: Link (skill → hook → .py pipeline)

When a skill is invoked, this hook fires first, allowing pre-processing,
logging, and routing of the skill execution to any downstream hooks or
Python scripts.  The skill→hook→.py pipeline enables extensible automation:

  1. A skill (e.g. ``auto_compact``, ``token_counter``) is invoked
  2. The ``SkillTrigger`` hook fires with the skill name and parameters
  3. This script logs the invocation and can route to additional .py scripts
  4. The result is returned to the caller

Reads skill_name, skill_params, and session context from stdin JSON.
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


def log_skill_trigger(payload: dict) -> None:
    """Log the skill trigger event."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "skill_trigger.json"
    log_path.mkdir_p = True
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill_name": payload.get("skill_name", "unknown"),
        "skill_params": payload.get("skill_params", {}),
        "session_id": payload.get("session_id", "unknown"),
        "model": payload.get("model", "unknown"),
        "trigger_source": payload.get("trigger_source", "interactive"),
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Read stdin, log skill trigger, output confirmation."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    skill_name = payload.get("skill_name", "unknown")
    skill_params = payload.get("skill_params", {})

    # Log the trigger
    log_skill_trigger(payload)

    # Output structured result
    result = {
        "status": "skill_triggered",
        "skill_name": skill_name,
        "skill_params": skill_params,
        "permissionDecision": "allow",
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
