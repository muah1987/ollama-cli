"""Tests for readline history file handling in interactive mode."""

import readline
from pathlib import Path
from unittest.mock import MagicMock, patch

from ollama_cmd.interactive import InteractiveMode


class TestSetupReadlineCorruptHistory:
    """Verify _setup_readline recovers from a corrupted history file."""

    def test_corrupted_history_file_is_removed(self, tmp_path: Path) -> None:
        """When read_history_file raises OSError, the corrupt file is deleted."""
        history_dir = tmp_path / ".ollama"
        history_file = history_dir / "history"
        history_dir.mkdir()
        history_file.write_text("corrupt data")

        with (
            patch("ollama_cmd.interactive._HISTORY_DIR", history_dir),
            patch("ollama_cmd.interactive._HISTORY_FILE", history_file),
            patch.object(readline, "read_history_file", side_effect=OSError(22, "Invalid argument")),
            patch.object(readline, "set_history_length"),
            patch.object(readline, "set_completer"),
            patch.object(readline, "parse_and_bind"),
        ):
            mode = MagicMock(spec=InteractiveMode)
            mode._COMMAND_TABLE = {}
            InteractiveMode._setup_readline(mode)

        assert not history_file.exists(), "Corrupted history file should have been removed"

    def test_missing_history_file_no_error(self, tmp_path: Path) -> None:
        """When the history file does not exist, _setup_readline succeeds silently."""
        history_dir = tmp_path / ".ollama"
        history_file = history_dir / "history"

        with (
            patch("ollama_cmd.interactive._HISTORY_DIR", history_dir),
            patch("ollama_cmd.interactive._HISTORY_FILE", history_file),
            patch.object(readline, "read_history_file", side_effect=FileNotFoundError),
            patch.object(readline, "set_history_length"),
            patch.object(readline, "set_completer"),
            patch.object(readline, "parse_and_bind"),
        ):
            mode = MagicMock(spec=InteractiveMode)
            mode._COMMAND_TABLE = {}
            InteractiveMode._setup_readline(mode)

        # No exception raised; history file still absent
        assert not history_file.exists()


class TestSlashCommandCompletion:
    """Verify readline tab completion for slash commands."""

    def test_slash_removed_from_delimiters(self, tmp_path: Path) -> None:
        """After _setup_readline, '/' must not be a completer delimiter."""
        history_dir = tmp_path / ".ollama"
        history_file = history_dir / "history"

        with (
            patch("ollama_cmd.interactive._HISTORY_DIR", history_dir),
            patch("ollama_cmd.interactive._HISTORY_FILE", history_file),
            patch.object(readline, "read_history_file", side_effect=FileNotFoundError),
        ):
            mode = MagicMock(spec=InteractiveMode)
            mode._COMMAND_TABLE = InteractiveMode._COMMAND_TABLE
            InteractiveMode._setup_readline(mode)

        delims = readline.get_completer_delims()
        assert "/" not in delims, "slash must be removed from completer delimiters"

    def test_completer_matches_slash_prefix(self, tmp_path: Path) -> None:
        """Completer should match commands when text starts with '/'."""
        history_dir = tmp_path / ".ollama"
        history_file = history_dir / "history"

        with (
            patch("ollama_cmd.interactive._HISTORY_DIR", history_dir),
            patch("ollama_cmd.interactive._HISTORY_FILE", history_file),
            patch.object(readline, "read_history_file", side_effect=FileNotFoundError),
        ):
            mode = MagicMock(spec=InteractiveMode)
            mode._COMMAND_TABLE = InteractiveMode._COMMAND_TABLE
            InteractiveMode._setup_readline(mode)

        completer = readline.get_completer()
        assert completer is not None

        # /he should match /help
        assert completer("/he", 0) == "/help"
        assert completer("/he", 1) is None

        # /b should match /bug and /build
        matches = []
        for i in range(10):
            m = completer("/b", i)
            if m is None:
                break
            matches.append(m)
        assert "/build" in matches
        assert "/bug" in matches
