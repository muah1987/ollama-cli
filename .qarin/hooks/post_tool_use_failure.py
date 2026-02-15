#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
PostToolUseFailure hook: structured error logging when a tool fails.

GOTCHA Layer: Tools + Transparency
ATLAS Phase: Assemble (error handling)

Reads tool_name, tool_input, and error from stdin JSON.
Logs structured error details to logs/post_tool_use_failure.json.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

ERROR_CATEGORIES: dict[str, list[str]] = {
    "permission": ["permission denied", "access denied", "forbidden", "not authorized"],
    "not_found": ["not found", "no such file", "does not exist", "enoent"],
    "timeout": ["timeout", "timed out", "deadline exceeded"],
    "network": ["connection refused", "network unreachable", "dns resolution"],
    "validation": ["invalid", "malformed", "bad request", "syntax error"],
}


def classify_error(error_text: str) -> str:
    """Classify the error into a category."""
    error_lower = error_text.lower()
    for category, patterns in ERROR_CATEGORIES.items():
        for pattern in patterns:
            if pattern in error_lower:
                return category
    return "unknown"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def log_failure(payload: dict, error_category: str) -> None:
    """Log tool failure details."""
    project_dir = os.environ.get(
        "QARIN_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "post_tool_use_failure.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    error_text = str(payload.get("error", ""))
    if len(error_text) > 2000:
        error_text = error_text[:2000] + "... [truncated]"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": payload.get("tool_name", "unknown"),
        "tool_input": payload.get("tool_input", {}),
        "error": error_text,
        "error_category": error_category,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Read stdin, classify error, log failure, output JSON."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    error_text = str(payload.get("error", ""))
    error_category = classify_error(error_text)

    log_failure(payload, error_category)

    result = {
        "status": "failure_logged",
        "tool_name": payload.get("tool_name", "unknown"),
        "error_category": error_category,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
