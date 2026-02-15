#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
PermissionRequest hook: permission auditing with auto-allow for read-only ops.

GOTCHA Layer: Guardrails + Transparency
ATLAS Phase: Link (permission gate)

Reads tool_name and tool_input from stdin JSON.
Auto-allows read-only tools (Read, Glob, Grep, safe Bash commands).
Returns a permissionDecision of allow, ask, or deny.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Permission rules
# ---------------------------------------------------------------------------

READ_ONLY_TOOLS: set[str] = {
    "Read",
    "Glob",
    "Grep",
    "Search",
    "WebFetch",
    "WebSearch",
    "View",
}

SAFE_BASH_COMMANDS: list[str] = [
    "ls",
    "cat",
    "pwd",
    "echo",
    "head",
    "tail",
    "wc",
    "find",
    "grep",
    "which",
    "whoami",
    "date",
    "env",
    "printenv",
    "uname",
    "file",
    "stat",
    "tree",
    "du",
    "df",
    "git status",
    "git log",
    "git diff",
    "git branch",
    "git show",
]

DENIED_TOOLS: set[str] = {
    "FormatDisk",
    "SystemShutdown",
}


def _is_safe_bash(tool_input: dict) -> bool:
    """Check if a Bash command is read-only / safe."""
    command = tool_input.get("command", "")
    if not command:
        return False

    command_stripped = command.strip()
    for safe_cmd in SAFE_BASH_COMMANDS:
        if command_stripped == safe_cmd or command_stripped.startswith(safe_cmd + " "):
            return True

    # Piped commands where first command is safe
    if "|" in command_stripped:
        first_cmd = command_stripped.split("|")[0].strip()
        for safe_cmd in SAFE_BASH_COMMANDS:
            if first_cmd == safe_cmd or first_cmd.startswith(safe_cmd + " "):
                return True

    return False


def evaluate_permission(tool_name: str, tool_input: dict) -> tuple[str, str]:
    """Evaluate permission for a tool call. Returns (decision, reason)."""
    if tool_name in DENIED_TOOLS:
        return "deny", f"Tool '{tool_name}' is explicitly denied"

    if tool_name in READ_ONLY_TOOLS:
        return "allow", f"Tool '{tool_name}' is a read-only operation"

    if tool_name in ("Bash", "Execute", "Shell", "Terminal"):
        if _is_safe_bash(tool_input):
            return "allow", "Bash command is a safe read-only operation"
        return "ask", "Bash command requires user confirmation"

    return "ask", f"Tool '{tool_name}' requires permission review"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def log_permission(payload: dict, decision: str, reason: str) -> None:
    """Log permission request event."""
    project_dir = os.environ.get(
        "QARIN_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "permission_request.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": payload.get("tool_name", "unknown"),
        "tool_input": payload.get("tool_input", {}),
        "decision": decision,
        "reason": reason,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Read stdin, evaluate permission, log, output decision JSON."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    tool_name = payload.get("tool_name", "unknown")
    tool_input = payload.get("tool_input", {})

    decision, reason = evaluate_permission(tool_name, tool_input)

    log_permission(payload, decision, reason)

    result = {
        "permissionDecision": decision,
        "reason": reason,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
