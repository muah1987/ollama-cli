#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Hook runner: executes hook scripts defined in settings.json.

Provides the HookRunner class that loads hook configuration and
dispatches events to the appropriate hook commands via subprocess.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class HookResult:
    """Result from executing a single hook."""
    success: bool
    stdout: str = ""
    stderr: str = ""
    return_code: int = 0
    parsed: dict = field(default_factory=dict)
    error: str = ""

    @property
    def permission_decision(self) -> str | None:
        """Extract permissionDecision from parsed output."""
        return self.parsed.get("permissionDecision")

    @property
    def additional_context(self) -> str | None:
        """Extract additionalContext from parsed output."""
        return self.parsed.get("additionalContext")

    @property
    def updated_input(self) -> dict | None:
        """Extract updatedInput from parsed output."""
        return self.parsed.get("updatedInput")


# ---------------------------------------------------------------------------
# HookRunner
# ---------------------------------------------------------------------------

class HookRunner:
    """Loads settings.json and executes hook commands for named events."""

    def __init__(self, settings_path: str | Path | None = None) -> None:
        """Initialize the runner by loading hook configuration.

        Parameters
        ----------
        settings_path:
            Path to the settings.json file. Defaults to
            ``<project_dir>/.ollama/settings.json``.
        """
        if settings_path is None:
            project_dir = os.environ.get(
                "OLLAMA_PROJECT_DIR",
                str(Path(__file__).resolve().parent.parent),
            )
            settings_path = Path(project_dir) / ".ollama" / "settings.json"
        else:
            settings_path = Path(settings_path)

        self._settings_path = settings_path
        self._hooks: dict = {}
        self._load_settings()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def _load_settings(self) -> None:
        """Load and parse the settings.json file."""
        if not self._settings_path.exists():
            self._hooks = {}
            return

        try:
            with open(self._settings_path) as f:
                data = json.load(f)
            self._hooks = data.get("hooks", {})
        except (json.JSONDecodeError, OSError) as exc:
            print(f"[HookRunner] Warning: failed to load {self._settings_path}: {exc}", file=sys.stderr)
            self._hooks = {}

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run_hook(
        self,
        event_name: str,
        payload: dict,
        *,
        timeout: int = 30,
    ) -> list[HookResult]:
        """Execute all hooks registered for *event_name*.

        Parameters
        ----------
        event_name:
            The event name (e.g. ``PreToolUse``, ``SessionStart``).
        payload:
            JSON-serialisable dict sent to the hook on stdin.
        timeout:
            Maximum seconds to wait for each hook command.

        Returns
        -------
        List of :class:`HookResult`, one per matching hook command.
        """
        results: list[HookResult] = []
        hook_entries = self._hooks.get(event_name, [])

        for entry in hook_entries:
            matcher = entry.get("matcher", "")
            commands = entry.get("hooks", [])

            # Matcher filtering: empty string matches everything
            if matcher and not self._matches(matcher, payload):
                continue

            for hook_def in commands:
                if hook_def.get("type") != "command":
                    continue

                command = hook_def.get("command", "")
                if not command:
                    continue

                result = self._execute_command(command, payload, timeout=timeout)
                results.append(result)

        return results

    def is_enabled(self) -> bool:
        """Check if hooks are enabled (settings file exists and has hooks)."""
        return bool(self._hooks)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _matches(matcher: str, payload: dict) -> bool:
        """Check if the matcher pattern matches the payload.

        Currently supports simple tool_name matching.
        An empty matcher matches everything.
        """
        if not matcher:
            return True
        tool_name = payload.get("tool_name", "")
        return matcher == tool_name or matcher in tool_name

    def _execute_command(
        self,
        command: str,
        payload: dict,
        *,
        timeout: int = 30,
    ) -> HookResult:
        """Run a single hook command via subprocess."""
        # Expand environment variables in the command
        expanded_command = os.path.expandvars(command)

        payload_json = json.dumps(payload)

        try:
            proc = subprocess.run(
                expanded_command,
                shell=True,
                input=payload_json,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={**os.environ},
            )

            # Try to parse stdout as JSON
            parsed: dict = {}
            stdout = proc.stdout.strip()
            if stdout:
                try:
                    parsed = json.loads(stdout)
                except json.JSONDecodeError:
                    pass

            return HookResult(
                success=proc.returncode == 0,
                stdout=proc.stdout,
                stderr=proc.stderr,
                return_code=proc.returncode,
                parsed=parsed,
            )

        except subprocess.TimeoutExpired:
            return HookResult(
                success=False,
                return_code=-1,
                error=f"Hook timed out after {timeout}s: {command}",
            )
        except OSError as exc:
            return HookResult(
                success=False,
                return_code=-1,
                error=f"Hook execution failed: {exc}",
            )


# ---------------------------------------------------------------------------
# Direct execution: test mode
# ---------------------------------------------------------------------------

def main() -> None:
    """Test mode: fire a sample SessionStart event."""
    print("=" * 60)
    print("  HookRunner Test Mode")
    print("=" * 60)
    print()

    # Determine settings path
    project_dir = os.environ.get(
        "OLLAMA_PROJECT_DIR",
        str(Path(__file__).resolve().parent.parent),
    )
    settings_path = Path(project_dir) / ".ollama" / "settings.json"

    print(f"Settings path: {settings_path}")
    print(f"Settings exists: {settings_path.exists()}")
    print()

    runner = HookRunner(settings_path)
    print(f"Hooks enabled: {runner.is_enabled()}")
    print()

    if not runner.is_enabled():
        print("No hooks configured. Exiting.")
        return

    # Fire a sample SessionStart event
    sample_payload = {
        "session_id": "test-session-001",
        "model": "llama3.2",
        "source": "test",
        "context_length": 4096,
    }

    print("Firing SessionStart with payload:")
    print(json.dumps(sample_payload, indent=2))
    print()

    results = runner.run_hook("SessionStart", sample_payload)

    print(f"Got {len(results)} result(s):")
    for i, result in enumerate(results):
        print(f"\n  Result {i + 1}:")
        print(f"    Success:     {result.success}")
        print(f"    Return code: {result.return_code}")
        if result.parsed:
            print(f"    Parsed:      {json.dumps(result.parsed, indent=6)}")
        if result.stderr:
            print(f"    Stderr:      {result.stderr[:500]}")
        if result.error:
            print(f"    Error:       {result.error}")

    print()
    print("Test complete.")


if __name__ == "__main__":
    main()
