#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Session start hook: initializes session context and detects providers.

GOTCHA Layer: Context + Args
ATLAS Phase: Architect

Reads session_id, model, and source from stdin JSON.
Loads OLLAMA.md for project context, detects available providers,
and prints a session banner.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------

def check_ollama_health(host: str = "http://localhost:11434") -> bool:
    """Check if the Ollama server is reachable."""
    try:
        req = urllib.request.Request(f"{host}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3):
            return True
    except (urllib.error.URLError, OSError, TimeoutError):
        return False


def detect_providers() -> dict[str, bool]:
    """Detect which AI providers are available."""
    # Load environment
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    env_path = Path(project_dir) / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")

    providers = {
        "ollama": check_ollama_health(ollama_host),
        "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY", "").strip()),
        "openai": bool(os.environ.get("OPENAI_API_KEY", "").strip()),
        "gemini": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
    }
    return providers


# ---------------------------------------------------------------------------
# Project context
# ---------------------------------------------------------------------------

def load_project_context() -> str | None:
    """Load OLLAMA.md if it exists in the project root."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    ollama_md = Path(project_dir) / "OLLAMA.md"
    if ollama_md.exists():
        try:
            return ollama_md.read_text(encoding="utf-8")
        except OSError:
            return None
    return None


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log_session_start(payload: dict, providers: dict[str, bool], context_loaded: bool) -> None:
    """Log session start event."""
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent.parent),
    )
    log_path = Path(project_dir) / "logs" / "session_start.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": payload.get("session_id", "unknown"),
        "model": payload.get("model", "unknown"),
        "source": payload.get("source", "unknown"),
        "providers": providers,
        "context_loaded": context_loaded,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

def print_banner(payload: dict, providers: dict[str, bool], context_loaded: bool) -> None:
    """Print a session startup banner to stderr for visibility."""
    model = payload.get("model", "unknown")
    session_id = payload.get("session_id", "unknown")
    source = payload.get("source", "cli")
    context_length = payload.get("context_length", 4096)

    available = [name for name, ok in providers.items() if ok]
    unavailable = [name for name, ok in providers.items() if not ok]

    lines = [
        "",
        "=" * 60,
        "  OLLAMA-CLI SESSION STARTED",
        "=" * 60,
        f"  Session:   {session_id}",
        f"  Model:     {model}",
        f"  Source:    {source}",
        f"  Context:   {context_length} tokens",
        f"  Providers: {', '.join(available) if available else 'none detected'}",
    ]
    if unavailable:
        lines.append(f"  Inactive:  {', '.join(unavailable)}")
    if context_loaded:
        lines.append("  Project:   OLLAMA.md loaded")
    lines.append("=" * 60)
    lines.append("")

    print("\n".join(lines), file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Read stdin, detect providers, print banner, log event."""
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        payload = {}

    providers = detect_providers()
    context_text = load_project_context()
    context_loaded = context_text is not None

    # Log the event
    log_session_start(payload, providers, context_loaded)

    # Print banner to stderr (informational)
    print_banner(payload, providers, context_loaded)

    # Output structured response to stdout
    result = {
        "status": "session_started",
        "session_id": payload.get("session_id", "unknown"),
        "providers": providers,
        "context_loaded": context_loaded,
    }
    if context_loaded:
        # Provide a truncated preview so caller knows context was found
        result["context_preview"] = (context_text or "")[:500]

    print(json.dumps(result))


if __name__ == "__main__":
    main()
