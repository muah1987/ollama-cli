#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Pre-tool-use hook: validates tool calls before execution.

GOTCHA Layer: Orchestration + Guardrails
ATLAS Phase: Link (validation)

Reads tool_name and tool_inputs from stdin JSON, performs risk scoring,
and returns a permission decision (allow/deny/ask) with reasoning.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Commands that are always blocked
BLOCKED_COMMANDS: set[str] = {
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    "format",
    ":(){:|:&};:",
    "dd if=/dev/zero",
    "dd if=/dev/random",
    "> /dev/sda",
    "chmod -R 777 /",
    "chown -R",
}

# Substrings in commands that raise risk
HIGH_RISK_PATTERNS: list[str] = [
    "rm -rf",
    "rm -r /",
    "sudo rm",
    "format c:",
    "mkfs.",
    "dd if=",
    "> /dev/",
    ":(){ :|:&};:",
    "--no-preserve-root",
    "chmod 777",
    "curl | sh",
    "curl | bash",
    "wget | sh",
    "wget | bash",
]

MEDIUM_RISK_PATTERNS: list[str] = [
    "sudo ",
    "chmod ",
    "chown ",
    "kill ",
    "pkill ",
    "systemctl ",
    "service ",
    "iptables ",
    "pip install",
    "npm install -g",
    "git push --force",
    "git reset --hard",
    "DROP TABLE",
    "DROP DATABASE",
    "DELETE FROM",
    "TRUNCATE",
]

# Tools that are inherently higher risk
HIGH_RISK_TOOLS: set[str] = {
    "Bash",
    "Execute",
    "Shell",
    "Terminal",
    "RunCommand",
}

LOW_RISK_TOOLS: set[str] = {
    "Read",
    "Glob",
    "Grep",
    "Search",
    "WebFetch",
    "WebSearch",
}


# ---------------------------------------------------------------------------
# Risk scoring
# ---------------------------------------------------------------------------

def compute_risk_score(tool_name: str, tool_inputs: dict) -> tuple[int, list[str]]:
    """Return a risk score 0-100 and list of reasons."""
    score = 0
    reasons: list[str] = []

    # Base risk by tool type
    if tool_name in HIGH_RISK_TOOLS:
        score += 30
        reasons.append(f"Tool '{tool_name}' is a high-risk execution tool")
    elif tool_name in LOW_RISK_TOOLS:
        score += 5
    else:
        score += 15

    # Inspect command content if present
    command_text = ""
    for key in ("command", "cmd", "script", "code", "input"):
        val = tool_inputs.get(key, "")
        if isinstance(val, str):
            command_text += " " + val

    command_lower = command_text.lower().strip()

    # Check for blocked commands
    for blocked in BLOCKED_COMMANDS:
        if blocked in command_lower:
            return 100, [f"Blocked command detected: '{blocked}'"]

    # Check high-risk patterns
    for pattern in HIGH_RISK_PATTERNS:
        if pattern.lower() in command_lower:
            score += 40
            reasons.append(f"High-risk pattern: '{pattern}'")

    # Check medium-risk patterns
    for pattern in MEDIUM_RISK_PATTERNS:
        if pattern.lower() in command_lower:
            score += 20
            reasons.append(f"Medium-risk pattern: '{pattern}'")

    # File path risk: writing to system directories
    for key in ("file_path", "path", "destination"):
        path_val = tool_inputs.get(key, "")
        if isinstance(path_val, str):
            if path_val.startswith("/etc/") or path_val.startswith("/usr/") or path_val.startswith("/boot/"):
                score += 30
                reasons.append(f"Writing to system directory: {path_val}")
            elif path_val.startswith("/home/") or path_val.startswith(os.path.expanduser("~")):
                score += 10
                reasons.append(f"Writing to home directory: {path_val}")

    # Cap at 100
    score = min(score, 100)

    if not reasons:
        reasons.append("No specific risks identified")

    return score, reasons


def make_decision(risk_score: int) -> str:
    """Return permission decision based on risk score."""
    if risk_score >= 80:
        return "deny"
    elif risk_score >= 50:
        return "ask"
    else:
        return "allow"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_event(payload: dict, risk_score: int, decision: str, reasons: list[str]) -> None:
    """Append a log entry to the pre_tool_use log file."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "pre_tool_use.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_name": payload.get("tool_name", "unknown"),
        "tool_inputs": payload.get("tool_inputs", {}),
        "risk_score": risk_score,
        "decision": decision,
        "reasons": reasons,
    }

    # Append to JSON-lines file
    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Read stdin, evaluate risk, output decision JSON."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    tool_name = payload.get("tool_name", "unknown")
    tool_inputs = payload.get("tool_inputs", {})

    risk_score, reasons = compute_risk_score(tool_name, tool_inputs)
    decision = make_decision(risk_score)

    # Log the event
    log_event(payload, risk_score, decision, reasons)

    # Output decision
    result = {
        "permissionDecision": decision,
        "reason": "; ".join(reasons),
        "risk_score": risk_score,
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()
