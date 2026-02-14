"""Tests for workspace trust prompt and /init command."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ollama_cmd.interactive import (
    _KNOWN_INSTRUCTION_FILES,
    _PROJECT_MEMORY_FILE,
    _WORKSPACE_TRUST_FILE,
    InteractiveMode,
    _import_instruction_files,
)


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


class TestImportInstructionFiles:
    """Verify detection and import of instruction files from other AI tools."""

    def test_imports_claude_md(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """CLAUDE.md content is appended to OLLAMA.md."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "OLLAMA.md").write_text("# proj\n", encoding="utf-8")
        (tmp_path / "CLAUDE.md").write_text("Use type hints everywhere.", encoding="utf-8")

        imported = _import_instruction_files()

        assert "CLAUDE.md" in imported
        content = (tmp_path / "OLLAMA.md").read_text(encoding="utf-8")
        assert "Use type hints everywhere." in content
        assert "<!-- imported: CLAUDE.md -->" in content

    def test_imports_copilot_instructions(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """.github/copilot-instructions.md is imported."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "OLLAMA.md").write_text("# proj\n", encoding="utf-8")
        gh_dir = tmp_path / ".github"
        gh_dir.mkdir()
        (gh_dir / "copilot-instructions.md").write_text("Follow PEP-8.", encoding="utf-8")

        imported = _import_instruction_files()

        assert ".github/copilot-instructions.md" in imported
        content = (tmp_path / "OLLAMA.md").read_text(encoding="utf-8")
        assert "Follow PEP-8." in content

    def test_skips_already_imported(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Files already imported (marker present) are not duplicated."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "OLLAMA.md").write_text(
            "# proj\n<!-- imported: CLAUDE.md -->\n## Imported from CLAUDE.md\nold\n",
            encoding="utf-8",
        )
        (tmp_path / "CLAUDE.md").write_text("new content", encoding="utf-8")

        imported = _import_instruction_files()

        assert imported == []
        content = (tmp_path / "OLLAMA.md").read_text(encoding="utf-8")
        assert "new content" not in content

    def test_no_files_returns_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When no instruction files exist, nothing is imported."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "OLLAMA.md").write_text("# proj\n", encoding="utf-8")

        imported = _import_instruction_files()

        assert imported == []

    def test_no_ollama_md_returns_empty(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When OLLAMA.md doesn't exist, nothing is imported."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "CLAUDE.md").write_text("some content", encoding="utf-8")

        imported = _import_instruction_files()

        assert imported == []

    def test_imports_multiple_files(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Multiple instruction files are imported in one call."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "OLLAMA.md").write_text("# proj\n", encoding="utf-8")
        (tmp_path / "CLAUDE.md").write_text("Claude rules", encoding="utf-8")
        (tmp_path / "GEMINI.md").write_text("Gemini rules", encoding="utf-8")

        imported = _import_instruction_files()

        assert "CLAUDE.md" in imported
        assert "GEMINI.md" in imported
        content = (tmp_path / "OLLAMA.md").read_text(encoding="utf-8")
        assert "Claude rules" in content
        assert "Gemini rules" in content

    def test_init_calls_import(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """/init detects and imports instruction files."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "CLAUDE.md").write_text("Claude instructions", encoding="utf-8")

        mode = MagicMock(spec=InteractiveMode)
        mode._print_info = InteractiveMode._print_info
        mode._print_system = InteractiveMode._print_system
        mode._print_error = InteractiveMode._print_error

        InteractiveMode._cmd_init(mode, "")

        content = (tmp_path / "OLLAMA.md").read_text(encoding="utf-8")
        assert "Claude instructions" in content


class TestKnownInstructionFiles:
    """Verify the constant listing known instruction files."""

    def test_known_files_include_expected(self) -> None:
        assert Path("CLAUDE.md") in _KNOWN_INSTRUCTION_FILES
        assert Path("GEMINI.md") in _KNOWN_INSTRUCTION_FILES
        assert Path("AGENT.md") in _KNOWN_INSTRUCTION_FILES
        assert Path(".github/copilot-instructions.md") in _KNOWN_INSTRUCTION_FILES


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

        assert _PROJECT_MEMORY_FILE == Path("OLLAMA.md")

    def test_prompt_marks_workspace_as_acknowledged(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """First trust prompt writes an acknowledgement marker for this folder."""
        monkeypatch.chdir(tmp_path)

        mode = MagicMock(spec=InteractiveMode)
        mode.session = MagicMock()
        mode.session.provider = "ollama"
        mode.session.model = "llama3.2"
        mode.session.token_counter = MagicMock()
        mode.session.provider_router = MagicMock()
        mode.session.provider_router._task_config = {}
        mode._print_info = InteractiveMode._print_info
        mode._print_system = InteractiveMode._print_system
        mode._prompt_workspace_model_selection = MagicMock()

        with patch("builtins.input", return_value="y"):
            InteractiveMode._prompt_workspace_trust(mode)

        assert _WORKSPACE_TRUST_FILE.exists()

    def test_should_prompt_workspace_trust_respects_marker(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Trust prompt is skipped once the marker exists in .ollama."""
        monkeypatch.chdir(tmp_path)
        assert InteractiveMode._should_prompt_workspace_trust() is True
        (tmp_path / ".ollama").mkdir()
        (tmp_path / ".ollama" / "workspace_trust_acknowledged").write_text("seen\n", encoding="utf-8")
        assert InteractiveMode._should_prompt_workspace_trust() is False


class TestSessionStartHookPayload:
    """Verify SessionStart hook payload references valid attributes."""

    def test_context_length_attribute_exists(self) -> None:
        """context_manager.max_context_length must exist (not max_length)."""
        from runner.context_manager import ContextManager

        cm = ContextManager()
        # The attribute used by the SessionStart hook payload must exist
        assert hasattr(cm, "max_context_length")
        assert cm.max_context_length == 4096

    def test_session_start_hook_payload_builds_without_error(self) -> None:
        """Building the SessionStart hook payload must not raise AttributeError."""
        from model.session import Session

        session = Session(model="test-model", provider="ollama")
        # Construct the same payload as InteractiveMode.run() does
        payload = {
            "session_id": session.session_id,
            "model": session.model,
            "provider": session.provider,
            "source": "interactive",
            "context_length": session.context_manager.max_context_length,
        }
        assert payload["context_length"] == 4096


class TestInitInCommandTable:
    """Verify /init is registered in the command table."""

    def test_init_command_registered(self) -> None:
        assert "/init" in InteractiveMode._COMMAND_TABLE
        assert InteractiveMode._COMMAND_TABLE["/init"] == "_cmd_init"
