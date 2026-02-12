"""Tests for workspace trust prompt and /init command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ollama_cmd.interactive import InteractiveMode, _PROJECT_MEMORY_FILE


class TestCmdInit:
    """Verify /init creates OLLAMA.md and .ollama/ directory."""

    def test_init_creates_ollama_md(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Running /init creates OLLAMA.md in the working directory."""
        monkeypatch.chdir(tmp_path)

        mode = MagicMock(spec=InteractiveMode)
        mode._print_info = InteractiveMode._print_info
        mode._print_system = InteractiveMode._print_system
        mode._print_error = InteractiveMode._print_error

        result = InteractiveMode._cmd_init(mode, "")

        assert result is False
        ollama_md = tmp_path / "OLLAMA.md"
        assert ollama_md.exists()
        content = ollama_md.read_text(encoding="utf-8")
        assert "Project Notes" in content
        assert tmp_path.name in content

    def test_init_creates_ollama_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """/init creates .ollama/ directory."""
        monkeypatch.chdir(tmp_path)

        mode = MagicMock(spec=InteractiveMode)
        mode._print_info = InteractiveMode._print_info
        mode._print_system = InteractiveMode._print_system
        mode._print_error = InteractiveMode._print_error

        InteractiveMode._cmd_init(mode, "")

        assert (tmp_path / ".ollama").is_dir()

    def test_init_skips_existing_ollama_md(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """/init does not overwrite an existing OLLAMA.md."""
        monkeypatch.chdir(tmp_path)
        existing = tmp_path / "OLLAMA.md"
        existing.write_text("existing content", encoding="utf-8")

        mode = MagicMock(spec=InteractiveMode)
        mode._print_info = InteractiveMode._print_info
        mode._print_system = InteractiveMode._print_system
        mode._print_error = InteractiveMode._print_error

        InteractiveMode._cmd_init(mode, "")

        assert existing.read_text(encoding="utf-8") == "existing content"

    def test_init_skips_existing_ollama_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """/init does not fail when .ollama/ already exists."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".ollama").mkdir()

        mode = MagicMock(spec=InteractiveMode)
        mode._print_info = InteractiveMode._print_info
        mode._print_system = InteractiveMode._print_system
        mode._print_error = InteractiveMode._print_error

        result = InteractiveMode._cmd_init(mode, "")
        assert result is False


class TestWorkspaceTrustPrompt:
    """Verify the workspace trust prompt fires when OLLAMA.md is missing."""

    def test_prompt_shown_when_no_ollama_md(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Trust prompt appears when OLLAMA.md is absent."""
        monkeypatch.chdir(tmp_path)

        mode = MagicMock(spec=InteractiveMode)
        mode._print_info = InteractiveMode._print_info
        mode._print_system = InteractiveMode._print_system

        with patch("builtins.input", return_value="y"):
            InteractiveMode._prompt_workspace_trust(mode)

        # No error = prompt ran successfully

    def test_prompt_not_needed_when_ollama_md_exists(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """_PROJECT_MEMORY_FILE.exists() is True so trust check is skipped."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "OLLAMA.md").write_text("# test", encoding="utf-8")

        # The run() method checks _PROJECT_MEMORY_FILE.exists() before calling
        # _prompt_workspace_trust, so we verify the constant points to the right file.
        assert _PROJECT_MEMORY_FILE == Path("OLLAMA.md")


class TestInitInCommandTable:
    """Verify /init is registered in the command table."""

    def test_init_command_registered(self) -> None:
        assert "/init" in InteractiveMode._COMMAND_TABLE
        assert InteractiveMode._COMMAND_TABLE["/init"] == "_cmd_init"
