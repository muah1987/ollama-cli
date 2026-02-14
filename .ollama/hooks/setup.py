#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Setup hook: fires on init or maintenance triggers.

GOTCHA Layer: Context + Orchestration
ATLAS Phase: Architect (initialization)

Reads trigger ("init" or "maintenance") from stdin JSON.
Loads git status if available, injects additionalContext,
and logs to logs/setup.json.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Git status
# ---------------------------------------------------------------------------


def get_git_status() -> dict | None:
    """Retrieve current git status if inside a git repository."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    try:
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=5,
        )
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=project_dir,
            timeout=5,
        )
        if branch_result.returncode == 0:
            dirty_files = [line.strip() for line in status_result.stdout.strip().splitlines() if line.strip()]
            return {
                "branch": branch_result.stdout.strip(),
                "dirty_file_count": len(dirty_files),
                "is_clean": len(dirty_files) == 0,
            }
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def log_setup(payload: dict, git_status: dict | None) -> None:
    """Log setup event."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "setup.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "trigger": payload.get("trigger", "unknown"),
        "git_status": git_status,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Read stdin, gather context, log, output JSON with additionalContext."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    trigger = payload.get("trigger", "init")
    git_status = get_git_status()

    log_setup(payload, git_status)

    additional_context: list[str] = []
    if git_status:
        additional_context.append(f"Git branch: {git_status['branch']}")
        if git_status["is_clean"]:
            additional_context.append("Working tree is clean")
        else:
            additional_context.append(f"{git_status['dirty_file_count']} dirty file(s)")

    result = {
        "status": "setup_complete",
        "trigger": trigger,
        "additionalContext": "\n".join(additional_context) if additional_context else "",
        "git_status": git_status,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
