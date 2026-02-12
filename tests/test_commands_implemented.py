"""
Tests for implemented CLI commands (pull, config, status).

Verifies that the previously-stubbed commands are now fully wired up
and their handler functions contain real logic rather than "coming soon"
placeholders.

Note: Uses subprocess for ``cmd.*`` imports to avoid the stdlib ``cmd``
module collision.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PROJECT_ROOT = str(Path(__file__).parent.parent)


def _run_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )


# ---------------------------------------------------------------------------
# cmd/root.py — stubs removed
# ---------------------------------------------------------------------------


class TestCommandsNotStubs:
    """Verify that all previously-stub commands now contain real logic."""

    @pytest.mark.parametrize(
        "func_name",
        ["cmd_pull", "cmd_config", "cmd_status", "cmd_show", "cmd_create", "cmd_rm", "cmd_cp", "cmd_ps", "cmd_stop"],
    )
    def test_command_is_not_stub(self, func_name: str) -> None:
        """Each command handler should have more than a trivial stub body."""
        result = _run_python(
            f"from cmd.root import {func_name}; "
            f"import inspect; "
            f"src = inspect.getsource({func_name}); "
            f"body_lines = ["
            f"    line for line in src.splitlines()[1:] "
            f"    if line.strip() and not line.lstrip().startswith('#')"
            f"]; "
            f"print(len(body_lines) > 1)"
        )
        assert result.stdout.strip() == "True", f"{func_name} appears to still be a stub"

    def test_pull_delegates_to_module(self) -> None:
        """cmd_pull should delegate to cmd.pull.handle_pull."""
        result = _run_python(
            "from cmd.root import cmd_pull; import inspect; "
            "src = inspect.getsource(cmd_pull); "
            "print('handle_pull' in src)"
        )
        assert result.stdout.strip() == "True"

    def test_config_delegates_to_module(self) -> None:
        """cmd_config should delegate to cmd.config.handle_config."""
        result = _run_python(
            "from cmd.root import cmd_config; import inspect; "
            "src = inspect.getsource(cmd_config); "
            "print('handle_config' in src)"
        )
        assert result.stdout.strip() == "True"

    def test_status_delegates_to_module(self) -> None:
        """cmd_status should delegate to cmd.status.handle_status."""
        result = _run_python(
            "from cmd.root import cmd_status; import inspect; "
            "src = inspect.getsource(cmd_status); "
            "print('handle_status' in src)"
        )
        assert result.stdout.strip() == "True"


# ---------------------------------------------------------------------------
# cmd/pull.py
# ---------------------------------------------------------------------------


class TestPullCommand:
    """Tests for the pull command module."""

    def test_handle_pull_importable(self) -> None:
        result = _run_python("from cmd.pull import handle_pull; print(callable(handle_pull))")
        assert result.stdout.strip() == "True"

    def test_handle_pull_no_model_exits(self) -> None:
        """pull without a model name should exit with an error."""
        result = _run_python(
            "import argparse, sys\n"
            "from cmd.pull import handle_pull\n"
            "args = argparse.Namespace(model_name=None, json=False)\n"
            "try:\n"
            "    handle_pull(args)\n"
            "except SystemExit as e:\n"
            "    print(f'exit:{e.code}')\n"
        )
        assert "exit:1" in result.stdout

    def test_build_parser(self) -> None:
        result = _run_python(
            "from cmd.pull import build_parser; "
            "p = build_parser(); ns = p.parse_args(['llama3.2']); "
            "print(ns.model_name)"
        )
        assert result.stdout.strip() == "llama3.2"

    def test_pull_no_stub_text(self) -> None:
        result = _run_python(
            "from cmd.pull import handle_pull; import inspect; "
            "src = inspect.getsource(handle_pull); "
            "print('coming soon' not in src.lower())"
        )
        assert result.stdout.strip() == "True"


# ---------------------------------------------------------------------------
# cmd/config.py
# ---------------------------------------------------------------------------


class TestConfigCommand:
    """Tests for the config command module."""

    def test_handle_config_importable(self) -> None:
        result = _run_python("from cmd.config import handle_config; print(callable(handle_config))")
        assert result.stdout.strip() == "True"

    def test_handle_config_show_all_json(self) -> None:
        """config with no action --json should produce valid JSON."""
        result = _run_python(
            "import argparse, json; "
            "from cmd.config import handle_config; "
            "args = argparse.Namespace(action=None, key=None, value=None, json=True); "
            "handle_config(args)"
        )
        data = json.loads(result.stdout)
        assert "ollama_host" in data
        assert "provider" in data

    def test_handle_config_get_key_json(self) -> None:
        """config get <key> --json should return that key."""
        result = _run_python(
            "import argparse; "
            "from cmd.config import handle_config; "
            "args = argparse.Namespace(action='get', key='provider', value=None, json=True); "
            "handle_config(args)"
        )
        data = json.loads(result.stdout)
        assert "provider" in data

    def test_handle_config_get_unknown_key_exits(self) -> None:
        """config get <unknown> should exit with an error."""
        result = _run_python(
            "import argparse, sys\n"
            "from cmd.config import handle_config\n"
            "args = argparse.Namespace(action='get', key='nonexistent_key_xyz', value=None, json=False)\n"
            "try:\n"
            "    handle_config(args)\n"
            "except SystemExit as e:\n"
            "    print(f'exit:{e.code}')\n"
        )
        assert "exit:1" in result.stdout

    def test_handle_config_set_sensitive_key_exits(self) -> None:
        """Setting a sensitive key via CLI should be blocked."""
        result = _run_python(
            "import argparse, sys\n"
            "from cmd.config import handle_config\n"
            "args = argparse.Namespace(action='set', key='anthropic_api_key', value='sk-test', json=False)\n"
            "try:\n"
            "    handle_config(args)\n"
            "except SystemExit as e:\n"
            "    print(f'exit:{e.code}')\n"
        )
        assert "exit:1" in result.stdout

    def test_build_parser(self) -> None:
        result = _run_python(
            "from cmd.config import build_parser; "
            "p = build_parser(); ns = p.parse_args(['set', 'ollama_model', 'llama3']); "
            "print(f'{ns.action}|{ns.key}|{ns.value}')"
        )
        assert result.stdout.strip() == "set|ollama_model|llama3"

    def test_config_masks_sensitive_values(self) -> None:
        """Sensitive keys should be masked in JSON output."""
        result = _run_python(
            "import argparse, json; "
            "from api.config import get_config; "
            "from cmd.config import handle_config; "
            "cfg = get_config(); cfg.anthropic_api_key = 'test-secret-key'; "
            "args = argparse.Namespace(action=None, key=None, value=None, json=True); "
            "handle_config(args)"
        )
        data = json.loads(result.stdout)
        assert data["anthropic_api_key"] == "****"
        assert "test-secret-key" not in result.stdout


# ---------------------------------------------------------------------------
# cmd/status.py
# ---------------------------------------------------------------------------


class TestStatusCommand:
    """Tests for the status command module."""

    def test_handle_status_importable(self) -> None:
        result = _run_python("from cmd.status import handle_status; print(callable(handle_status))")
        assert result.stdout.strip() == "True"

    def test_handle_status_json_output(self) -> None:
        """status --json should produce valid JSON with expected keys."""
        result = _run_python(
            "import argparse; "
            "from cmd.status import handle_status; "
            "args = argparse.Namespace(json=True); "
            "handle_status(args)"
        )
        data = json.loads(result.stdout)
        assert "server" in data
        assert "config" in data
        assert "sessions" in data
        assert data["server"]["status"] in ("running", "offline")

    def test_handle_status_config_section(self) -> None:
        """status JSON should include provider and model info."""
        result = _run_python(
            "import argparse; "
            "from cmd.status import handle_status; "
            "args = argparse.Namespace(json=True); "
            "handle_status(args)"
        )
        data = json.loads(result.stdout)
        assert "provider" in data["config"]
        assert "model" in data["config"]
        assert "context_length" in data["config"]

    def test_build_parser(self) -> None:
        result = _run_python(
            "from cmd.status import build_parser; "
            "p = build_parser(); ns = p.parse_args(['--json']); "
            "print(ns.json)"
        )
        assert result.stdout.strip() == "True"

    def test_status_no_stub_text(self) -> None:
        result = _run_python(
            "from cmd.status import handle_status; import inspect; "
            "src = inspect.getsource(handle_status); "
            "print('coming soon' not in src.lower())"
        )
        assert result.stdout.strip() == "True"
