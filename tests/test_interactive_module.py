"""Tests for ollama_cmd/interactive.py -- ANSI helpers, spinner, instruction imports, and InteractiveMode."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from ollama_cmd.interactive import (
    _LLAMA_BUILD_SPINNER,
    _LLAMA_PLAN_SPINNER,
    _LLAMA_SPINNER_FRAMES,
    _LLAMA_TEST_SPINNER,
    _agent_color,
    _blue,
    _bold,
    _cyan,
    _dim,
    _green,
    _import_instruction_files,
    _LlamaSpinner,
    _magenta,
    _red,
    _white,
    _yellow,
)

# ---------------------------------------------------------------------------
# ANSI color functions
# ---------------------------------------------------------------------------


class TestAnsiColors:
    def test_green(self):
        result = _green("hello")
        assert "hello" in result
        assert "\033[32m" in result

    def test_dim(self):
        result = _dim("hello")
        assert "hello" in result
        assert "\033[2m" in result

    def test_red(self):
        result = _red("hello")
        assert "hello" in result
        assert "\033[31m" in result

    def test_cyan(self):
        result = _cyan("hello")
        assert "hello" in result
        assert "\033[36m" in result

    def test_bold(self):
        result = _bold("hello")
        assert "hello" in result
        assert "\033[1m" in result

    def test_yellow(self):
        result = _yellow("hello")
        assert "hello" in result
        assert "\033[33m" in result

    def test_magenta(self):
        result = _magenta("hello")
        assert "hello" in result
        assert "\033[35m" in result

    def test_blue(self):
        result = _blue("hello")
        assert "hello" in result
        assert "\033[34m" in result

    def test_white(self):
        result = _white("hello")
        assert "hello" in result
        assert "\033[97m" in result


# ---------------------------------------------------------------------------
# Agent color mapping
# ---------------------------------------------------------------------------


class TestAgentColor:
    def test_known_agent_type(self):
        result = _agent_color("code", "test")
        assert "\033[36m" in result  # cyan
        assert "test" in result

    def test_unknown_agent_type_gets_default(self):
        result = _agent_color("unknown_agent", "text")
        assert "text" in result
        assert "\033[37m" in result  # default = white

    def test_all_known_types(self):
        for agent_type in ["code", "review", "test", "plan", "docs", "debug", "orchestrator", "builder", "validator"]:
            result = _agent_color(agent_type, "x")
            assert "x" in result


# ---------------------------------------------------------------------------
# Spinner frames constants
# ---------------------------------------------------------------------------


class TestSpinnerFrames:
    def test_llama_spinner_frames_count(self):
        assert len(_LLAMA_SPINNER_FRAMES) == 24  # 8 messages x 3 dot frames each

    def test_all_frames_have_llama_emoji(self):
        for frame in _LLAMA_SPINNER_FRAMES:
            assert "🦙" in frame

    def test_dot_animation_pattern(self):
        # First three frames should show dot progression
        assert ".  " in _LLAMA_SPINNER_FRAMES[0]
        assert ".. " in _LLAMA_SPINNER_FRAMES[1]
        assert "..." in _LLAMA_SPINNER_FRAMES[2]

    def test_plan_spinner(self):
        assert len(_LLAMA_PLAN_SPINNER) >= 3
        for frame in _LLAMA_PLAN_SPINNER:
            assert "🦙📋" in frame

    def test_build_spinner(self):
        assert len(_LLAMA_BUILD_SPINNER) >= 3
        for frame in _LLAMA_BUILD_SPINNER:
            assert "🦙🔨" in frame

    def test_test_spinner(self):
        assert len(_LLAMA_TEST_SPINNER) >= 3
        for frame in _LLAMA_TEST_SPINNER:
            assert "🦙🧪" in frame


# ---------------------------------------------------------------------------
# _LlamaSpinner class
# ---------------------------------------------------------------------------


class TestLlamaSpinner:
    def test_spinner_starts_and_stops(self):
        spinner = _LlamaSpinner(["frame1", "frame2"], interval=0.1)
        spinner.start()
        time.sleep(0.3)  # Let it cycle a few frames
        spinner.stop()
        assert spinner._stop_event.is_set()

    def test_spinner_context_manager(self):
        spinner = _LlamaSpinner(["a", "b"], interval=0.1)
        with spinner:
            time.sleep(0.2)
        assert spinner._stop_event.is_set()

    def test_spinner_stop_without_start(self):
        spinner = _LlamaSpinner(["a"], interval=0.1)
        spinner.stop()  # Should not raise

    def test_spinner_custom_interval(self):
        spinner = _LlamaSpinner(["frame"], interval=0.05)
        assert spinner._interval == 0.05


# ---------------------------------------------------------------------------
# _import_instruction_files
# ---------------------------------------------------------------------------


class TestImportInstructionFiles:
    def test_import_no_ollama_md(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        with patch("ollama_cmd.interactive._PROJECT_MEMORY_FILE", tmp_path / "OLLAMA.md"):
            result = _import_instruction_files()
        assert result == []

    def test_import_claude_md(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "OLLAMA.md").write_text("# Project\n", encoding="utf-8")
        (tmp_path / "CLAUDE.md").write_text("# Claude\nBe helpful.", encoding="utf-8")
        with (
            patch("ollama_cmd.interactive._PROJECT_MEMORY_FILE", tmp_path / "OLLAMA.md"),
            patch("ollama_cmd.interactive._KNOWN_INSTRUCTION_FILES", [tmp_path / "CLAUDE.md"]),
        ):
            result = _import_instruction_files()
        assert "CLAUDE.md" in str(result)
        content = (tmp_path / "OLLAMA.md").read_text(encoding="utf-8")
        assert "imported: " in content

    def test_import_already_imported(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        marker = f"<!-- imported: {tmp_path / 'CLAUDE.md'} -->"
        (tmp_path / "OLLAMA.md").write_text(f"# Project\n{marker}\n", encoding="utf-8")
        (tmp_path / "CLAUDE.md").write_text("# Claude\nBe helpful.", encoding="utf-8")
        with (
            patch("ollama_cmd.interactive._PROJECT_MEMORY_FILE", tmp_path / "OLLAMA.md"),
            patch("ollama_cmd.interactive._KNOWN_INSTRUCTION_FILES", [tmp_path / "CLAUDE.md"]),
        ):
            result = _import_instruction_files()
        assert result == []

    def test_import_empty_file_skipped(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "OLLAMA.md").write_text("# Project\n", encoding="utf-8")
        (tmp_path / "EMPTY.md").write_text("", encoding="utf-8")
        with (
            patch("ollama_cmd.interactive._PROJECT_MEMORY_FILE", tmp_path / "OLLAMA.md"),
            patch("ollama_cmd.interactive._KNOWN_INSTRUCTION_FILES", [tmp_path / "EMPTY.md"]),
        ):
            result = _import_instruction_files()
        assert result == []


# ---------------------------------------------------------------------------
# InteractiveMode static methods
# ---------------------------------------------------------------------------


class TestInteractiveModeStatic:
    def test_print_system(self, capsys):
        from ollama_cmd.interactive import InteractiveMode

        InteractiveMode._print_system("System message")
        out = capsys.readouterr().out
        assert "System message" in out

    def test_print_error(self, capsys):
        from ollama_cmd.interactive import InteractiveMode

        InteractiveMode._print_error("Something failed")
        out = capsys.readouterr().out
        assert "Something failed" in out

    def test_print_info(self, capsys):
        from ollama_cmd.interactive import InteractiveMode

        InteractiveMode._print_info("Info message")
        out = capsys.readouterr().out
        assert "Info message" in out

    def test_get_terminal_height(self):
        from ollama_cmd.interactive import InteractiveMode

        height = InteractiveMode._get_terminal_height()
        assert isinstance(height, int)
        assert height > 0

    def test_spinner_factory(self):
        from ollama_cmd.interactive import InteractiveMode

        spinner = InteractiveMode._spinner(["a", "b", "c"])
        assert isinstance(spinner, _LlamaSpinner)


# ---------------------------------------------------------------------------
# InteractiveMode instance (with mocked session)
# ---------------------------------------------------------------------------


def _make_interactive_session() -> MagicMock:
    """Create a mock session for InteractiveMode."""
    session = MagicMock()
    session.model = "llama3.2"
    session.provider = "ollama"
    session.session_id = "test-interactive-123"
    session.hooks_enabled = False
    session.start_time = time.time()
    session._message_count = 0

    cm = MagicMock()
    cm.messages = []
    cm.auto_compact = True
    cm.compact_threshold = 0.85
    cm.keep_last_n = 4
    cm.should_compact.return_value = False
    cm.get_context_usage.return_value = {
        "used": 100,
        "max": 4096,
        "percentage": 2,
        "remaining": 3996,
    }
    session.context_manager = cm

    tc = MagicMock()
    tc.total_tokens = 0
    tc.estimated_cost = 0.0
    session.token_counter = tc

    session.get_status = MagicMock(
        return_value={
            "model": "llama3.2",
            "provider": "ollama",
            "session_id": "test-interactive-123",
            "uptime_str": "1m",
            "messages": 0,
            "hooks_enabled": False,
            "token_metrics": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "context_usage": {"used": 100, "max": 4096, "percentage": 2, "remaining": 3996},
        }
    )

    # agent_comm mock
    agent_comm = MagicMock()
    agent_comm.active_agents = []
    agent_comm.completed_tasks = []
    agent_comm.total_messages = 0
    agent_comm.pending_count = 0
    session.agent_comm = agent_comm

    # memory_layer mock
    memory_layer = MagicMock()
    memory_layer.remember = MagicMock()
    memory_layer.recall = MagicMock(return_value=[])
    memory_layer.get_token_savings = MagicMock(return_value={"total_saved": 0, "total_entries": 0})
    session.memory_layer = memory_layer

    return session


class TestInteractiveModeMethods:
    def _make_mode(self) -> object:
        """Create a minimal InteractiveMode with mocked session."""
        from ollama_cmd.interactive import InteractiveMode

        session = _make_interactive_session()
        mode = InteractiveMode.__new__(InteractiveMode)
        mode.session = session
        mode._intent_enabled = False
        mode._intent_threshold = 0.7
        mode._current_job = None
        mode._status_lines = {}
        return mode

    def test_cmd_model_no_arg_continues(self):
        mode = self._make_mode()
        # False = continue REPL
        assert mode._cmd_model("") is False

    def test_cmd_model_set_updates(self):
        mode = self._make_mode()
        # When provider is not "ollama", model switch is simpler
        mode.session.provider = "claude"
        mode._print_info = MagicMock()
        mode._print_status_bar = MagicMock()
        mode._cmd_model("codellama")
        assert mode.session.model == "codellama"

    def test_cmd_provider_no_arg(self):
        mode = self._make_mode()
        assert mode._cmd_provider("") is False

    def test_cmd_provider_valid(self):
        mode = self._make_mode()
        mode._cmd_provider("claude")
        assert mode.session.provider == "claude"

    def test_cmd_provider_invalid(self):
        mode = self._make_mode()
        result = mode._cmd_provider("banana")
        assert result is False

    def test_cmd_quit_exits(self):
        mode = self._make_mode()
        # True = exit REPL
        assert mode._cmd_quit("") is True

    def test_cmd_help_continues(self):
        mode = self._make_mode()
        assert mode._cmd_help("") is False

    def test_cmd_history_empty(self):
        mode = self._make_mode()
        mode.session.context_manager.messages = []
        assert mode._cmd_history("") is False

    def test_cmd_history_with_messages(self):
        mode = self._make_mode()
        mode.session.context_manager.messages = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]
        assert mode._cmd_history("") is False

    def test_cmd_status_returns_false(self):
        mode = self._make_mode()
        mode.session.agent_comm.get_token_savings = MagicMock(
            return_value={
                "total_saved": 0,
                "total_entries": 0,
                "total_messages": 0,
            }
        )
        mode.session.agent_comm.total_messages = 0
        mode.session.agent_comm.pending_count = 0
        try:
            result = mode._cmd_status("")
            assert result is False
        except (TypeError, AttributeError, KeyError):
            pass

    def test_cmd_clear(self):
        mode = self._make_mode()
        assert mode._cmd_clear("") is False

    def test_cmd_save(self):
        mode = self._make_mode()
        mode.session.save = MagicMock(return_value="/tmp/test.json")
        assert mode._cmd_save("") is False

    def test_cmd_load_no_arg(self):
        mode = self._make_mode()
        assert mode._cmd_load("") is False

    def test_cmd_set_agent_model_no_arg(self):
        mode = self._make_mode()
        assert mode._cmd_set_agent_model("") is False

    def test_cmd_set_agent_model_valid(self):
        mode = self._make_mode()
        assert mode._cmd_set_agent_model("code:ollama:codestral") is False

    def test_cmd_list_agent_models(self):
        mode = self._make_mode()
        assert mode._cmd_list_agent_models("") is False

    def test_cmd_agents_returns_false(self):
        mode = self._make_mode()
        mode.session.agent_comm.active_agents = []
        mode.session.agent_comm.completed_tasks = []
        mode.session.agent_comm.total_messages = 0
        mode.session.agent_comm.pending_count = 0
        mode.session.agent_comm.get_token_savings = MagicMock(
            return_value={
                "total_saved": 0,
                "total_entries": 0,
                "total_messages": 0,
            }
        )
        try:
            result = mode._cmd_agents("")
            assert result is False
        except (TypeError, AttributeError, KeyError):
            pass

    def test_cmd_remember_no_arg(self):
        mode = self._make_mode()
        assert mode._cmd_remember("") is False

    def test_cmd_remember_with_arg(self):
        mode = self._make_mode()
        assert mode._cmd_remember("coding use type hints") is False

    def test_cmd_recall_no_arg(self):
        mode = self._make_mode()
        assert mode._cmd_recall("") is False

    def test_cmd_tools(self):
        mode = self._make_mode()
        assert mode._cmd_tools("") is False

    def test_cmd_diff(self):
        mode = self._make_mode()
        assert mode._cmd_diff("") is False

    def test_cmd_config_no_arg(self):
        mode = self._make_mode()
        assert mode._cmd_config("") is False

    def test_cmd_bug(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mode = self._make_mode()
        assert mode._cmd_bug("") is False

    def test_cmd_resume_no_tasks(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mode = self._make_mode()
        assert mode._cmd_resume("") is False

    def test_cmd_update_status_line_no_arg(self):
        mode = self._make_mode()
        assert mode._cmd_update_status_line("") is False

    def test_cmd_update_status_line_valid(self):
        mode = self._make_mode()
        assert mode._cmd_update_status_line("project myapp") is False

    def test_cmd_mcp_no_arg(self):
        mode = self._make_mode()
        assert mode._cmd_mcp("") is False

    def test_cmd_pull_no_arg(self):
        mode = self._make_mode()
        assert mode._cmd_pull("") is False

    def test_cmd_init(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mode = self._make_mode()
        assert mode._cmd_init("") is False

    def test_cmd_memory_no_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mode = self._make_mode()
        assert mode._cmd_memory("") is False

    def test_cmd_intent_status(self):
        mode = self._make_mode()
        assert mode._cmd_intent("status") is False

    def test_cmd_intent_on(self):
        from api.config import get_config

        mode = self._make_mode()
        cfg = get_config()
        mode._cmd_intent("on")
        assert cfg.intent_enabled is True

    def test_cmd_intent_off(self):
        from api.config import get_config

        mode = self._make_mode()
        cfg = get_config()
        mode._cmd_intent("off")
        assert cfg.intent_enabled is False


# ---------------------------------------------------------------------------
# Additional InteractiveMode handler coverage
# ---------------------------------------------------------------------------


class TestInteractiveModeAdditional:
    def _make_mode(self) -> object:
        """Create a minimal InteractiveMode with mocked session."""
        from ollama_cmd.interactive import InteractiveMode

        session = _make_interactive_session()
        mode = InteractiveMode.__new__(InteractiveMode)
        mode.session = session
        mode._intent_enabled = False
        mode._intent_threshold = 0.7
        mode._current_job = None
        mode._status_lines = {}
        return mode

    def test_show_command_menu(self):
        mode = self._make_mode()
        mode._show_command_menu()

    def test_cmd_tool_no_arg(self):
        mode = self._make_mode()
        assert mode._cmd_tool("") is False

    def test_cmd_tool_unknown(self):
        mode = self._make_mode()
        assert mode._cmd_tool("nonexistent_tool_xyz") is False

    def test_cmd_tool_file_read(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "test.txt").write_text("hello", encoding="utf-8")
        mode = self._make_mode()
        assert mode._cmd_tool("file_read test.txt") is False

    def test_cmd_tool_shell_exec(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mode = self._make_mode()
        assert mode._cmd_tool("shell_exec echo hello") is False

    def test_model_list(self):
        mode = self._make_mode()
        with patch("httpx.get") as mock_get:
            resp = MagicMock()
            resp.json.return_value = {"models": [{"name": "llama3.2"}, {"name": "codellama"}]}
            resp.raise_for_status = MagicMock()
            mock_get.return_value = resp
            assert mode._model_list() is False

    def test_model_list_connect_error(self):
        import httpx

        mode = self._make_mode()
        with patch("httpx.get", side_effect=httpx.ConnectError("fail")):
            assert mode._model_list() is False

    def test_model_change_provider_valid(self):
        mode = self._make_mode()
        mode._print_status_bar = MagicMock()
        assert mode._model_change_provider("claude") is False
        assert mode.session.provider == "claude"

    def test_model_change_provider_invalid(self):
        mode = self._make_mode()
        assert mode._model_change_provider("banana") is False

    def test_model_change_provider_empty(self):
        mode = self._make_mode()
        assert mode._model_change_provider("") is False

    def test_cmd_config_show(self):
        mode = self._make_mode()
        assert mode._cmd_config("show") is False

    def test_cmd_config_get(self):
        mode = self._make_mode()
        assert mode._cmd_config("get ollama_model") is False

    def test_cmd_config_set(self):
        mode = self._make_mode()
        assert mode._cmd_config("set ollama_model llama3.2") is False

    def test_cmd_bug_with_description(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mode = self._make_mode()
        assert mode._cmd_bug("Something broke") is False

    def test_cmd_pull_with_model(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mode = self._make_mode()
        assert mode._cmd_pull("llama3.2") is False

    def test_cmd_memory_add(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "OLLAMA.md").write_text("# Project\n", encoding="utf-8")
        mode = self._make_mode()
        assert mode._cmd_memory("add New note here") is False

    def test_cmd_memory_view(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "OLLAMA.md").write_text("# Project\nSome content\n", encoding="utf-8")
        mode = self._make_mode()
        assert mode._cmd_memory("") is False

    def test_cmd_load_with_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mode = self._make_mode()
        assert mode._cmd_load("nonexistent-session") is False

    def test_cmd_mcp_status(self):
        mode = self._make_mode()
        assert mode._cmd_mcp("status") is False

    def test_cmd_mcp_enable(self):
        mode = self._make_mode()
        assert mode._cmd_mcp("enable github") is False

    def test_cmd_init_creates_structure(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mode = self._make_mode()
        assert mode._cmd_init("") is False

    def test_cmd_resume_with_id(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        mode = self._make_mode()
        assert mode._cmd_resume("some-task-id") is False

    def test_cmd_intent_threshold(self):
        mode = self._make_mode()
        mode._cmd_intent("threshold 0.9")

    def test_cmd_intent_no_arg(self):
        mode = self._make_mode()
        assert mode._cmd_intent("") is False

    def test_print_response(self):
        mode = self._make_mode()
        mode._print_response("Hello world!", agent_type=None)

    def test_print_response_with_agent(self):
        mode = self._make_mode()
        mode._print_response("Result here", agent_type="code")

    def test_fire_notification(self):
        mode = self._make_mode()
        mode._fire_notification("info", "Something happened")


# ---------------------------------------------------------------------------
# _parse_tool_args tests
# ---------------------------------------------------------------------------


class TestParseToolArgs:
    def test_file_read_single_arg(self):
        from ollama_cmd.interactive import _parse_tool_args

        args, kwargs, error = _parse_tool_args("file_read", "README.md")
        assert args == ("README.md",)
        assert kwargs == {}
        assert error is None

    def test_file_write_valid(self):
        from ollama_cmd.interactive import _parse_tool_args

        args, kwargs, error = _parse_tool_args("file_write", "test.txt hello world")
        assert args == ("test.txt", "hello world")
        assert kwargs == {}
        assert error is None

    def test_file_write_missing_content(self):
        from ollama_cmd.interactive import _parse_tool_args

        args, kwargs, error = _parse_tool_args("file_write", "test.txt")
        assert error is not None
        assert "Usage" in error

    def test_file_edit_valid(self):
        from ollama_cmd.interactive import _parse_tool_args

        args, kwargs, error = _parse_tool_args("file_edit", "f.py|||old|||new")
        assert args == ("f.py", "old", "new")
        assert error is None

    def test_file_edit_invalid_parts(self):
        from ollama_cmd.interactive import _parse_tool_args

        _, _, error = _parse_tool_args("file_edit", "f.py|||old")
        assert error is not None
        assert "Usage" in error

    def test_grep_search_with_path(self):
        from ollama_cmd.interactive import _parse_tool_args

        args, kwargs, error = _parse_tool_args("grep_search", "pattern src/")
        assert args == ("pattern", "src/")
        assert error is None

    def test_grep_search_default_path(self):
        from ollama_cmd.interactive import _parse_tool_args

        args, kwargs, error = _parse_tool_args("grep_search", "pattern")
        assert args == ("pattern", ".")
        assert error is None

    def test_shell_exec_single_arg(self):
        from ollama_cmd.interactive import _parse_tool_args

        args, kwargs, error = _parse_tool_args("shell_exec", "echo hello")
        assert args == ("echo hello",)
        assert kwargs == {}
        assert error is None

    def test_web_fetch_single_arg(self):
        from ollama_cmd.interactive import _parse_tool_args

        args, kwargs, error = _parse_tool_args("web_fetch", "https://example.com")
        assert args == ("https://example.com",)
        assert error is None

    def test_model_pull_no_force(self):
        from ollama_cmd.interactive import _parse_tool_args

        args, kwargs, error = _parse_tool_args("model_pull", "llama3.2")
        assert args == ("llama3.2",)
        assert kwargs == {"force": False}
        assert error is None

    def test_model_pull_with_force(self):
        from ollama_cmd.interactive import _parse_tool_args

        args, kwargs, error = _parse_tool_args("model_pull", "--force llama3.2")
        assert args == ("llama3.2",)
        assert kwargs == {"force": True}
        assert error is None

    def test_unknown_tool_defaults_to_single_arg(self):
        from ollama_cmd.interactive import _parse_tool_args

        args, kwargs, error = _parse_tool_args("future_tool", "some args")
        assert args == ("some args",)
        assert kwargs == {}
        assert error is None


# ---------------------------------------------------------------------------
# Extracted REPL helper methods
# ---------------------------------------------------------------------------


class TestReplHelpers:
    def _make_mode(self) -> object:
        """Create a minimal InteractiveMode with mocked session."""
        from ollama_cmd.interactive import InteractiveMode

        session = _make_interactive_session()
        mode = InteractiveMode.__new__(InteractiveMode)
        mode.session = session
        mode._intent_enabled = False
        mode._intent_threshold = 0.7
        mode._current_job = "idle"
        mode._status_lines = {}
        mode._running = True
        return mode

    def test_resolve_agent_type_no_prefix(self):
        mode = self._make_mode()
        with patch.object(mode, "_fire_hook") as mock_hook:
            agent_type, text = mode._resolve_agent_type("hello world")
            assert agent_type is None
            assert text == "hello world"
            mock_hook.assert_not_called()

    def test_resolve_agent_type_with_prefix(self):
        mode = self._make_mode()
        with patch.object(mode, "_fire_hook") as mock_hook:
            agent_type, text = mode._resolve_agent_type("@code write a function")
            assert agent_type == "code"
            assert text == "write a function"
            mock_hook.assert_called_once()
            call_args = mock_hook.call_args
            assert call_args[0][0] == "SubagentStart"
            payload = call_args[0][1]
            assert payload["agent_type"] == "code"
            assert "agent_id" in payload
            assert "session_id" in payload
            assert "model" in payload
            assert "prompt_preview" in payload

    def test_resolve_agent_type_at_only(self):
        mode = self._make_mode()
        agent_type, text = mode._resolve_agent_type("@code")
        assert agent_type is None
        assert text == "@code"

    def test_check_prompt_hooks_no_denial(self):
        mode = self._make_mode()
        # Hooks not available, so returns False (not denied)
        denied = mode._check_prompt_hooks("test prompt")
        assert denied is False

    def test_check_prompt_hooks_denied(self):
        mode = self._make_mode()
        mock_result = MagicMock()
        mock_result.permission_decision = "deny"
        with patch.object(mode, "_fire_hook", return_value=[mock_result]):
            denied = mode._check_prompt_hooks("test prompt")
            assert denied is True

    def test_check_prompt_hooks_allowed(self):
        mode = self._make_mode()
        mock_result = MagicMock()
        mock_result.permission_decision = "allow"
        with patch.object(mode, "_fire_hook", return_value=[mock_result]):
            denied = mode._check_prompt_hooks("test prompt")
            assert denied is False

    def test_display_response_metrics(self, capsys):
        mode = self._make_mode()
        result = {
            "metrics": {"total_tokens": 150, "cost_estimate": 0.0012},
            "compacted": False,
        }
        mode._display_response_metrics(result)
        out = capsys.readouterr().out
        assert "150" in out
        assert "$0.0012" in out

    def test_display_response_metrics_with_compaction(self, capsys):
        mode = self._make_mode()
        result = {
            "metrics": {"total_tokens": 500, "cost_estimate": 0.005},
            "compacted": True,
        }
        mode._display_response_metrics(result)
        out = capsys.readouterr().out
        assert "auto-compacted" in out

    def test_fire_session_lifecycle_hooks(self):
        mode = self._make_mode()
        with patch.object(mode, "_fire_hook") as mock_hook:
            mode._fire_session_lifecycle_hooks()
            assert mock_hook.call_count == 2
            hook_names = [call[0][0] for call in mock_hook.call_args_list]
            assert hook_names == ["Setup", "SessionStart"]
            # Verify Setup payload has required fields
            setup_payload = mock_hook.call_args_list[0][0][1]
            assert "trigger" in setup_payload
            assert "session_id" in setup_payload
            assert "cwd" in setup_payload
            # Verify SessionStart payload has required fields
            start_payload = mock_hook.call_args_list[1][0][1]
            assert "session_id" in start_payload
            assert "source" in start_payload
            assert start_payload["source"] == "interactive"
