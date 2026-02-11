#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Notification hook: handles notification events from the CLI.

GOTCHA Layer: Orchestration
ATLAS Phase: Assemble

Reads notification type and message from stdin JSON.
Handles different notification types (info, warning, error, completion)
and logs them appropriately.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Notification handling
# ---------------------------------------------------------------------------

NOTIFICATION_PREFIXES = {
    "info": "[INFO]",
    "warning": "[WARN]",
    "error": "[ERROR]",
    "completion": "[DONE]",
    "progress": "[PROG]",
}


def handle_notification(payload: dict) -> dict:
    """Process a notification event and return structured result."""
    notif_type = payload.get("type", payload.get("notification_type", "info"))
    message = payload.get("message", "")
    title = payload.get("title", "")
    session_id = payload.get("session_id", "unknown")

    # Normalize type
    notif_type = notif_type.lower().strip()
    if notif_type not in NOTIFICATION_PREFIXES:
        notif_type = "info"

    prefix = NOTIFICATION_PREFIXES[notif_type]

    # Format display message
    display_parts = [prefix]
    if title:
        display_parts.append(title + ":")
    if message:
        display_parts.append(message)
    display_message = " ".join(display_parts)

    # Print to stderr for visibility (errors and warnings get emphasis)
    if notif_type == "error":
        print(f"\n  ** {display_message} **\n", file=sys.stderr)
    elif notif_type == "warning":
        print(f"\n  * {display_message} *\n", file=sys.stderr)
    elif notif_type == "completion":
        print(f"\n  {display_message}\n", file=sys.stderr)

    return {
        "notification_type": notif_type,
        "title": title,
        "message": message,
        "display_message": display_message,
        "session_id": session_id,
    }


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def log_notification(payload: dict, processed: dict) -> None:
    """Log the notification event."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "notification.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **processed,
        "raw_payload": payload,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Read stdin, handle notification, log event."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    processed = handle_notification(payload)

    # Log the event
    log_notification(payload, processed)

    # Output structured result
    result = {
        "status": "notification_handled",
        **processed,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
