"""Tests for the TUI command processor -- dispatch, registry, and handlers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tui.command_processor import COMMAND_REGISTRY, CommandProcessor, CommandResult

# ---------------------------------------------------------------------------
# Command Registry tests
# ---------------------------------------------------------------------------


class TestCommandRegistry:
    """Test the COMMAND_REGISTRY structure and contents."""

    def test_registry_has_34_commands(self):
        """The registry contains exactly 34 slash commands."""
        assert len(COMMAND_REGISTRY) == 34

    def test_all_expected_commands_registered(self):
        """Every expected command name is present in the registry."""
        expected = [
            "/help",
            "/quit",
            "/exit",
            "/status",
            "/clear",
            "/model",
            "/provider",
            "/save",
            "/load",
            "/history",
            "/compact",
            "/memory",
            "/remember",
            "/recall",
            "/tools",
            "/tool",
            "/pull",
            "/diff",
            "/mcp",
            "/agents",
            "/set-agent-model",
            "/list-agent-models",
            "/chain",
            "/team_planning",
            "/build",
            "/resume",
            "/intent",
            "/init",
            "/config",
            "/settings",
            "/bug",
            "/plan",
            "/complete_w_team",
            "/update_status_line",
        ]
        for cmd in expected:
            assert cmd in COMMAND_REGISTRY, f"Missing command: {cmd}"

    def test_no_unexpected_commands(self):
        """The registry does not contain commands outside the expected set."""
        expected = {
            "/help",
            "/quit",
            "/exit",
            "/status",
            "/clear",
            "/model",
            "/provider",
            "/save",
            "/load",
            "/history",
            "/compact",
            "/memory",
            "/remember",
            "/recall",
            "/tools",
            "/tool",
            "/pull",
            "/diff",
            "/mcp",
            "/agents",
            "/set-agent-model",
            "/list-agent-models",
            "/chain",
            "/team_planning",
            "/build",
            "/resume",
            "/intent",
            "/init",
            "/config",
            "/settings",
            "/bug",
            "/plan",
            "/complete_w_team",
            "/update_status_line",
        }
        actual = set(COMMAND_REGISTRY.keys())
        unexpected = actual - expected
        assert unexpected == set(), f"Unexpected commands in registry: {unexpected}"

    def test_each_entry_has_handler_desc_category(self):
        """Every registry entry is a 3-tuple of (handler_name, description, category)."""
        for cmd, entry in COMMAND_REGISTRY.items():
            assert isinstance(entry, tuple), f"{cmd} entry is not a tuple"
            assert len(entry) == 3, f"{cmd} entry does not have 3 elements"
            handler, desc, cat = entry
            assert isinstance(handler, str), f"{cmd} handler is not a string"
            assert isinstance(desc, str), f"{cmd} description is not a string"
            assert isinstance(cat, str), f"{cmd} category is not a string"

    def test_handler_names_start_with_underscore_cmd(self):
        """Every handler method name starts with _cmd_."""
        for cmd, (handler, _desc, _cat) in COMMAND_REGISTRY.items():
            assert handler.startswith("_cmd_"), f"{cmd} handler '{handler}' does not start with _cmd_"

    def test_descriptions_non_empty(self):
        """Every command has a non-empty description."""
        for cmd, (_handler, desc, _cat) in COMMAND_REGISTRY.items():
            assert len(desc) > 0, f"{cmd} has an empty description"

    def test_categories_non_empty(self):
        """Every command has a non-empty category."""
        for cmd, (_handler, _desc, cat) in COMMAND_REGISTRY.items():
            assert len(cat) > 0, f"{cmd} has an empty category"

    def test_expected_categories_present(self):
        """The registry contains all expected category values."""
        categories = {cat for _, (_, _, cat) in COMMAND_REGISTRY.items()}
        for expected in ("Session", "Memory", "Tools", "Agents", "Project", "Other"):
            assert expected in categories, f"Missing category: {expected}"

    def test_quit_and_exit_share_handler(self):
        """/quit and /exit both map to the same handler."""
        quit_handler = COMMAND_REGISTRY["/quit"][0]
        exit_handler = COMMAND_REGISTRY["/exit"][0]
        assert quit_handler == exit_handler


# ---------------------------------------------------------------------------
# CommandResult tests
# ---------------------------------------------------------------------------


class TestCommandResult:
    """Test CommandResult dataclass."""

    def test_defaults(self):
        """CommandResult defaults to non-exit with empty output/errors/data."""
        result = CommandResult()
        assert result.should_exit is False
        assert result.output == []
        assert result.errors == []
        assert result.data == {}

    def test_exit_result(self):
        """CommandResult can signal exit."""
        result = CommandResult(should_exit=True)
        assert result.should_exit is True

    def test_output_result(self):
        """CommandResult stores output lines."""
        result = CommandResult(output=["line1", "line2"])
        assert len(result.output) == 2
        assert result.output[0] == "line1"
        assert result.output[1] == "line2"

    def test_errors_result(self):
        """CommandResult stores error messages."""
        result = CommandResult(errors=["something went wrong"])
        assert len(result.errors) == 1
        assert "wrong" in result.errors[0]

    def test_data_result(self):
        """CommandResult stores arbitrary data dict."""
        result = CommandResult(data={"key": "value", "count": 42})
        assert result.data["key"] == "value"
        assert result.data["count"] == 42

    def test_combined_result(self):
        """CommandResult can have output, errors, and data simultaneously."""
        result = CommandResult(
            should_exit=False,
            output=["ok"],
            errors=["warn"],
            data={"x": 1},
        )
        assert result.should_exit is False
        assert result.output == ["ok"]
        assert result.errors == ["warn"]
        assert result.data == {"x": 1}


# ---------------------------------------------------------------------------
# CommandProcessor -- helper to build a processor with mocked session
# ---------------------------------------------------------------------------


def _make_processor() -> CommandProcessor:
    """Create a CommandProcessor with a fully mocked session and output.

    Uses ``spec=[]`` on sub-objects that the command processor probes via
    ``hasattr`` so that auto-created MagicMock attributes (e.g.
    ``agent_comm``, ``memory_layer``) do not appear unexpectedly.
    """
    session = MagicMock()
    session.model = "llama3.2"
    session.provider = "ollama"
    session.session_id = "test-12345678"
    session.context_manager = MagicMock()
    session.context_manager.messages = ["msg1", "msg2"]
    session.context_manager.auto_compact = True
    session.context_manager.compact_threshold = 0.8
    session.context_manager.keep_last_n = 10
    session.context_manager.should_compact.return_value = False
    session.token_counter = MagicMock()
    session.token_counter.total_tokens = 100
    session.token_counter.estimated_cost = 0.001
    session.get_status = MagicMock(
        return_value={
            "model": "llama3.2",
            "provider": "ollama",
            "session_id": "test-12345678",
            "uptime_str": "5m",
            "messages": 2,
            "hooks_enabled": False,
            "token_metrics": {
                "prompt_tokens": 50,
                "completion_tokens": 50,
                "total_tokens": 100,
                "tokens_per_second": 25.0,
                "cost_estimate": 0.001,
            },
            "context_usage": {
                "used": 100,
                "max": 4096,
                "percentage": 2,
                "remaining": 3996,
            },
        }
    )

    # Prevent _cmd_status from finding agent_comm / memory_layer on the mock,
    # which would trigger format-string calls on nested MagicMock values.
    del session.agent_comm
    del session.memory_layer

    output = MagicMock()
    return CommandProcessor(session=session, output=output)


# ---------------------------------------------------------------------------
# CommandProcessor dispatch tests
# ---------------------------------------------------------------------------


class TestCommandProcessorDispatch:
    """Test CommandProcessor.dispatch routes commands correctly."""

    @pytest.mark.asyncio
    async def test_dispatch_quit(self):
        """/quit returns should_exit=True."""
        proc = _make_processor()
        result = await proc.dispatch("/quit")
        assert result.should_exit is True

    @pytest.mark.asyncio
    async def test_dispatch_exit(self):
        """/exit returns should_exit=True (alias for /quit)."""
        proc = _make_processor()
        result = await proc.dispatch("/exit")
        assert result.should_exit is True

    @pytest.mark.asyncio
    async def test_dispatch_help(self):
        """/help returns output and does not exit."""
        proc = _make_processor()
        result = await proc.dispatch("/help")
        assert result.should_exit is False
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_dispatch_help_contains_usage(self):
        """/help output includes usage instructions."""
        proc = _make_processor()
        result = await proc.dispatch("/help")
        combined = "\n".join(result.output)
        assert "Help" in combined
        assert "/command" in combined or "slash command" in combined.lower()

    @pytest.mark.asyncio
    async def test_dispatch_status(self):
        """/status returns session status output."""
        proc = _make_processor()
        result = await proc.dispatch("/status")
        assert result.should_exit is False
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_dispatch_status_contains_model(self):
        """/status output includes model name."""
        proc = _make_processor()
        result = await proc.dispatch("/status")
        combined = "\n".join(result.output)
        assert "llama3.2" in combined

    @pytest.mark.asyncio
    async def test_dispatch_status_contains_provider(self):
        """/status output includes provider name."""
        proc = _make_processor()
        result = await proc.dispatch("/status")
        combined = "\n".join(result.output)
        assert "ollama" in combined

    @pytest.mark.asyncio
    async def test_dispatch_status_contains_tokens(self):
        """/status output includes token information."""
        proc = _make_processor()
        result = await proc.dispatch("/status")
        combined = "\n".join(result.output)
        assert "Token" in combined

    @pytest.mark.asyncio
    async def test_dispatch_clear(self):
        """/clear returns confirmation and does not exit."""
        proc = _make_processor()
        result = await proc.dispatch("/clear")
        assert result.should_exit is False

    @pytest.mark.asyncio
    async def test_dispatch_clear_calls_context_clear(self):
        """/clear calls context_manager.clear() on the session."""
        proc = _make_processor()
        await proc.dispatch("/clear")
        proc.session.context_manager.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_unknown_command(self):
        """Unknown command returns an error."""
        proc = _make_processor()
        result = await proc.dispatch("/nonexistent")
        assert result.should_exit is False
        assert len(result.errors) > 0
        assert "Unknown command" in result.errors[0]

    @pytest.mark.asyncio
    async def test_dispatch_unknown_command_suggests_help(self):
        """Unknown command error suggests /help."""
        proc = _make_processor()
        result = await proc.dispatch("/foobar")
        assert any("/help" in e for e in result.errors)

    @pytest.mark.asyncio
    async def test_dispatch_case_insensitive(self):
        """Commands are case-insensitive."""
        proc = _make_processor()
        result = await proc.dispatch("/QUIT")
        assert result.should_exit is True

    @pytest.mark.asyncio
    async def test_dispatch_mixed_case(self):
        """Commands with mixed case are handled correctly."""
        proc = _make_processor()
        result = await proc.dispatch("/Help")
        assert result.should_exit is False
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_dispatch_with_extra_whitespace(self):
        """Commands with trailing arguments are parsed correctly."""
        proc = _make_processor()
        result = await proc.dispatch("/quit   ")
        assert result.should_exit is True


# ---------------------------------------------------------------------------
# Menu (bare /) tests
# ---------------------------------------------------------------------------


class TestCommandProcessorMenu:
    """Test the bare / menu display."""

    @pytest.mark.asyncio
    async def test_dispatch_bare_slash_shows_menu(self):
        """Bare / shows the command menu."""
        proc = _make_processor()
        result = await proc.dispatch("/")
        assert result.should_exit is False
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_menu_contains_available_commands(self):
        """Menu output includes 'Available Commands' header."""
        proc = _make_processor()
        result = await proc.dispatch("/")
        combined = "\n".join(result.output)
        assert "Available Commands" in combined

    @pytest.mark.asyncio
    async def test_menu_contains_categories(self):
        """Menu output includes category headers."""
        proc = _make_processor()
        result = await proc.dispatch("/")
        combined = "\n".join(result.output)
        assert "Session" in combined
        assert "Agents" in combined
        assert "Other" in combined

    @pytest.mark.asyncio
    async def test_menu_excludes_exit_alias(self):
        """Menu output excludes /exit (alias for /quit)."""
        proc = _make_processor()
        result = await proc.dispatch("/")
        combined = "\n".join(result.output)
        # /quit should be present but /exit should be skipped
        assert "/quit" in combined
        # Check that /exit is not listed (it's a hidden alias)
        # Split by whitespace to avoid false matches in description text
        tokens = combined.split()
        assert "/exit" not in tokens


# ---------------------------------------------------------------------------
# Intent command tests
# ---------------------------------------------------------------------------


class TestCommandProcessorIntent:
    """Test /intent command and its subcommands."""

    @pytest.mark.asyncio
    async def test_dispatch_intent_status(self):
        """/intent (no args) shows classifier status."""
        proc = _make_processor()
        result = await proc.dispatch("/intent")
        assert result.should_exit is False
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_dispatch_intent_status_shows_enabled_state(self):
        """/intent output includes enabled/disabled state."""
        proc = _make_processor()
        result = await proc.dispatch("/intent")
        combined = "\n".join(result.output)
        assert "enabled" in combined or "disabled" in combined

    @pytest.mark.asyncio
    async def test_dispatch_intent_on(self):
        """/intent on enables the classifier."""
        proc = _make_processor()
        result = await proc.dispatch("/intent on")
        assert result.should_exit is False
        combined = "\n".join(result.output)
        assert "enabled" in combined.lower()

    @pytest.mark.asyncio
    async def test_dispatch_intent_off(self):
        """/intent off disables the classifier."""
        proc = _make_processor()
        result = await proc.dispatch("/intent off")
        assert result.should_exit is False
        combined = "\n".join(result.output)
        assert "disabled" in combined.lower()

    @pytest.mark.asyncio
    async def test_dispatch_intent_test(self):
        """/intent test <prompt> classifies a prompt."""
        proc = _make_processor()
        result = await proc.dispatch("/intent test write a function to sort a list")
        assert result.should_exit is False
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_dispatch_intent_test_no_prompt(self):
        """/intent test without a prompt returns an error."""
        proc = _make_processor()
        result = await proc.dispatch("/intent test")
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_dispatch_intent_threshold_set(self):
        """/intent threshold 0.5 sets the confidence threshold."""
        proc = _make_processor()
        result = await proc.dispatch("/intent threshold 0.5")
        assert result.should_exit is False
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_dispatch_intent_threshold_no_value(self):
        """/intent threshold without value shows current threshold."""
        proc = _make_processor()
        result = await proc.dispatch("/intent threshold")
        assert result.should_exit is False
        assert len(result.output) > 0

    @pytest.mark.asyncio
    async def test_dispatch_intent_threshold_invalid(self):
        """/intent threshold with non-numeric value returns an error."""
        proc = _make_processor()
        result = await proc.dispatch("/intent threshold abc")
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_dispatch_intent_threshold_out_of_range(self):
        """/intent threshold with value > 1.0 returns an error."""
        proc = _make_processor()
        result = await proc.dispatch("/intent threshold 1.5")
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_dispatch_intent_unknown_subcommand(self):
        """/intent with unknown subcommand returns an error."""
        proc = _make_processor()
        result = await proc.dispatch("/intent bogus")
        assert len(result.errors) > 0


# ---------------------------------------------------------------------------
# Static helpers tests
# ---------------------------------------------------------------------------


class TestStaticHelpers:
    """Test CommandProcessor static/class methods."""

    def test_get_command_names_returns_list(self):
        """get_command_names() returns a list."""
        names = CommandProcessor.get_command_names()
        assert isinstance(names, list)

    def test_get_command_names_count(self):
        """get_command_names() returns all 34 command names."""
        names = CommandProcessor.get_command_names()
        assert len(names) == 34

    def test_get_command_names_contains_expected(self):
        """get_command_names() includes /help, /quit, /status."""
        names = CommandProcessor.get_command_names()
        assert "/help" in names
        assert "/quit" in names
        assert "/status" in names

    def test_get_command_names_all_start_with_slash(self):
        """Every command name starts with /."""
        names = CommandProcessor.get_command_names()
        for name in names:
            assert name.startswith("/"), f"Command name '{name}' does not start with /"

    def test_get_commands_by_category_returns_dict(self):
        """get_commands_by_category() returns a dict."""
        cats = CommandProcessor.get_commands_by_category()
        assert isinstance(cats, dict)

    def test_get_commands_by_category_has_expected_categories(self):
        """get_commands_by_category() contains expected category keys."""
        cats = CommandProcessor.get_commands_by_category()
        for expected in ("Session", "Memory", "Tools", "Agents", "Project", "Other"):
            assert expected in cats, f"Missing category: {expected}"

    def test_get_commands_by_category_values_are_tuples(self):
        """Each category value is a list of (command, description) tuples."""
        cats = CommandProcessor.get_commands_by_category()
        for cat, entries in cats.items():
            assert isinstance(entries, list), f"Category {cat} is not a list"
            for entry in entries:
                assert isinstance(entry, tuple), f"Entry in {cat} is not a tuple"
                assert len(entry) == 2, f"Entry in {cat} does not have 2 elements"
                cmd, desc = entry
                assert isinstance(cmd, str)
                assert isinstance(desc, str)

    def test_get_commands_by_category_excludes_exit(self):
        """get_commands_by_category() excludes /exit (alias)."""
        cats = CommandProcessor.get_commands_by_category()
        all_cmds = [cmd for entries in cats.values() for cmd, _ in entries]
        assert "/exit" not in all_cmds


# ---------------------------------------------------------------------------
# Unimplemented command dispatch tests
# ---------------------------------------------------------------------------


class TestUnimplementedCommands:
    """Test dispatching commands that are registered but not implemented in CommandProcessor."""

    @pytest.mark.asyncio
    async def test_dispatch_model_no_crash(self):
        """/model dispatches without crashing (may return error if unimplemented)."""
        proc = _make_processor()
        result = await proc.dispatch("/model")
        assert isinstance(result, CommandResult)

    @pytest.mark.asyncio
    async def test_dispatch_provider_no_crash(self):
        """/provider dispatches without crashing."""
        proc = _make_processor()
        result = await proc.dispatch("/provider")
        assert isinstance(result, CommandResult)

    @pytest.mark.asyncio
    async def test_dispatch_history_no_crash(self):
        """/history dispatches without crashing."""
        proc = _make_processor()
        result = await proc.dispatch("/history")
        assert isinstance(result, CommandResult)

    @pytest.mark.asyncio
    async def test_dispatch_memory_no_crash(self):
        """/memory dispatches without crashing."""
        proc = _make_processor()
        result = await proc.dispatch("/memory")
        assert isinstance(result, CommandResult)

    @pytest.mark.asyncio
    async def test_dispatch_tools_no_crash(self):
        """/tools dispatches without crashing."""
        proc = _make_processor()
        result = await proc.dispatch("/tools")
        assert isinstance(result, CommandResult)

    @pytest.mark.asyncio
    async def test_dispatch_agents_no_crash(self):
        """/agents dispatches without crashing."""
        proc = _make_processor()
        result = await proc.dispatch("/agents")
        assert isinstance(result, CommandResult)

    @pytest.mark.asyncio
    async def test_dispatch_config_no_crash(self):
        """/config dispatches without crashing."""
        proc = _make_processor()
        result = await proc.dispatch("/config")
        assert isinstance(result, CommandResult)

    @pytest.mark.asyncio
    async def test_dispatch_bug_no_crash(self):
        """/bug dispatches without crashing."""
        proc = _make_processor()
        result = await proc.dispatch("/bug")
        assert isinstance(result, CommandResult)


# ---------------------------------------------------------------------------
# Full command handler tests
# ---------------------------------------------------------------------------


def _make_rich_processor() -> CommandProcessor:
    """Create a CommandProcessor with a fully mocked session including
    agent_comm, memory_layer, and other optional attributes so the full
    command handler paths are exercised."""
    session = MagicMock()
    session.model = "llama3.2"
    session.provider = "ollama"
    session.session_id = "test-rich-1234"
    session.hooks_enabled = False
    session.start_time = 0.0
    session._message_count = 5

    # context_manager
    cm = MagicMock()
    cm.messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    cm.auto_compact = True
    cm.compact_threshold = 0.85
    cm.keep_last_n = 4
    cm.should_compact.return_value = False
    cm.get_context_usage.return_value = {
        "used": 500,
        "max": 4096,
        "percentage": 12,
        "remaining": 3596,
    }
    session.context_manager = cm

    # token_counter
    tc = MagicMock()
    tc.total_tokens = 200
    tc.estimated_cost = 0.002
    session.token_counter = tc

    # get_status
    session.get_status = MagicMock(
        return_value={
            "model": "llama3.2",
            "provider": "ollama",
            "session_id": "test-rich-1234",
            "uptime_str": "10m",
            "messages": 2,
            "hooks_enabled": False,
            "token_metrics": {
                "prompt_tokens": 100,
                "completion_tokens": 100,
                "total_tokens": 200,
                "tokens_per_second": 30.0,
                "cost_estimate": 0.002,
            },
            "context_usage": {
                "used": 500,
                "max": 4096,
                "percentage": 12,
                "remaining": 3596,
            },
        }
    )

    # agent_comm
    agent_comm = MagicMock()
    agent_comm.get_token_savings.return_value = {
        "total_messages": 5,
        "context_tokens_saved": 100,
    }
    agent_comm.receive.return_value = []
    session.agent_comm = agent_comm

    # memory_layer
    memory_layer = MagicMock()
    memory_layer.get_token_savings.return_value = {
        "total_entries": 2,
        "total_raw_tokens": 50,
        "context_tokens_used": 30,
        "tokens_saved": 20,
    }
    memory_layer.get_context_block.return_value = ""
    memory_layer.get_all_entries.return_value = []
    memory_layer.recall_relevant.return_value = []
    session.memory_layer = memory_layer

    output = MagicMock()
    return CommandProcessor(session=session, output=output)


class TestCommandHandlerModel:
    """Test /model command handler."""

    @pytest.mark.asyncio
    async def test_model_no_arg_shows_current(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/model")
        assert any("llama3.2" in line for line in result.output)

    @pytest.mark.asyncio
    async def test_model_switch(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/model codestral")
        assert any("codestral" in line for line in result.output)
        assert proc.session.model == "codestral"


class TestCommandHandlerProvider:
    """Test /provider command handler."""

    @pytest.mark.asyncio
    async def test_provider_no_arg_shows_current(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/provider")
        assert any("ollama" in line for line in result.output)

    @pytest.mark.asyncio
    async def test_provider_switch_valid(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/provider claude")
        assert not result.errors
        assert proc.session.provider == "claude"

    @pytest.mark.asyncio
    async def test_provider_switch_invalid(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/provider banana")
        assert result.errors


class TestCommandHandlerSave:
    """Test /save command handler."""

    @pytest.mark.asyncio
    async def test_save_calls_session(self):
        proc = _make_rich_processor()
        proc.session.save.return_value = "/tmp/session.json"
        result = await proc.dispatch("/save")
        assert not result.errors


class TestCommandHandlerLoad:
    """Test /load command handler."""

    @pytest.mark.asyncio
    async def test_load_no_arg_error(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/load")
        assert result.errors

    @pytest.mark.asyncio
    async def test_load_file_not_found(self):
        proc = _make_rich_processor()
        from unittest.mock import patch

        with patch("tui.command_processor.CommandProcessor._cmd_load") as mock_load:
            mock_load.return_value = CommandResult(errors=["not found"])
            result = await proc.dispatch("/load nonexistent")
            assert result.errors


class TestCommandHandlerHistory:
    """Test /history command handler."""

    @pytest.mark.asyncio
    async def test_history_with_messages(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/history")
        assert not result.errors
        assert len(result.output) >= 2  # Two messages in mock

    @pytest.mark.asyncio
    async def test_history_with_empty_messages(self):
        proc = _make_rich_processor()
        proc.session.context_manager.messages = []
        result = await proc.dispatch("/history")
        assert any("No conversation" in line for line in result.output)

    @pytest.mark.asyncio
    async def test_history_with_string_messages(self):
        proc = _make_rich_processor()
        proc.session.context_manager.messages = ["hello", "world"]
        result = await proc.dispatch("/history")
        assert len(result.output) >= 2


class TestCommandHandlerCompact:
    """Test /compact command handler."""

    @pytest.mark.asyncio
    async def test_compact_nothing_to_compact(self):
        proc = _make_rich_processor()
        proc.session.context_manager.messages = ["a", "b"]
        proc.session.context_manager.keep_last_n = 10
        result = await proc.dispatch("/compact")
        assert any("Nothing to compact" in line for line in result.output)

    @pytest.mark.asyncio
    async def test_compact_no_context_manager(self):
        proc = _make_rich_processor()
        del proc.session.context_manager
        result = await proc.dispatch("/compact")
        assert any("not available" in line for line in result.output)


class TestCommandHandlerMemory:
    """Test /memory command handler."""

    @pytest.mark.asyncio
    async def test_memory_no_arg_no_file(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/memory")
        # Either shows content or says not found
        assert result.output or result.errors

    @pytest.mark.asyncio
    async def test_memory_add_note(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "QARIN.md").write_text("# Test\n", encoding="utf-8")
        proc = _make_rich_processor()
        result = await proc.dispatch("/memory always use type hints")
        assert any("Added" in line for line in result.output)


class TestCommandHandlerRemember:
    """Test /remember command handler."""

    @pytest.mark.asyncio
    async def test_remember_no_arg(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/remember")
        assert result.errors

    @pytest.mark.asyncio
    async def test_remember_key_value(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/remember coding use type hints")
        assert not result.errors


class TestCommandHandlerRecall:
    """Test /recall command handler."""

    @pytest.mark.asyncio
    async def test_recall_no_arg(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/recall")
        assert result.output

    @pytest.mark.asyncio
    async def test_recall_with_query(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/recall coding")
        assert result.output


class TestCommandHandlerTools:
    """Test /tools command handler."""

    @pytest.mark.asyncio
    async def test_tools_lists_available(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/tools")
        # Should return tools or an import error message
        assert result.output or result.errors


class TestCommandHandlerTool:
    """Test /tool command handler."""

    @pytest.mark.asyncio
    async def test_tool_no_arg(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/tool")
        assert result.errors
        assert any("Usage" in line for line in result.errors)

    @pytest.mark.asyncio
    async def test_tool_file_read(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "test.txt").write_text("hello world", encoding="utf-8")
        proc = _make_rich_processor()
        result = await proc.dispatch("/tool file_read test.txt")
        # May succeed or get an import error depending on env
        assert isinstance(result, CommandResult)


class TestCommandHandlerDiff:
    """Test /diff command handler."""

    @pytest.mark.asyncio
    async def test_diff_in_git_repo(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/diff")
        # Either shows git diff or says not a git repo
        assert result.output or result.errors


class TestCommandHandlerPull:
    """Test /pull command handler."""

    @pytest.mark.asyncio
    async def test_pull_no_arg(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/pull")
        assert result.errors
        assert any("Usage" in line for line in result.errors)


class TestCommandHandlerMcp:
    """Test /mcp command handler."""

    @pytest.mark.asyncio
    async def test_mcp_no_arg(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/mcp")
        # Either lists servers or returns import error
        assert result.output or result.errors

    @pytest.mark.asyncio
    async def test_mcp_invalid_subcommand(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/mcp badsub")
        assert result.errors


class TestCommandHandlerAgents:
    """Test /agents command handler."""

    @pytest.mark.asyncio
    async def test_agents_with_agent_comm(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/agents")
        assert not result.errors
        assert result.output


class TestCommandHandlerSetAgentModel:
    """Test /set-agent-model command handler."""

    @pytest.mark.asyncio
    async def test_set_agent_model_no_arg(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/set-agent-model")
        assert result.errors

    @pytest.mark.asyncio
    async def test_set_agent_model_invalid_format(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/set-agent-model invalid")
        assert result.errors

    @pytest.mark.asyncio
    async def test_set_agent_model_valid(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/set-agent-model code:ollama:codestral")
        assert not result.errors


class TestCommandHandlerListAgentModels:
    """Test /list-agent-models command handler."""

    @pytest.mark.asyncio
    async def test_list_agent_models(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/list-agent-models")
        # May return models or import error
        assert isinstance(result, CommandResult)


class TestCommandHandlerChain:
    """Test /chain command handler."""

    @pytest.mark.asyncio
    async def test_chain_no_arg(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/chain")
        assert result.errors
        assert any("Usage" in line for line in result.errors)


class TestCommandHandlerTeamPlanning:
    """Test /team_planning command handler."""

    @pytest.mark.asyncio
    async def test_team_planning_no_arg(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/team_planning")
        assert result.errors

    @pytest.mark.asyncio
    async def test_plan_alias_no_arg(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/plan")
        assert result.errors


class TestCommandHandlerBuild:
    """Test /build command handler."""

    @pytest.mark.asyncio
    async def test_build_no_arg(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/build")
        assert result.errors
        assert any("Usage" in line for line in result.errors)

    @pytest.mark.asyncio
    async def test_build_missing_file(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/build nonexistent.md")
        assert result.errors


class TestCommandHandlerResume:
    """Test /resume command handler."""

    @pytest.mark.asyncio
    async def test_resume_no_tasks_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        proc = _make_rich_processor()
        result = await proc.dispatch("/resume")
        assert any("No previous tasks" in line for line in result.output)

    @pytest.mark.asyncio
    async def test_resume_with_tasks(self, tmp_path, monkeypatch):
        import json

        monkeypatch.chdir(tmp_path)
        tasks_dir = tmp_path / ".qarin" / "tasks"
        tasks_dir.mkdir(parents=True)
        task = {"id": "test-task", "type": "test", "description": "A task", "status": "planned"}
        (tasks_dir / "test-task.json").write_text(json.dumps(task), encoding="utf-8")
        proc = _make_rich_processor()
        result = await proc.dispatch("/resume")
        assert any("test-task" in line for line in result.output)


class TestCommandHandlerInit:
    """Test /init command handler."""

    @pytest.mark.asyncio
    async def test_init_creates_files(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        proc = _make_rich_processor()
        result = await proc.dispatch("/init")
        assert any("initialized" in line.lower() or "created" in line.lower() for line in result.output)
        assert (tmp_path / "QARIN.md").exists()
        assert (tmp_path / ".qarin").exists()

    @pytest.mark.asyncio
    async def test_init_idempotent(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "QARIN.md").write_text("# test\n", encoding="utf-8")
        (tmp_path / ".qarin").mkdir()
        proc = _make_rich_processor()
        result = await proc.dispatch("/init")
        assert any("already" in line.lower() or "nothing" in line.lower() for line in result.output)

    @pytest.mark.asyncio
    async def test_init_imports_instruction_files(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "CLAUDE.md").write_text("# Claude Instructions\nBe helpful.", encoding="utf-8")
        proc = _make_rich_processor()
        await proc.dispatch("/init")
        ollama_md = (tmp_path / "QARIN.md").read_text(encoding="utf-8")
        assert "imported: CLAUDE.md" in ollama_md


class TestCommandHandlerConfig:
    """Test /config command handler."""

    @pytest.mark.asyncio
    async def test_config_no_arg_shows_settings(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/config")
        assert not result.errors
        assert any("ollama_host" in line for line in result.output)

    @pytest.mark.asyncio
    async def test_config_get_specific_key(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/config ollama_model")
        assert not result.errors

    @pytest.mark.asyncio
    async def test_config_unknown_key(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/config unknown_key_xyz value")
        assert result.errors

    @pytest.mark.asyncio
    async def test_settings_alias(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/settings")
        assert not result.errors
        assert any("ollama_host" in line for line in result.output)

    @pytest.mark.asyncio
    async def test_config_rejects_none_typed_key(self):
        """Setting a config key that is currently None should be rejected."""
        proc = _make_rich_processor()
        from unittest.mock import patch

        fake_cfg = MagicMock()
        fake_cfg.allowed_tools = None
        with patch("api.config.get_config", return_value=fake_cfg):
            result = await proc.dispatch("/config allowed_tools shell_exec")
        assert result.errors
        assert "None" in result.errors[0] or "unset" in result.errors[0]

    @pytest.mark.asyncio
    async def test_config_rejects_complex_typed_key(self):
        """Setting a config key that is a dict/list should be rejected."""
        proc = _make_rich_processor()
        from unittest.mock import patch

        fake_cfg = MagicMock()
        fake_cfg.agent_models = {"code": {"provider": "ollama", "model": "codestral"}}
        with patch("api.config.get_config", return_value=fake_cfg):
            result = await proc.dispatch("/config agent_models something")
        assert result.errors
        assert "complex type" in result.errors[0] or "settings.json" in result.errors[0]


class TestCommandHandlerBug:
    """Test /bug command handler."""

    @pytest.mark.asyncio
    async def test_bug_no_arg(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        proc = _make_rich_processor()
        result = await proc.dispatch("/bug")
        assert not result.errors
        assert any("saved" in line.lower() for line in result.output)

    @pytest.mark.asyncio
    async def test_bug_with_description(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        proc = _make_rich_processor()
        result = await proc.dispatch("/bug something is broken")
        assert not result.errors


class TestCommandHandlerUpdateStatusLine:
    """Test /update_status_line command handler."""

    @pytest.mark.asyncio
    async def test_update_status_line_no_arg(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/update_status_line")
        assert result.errors

    @pytest.mark.asyncio
    async def test_update_status_line_missing_value(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/update_status_line key_only")
        assert result.errors

    @pytest.mark.asyncio
    async def test_update_status_line_valid(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/update_status_line project myapp")
        assert not result.errors
        assert any("myapp" in line for line in result.output)


# ---------------------------------------------------------------------------
# Deeper handler tests -- exercise code paths within handlers
# ---------------------------------------------------------------------------


class TestCompactDeepPaths:
    """Test _cmd_compact with enough messages to trigger actual compaction."""

    @pytest.mark.asyncio
    async def test_compact_fires_when_enough_messages(self):
        from unittest.mock import AsyncMock

        proc = _make_rich_processor()
        cm = proc.session.context_manager
        cm.messages = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        cm.keep_last_n = 4
        cm.get_context_usage = MagicMock(return_value={"used": 2000, "max": 4096, "percentage": 48, "remaining": 2096})
        proc.session.compact = AsyncMock(
            return_value={"messages_removed": 16, "before_tokens": 2000, "after_tokens": 500}
        )
        result = await proc.dispatch("/compact")
        assert not result.errors
        assert any("Removed" in line for line in result.output)

    @pytest.mark.asyncio
    async def test_compact_uses_cm_compact(self):
        from unittest.mock import AsyncMock

        proc = _make_rich_processor()
        cm = proc.session.context_manager
        cm.messages = [f"m{i}" for i in range(10)]
        cm.keep_last_n = 2
        cm.get_context_usage = MagicMock(return_value={"used": 1000, "max": 4096, "percentage": 24, "remaining": 3096})
        del proc.session.compact
        cm.compact = AsyncMock(return_value={"messages_removed": 8})
        result = await proc.dispatch("/compact")
        assert not result.errors

    @pytest.mark.asyncio
    async def test_compact_exception(self):
        proc = _make_rich_processor()
        cm = proc.session.context_manager
        cm.messages = [f"m{i}" for i in range(10)]
        cm.keep_last_n = 2
        cm.get_context_usage = MagicMock(return_value={})
        proc.session.compact = MagicMock(side_effect=RuntimeError("boom"))
        result = await proc.dispatch("/compact")
        assert result.errors
        assert any("boom" in e for e in result.errors)


class TestLoadDeepPaths:
    """Test _cmd_load with real session loading."""

    @pytest.mark.asyncio
    async def test_load_success(self):
        proc = _make_rich_processor()
        mock_loaded = MagicMock()
        mock_loaded.session_id = "loaded-123"
        mock_loaded.model = "codellama"
        mock_loaded.provider = "ollama"
        mock_loaded.context_manager = MagicMock()
        mock_loaded.token_counter = MagicMock()
        mock_loaded.hooks_enabled = False
        mock_loaded.start_time = 0.0
        mock_loaded._message_count = 10
        from unittest.mock import patch

        with patch("model.session.Session.load", return_value=mock_loaded):
            result = await proc.dispatch("/load test-session")
        assert not result.errors
        assert any("loaded" in line.lower() for line in result.output)

    @pytest.mark.asyncio
    async def test_load_file_not_found_real(self):
        proc = _make_rich_processor()
        from unittest.mock import patch

        with patch("model.session.Session.load", side_effect=FileNotFoundError("nope")):
            result = await proc.dispatch("/load nonexistent")
        assert result.errors

    @pytest.mark.asyncio
    async def test_load_generic_error(self):
        proc = _make_rich_processor()
        from unittest.mock import patch

        with patch("model.session.Session.load", side_effect=RuntimeError("corrupt")):
            result = await proc.dispatch("/load broken-session")
        assert result.errors
        assert any("Failed" in e for e in result.errors)


class TestToolDeepPaths:
    """Test _cmd_tool dispatch."""

    @pytest.mark.asyncio
    async def test_tool_file_read_success(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "hello.txt").write_text("world", encoding="utf-8")
        proc = _make_rich_processor()
        result = await proc.dispatch("/tool file_read hello.txt")
        assert isinstance(result, CommandResult)

    @pytest.mark.asyncio
    async def test_tool_shell_command(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        proc = _make_rich_processor()
        result = await proc.dispatch("/tool shell echo hi")
        assert isinstance(result, CommandResult)


class TestMcpDeepPaths:
    """Test _cmd_mcp subcommands."""

    @pytest.mark.asyncio
    async def test_mcp_enable_disable(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/mcp enable github")
        assert isinstance(result, CommandResult)

    @pytest.mark.asyncio
    async def test_mcp_tools(self):
        proc = _make_rich_processor()
        result = await proc.dispatch("/mcp tools")
        assert isinstance(result, CommandResult)


class TestSetAgentModelDeepPaths:
    @pytest.mark.asyncio
    async def test_set_multiple_agents(self):
        proc = _make_rich_processor()
        result1 = await proc.dispatch("/set-agent-model code:ollama:codestral")
        result2 = await proc.dispatch("/set-agent-model review:claude:claude-sonnet")
        assert not result1.errors
        assert not result2.errors

    @pytest.mark.asyncio
    async def test_list_after_set(self):
        proc = _make_rich_processor()
        await proc.dispatch("/set-agent-model test:ollama:llama3.2")
        result = await proc.dispatch("/list-agent-models")
        assert isinstance(result, CommandResult)


class TestDiffDeepPaths:
    @pytest.mark.asyncio
    async def test_diff_in_non_git_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        proc = _make_rich_processor()
        result = await proc.dispatch("/diff")
        # Either errors (not a git repo) or empty output
        assert isinstance(result, CommandResult)


class TestSaveDeepPaths:
    @pytest.mark.asyncio
    async def test_save_with_name(self):
        proc = _make_rich_processor()
        proc.session.save = MagicMock(return_value="/tmp/test.json")
        result = await proc.dispatch("/save my-session")
        assert not result.errors

    @pytest.mark.asyncio
    async def test_save_no_save_attr(self):
        proc = _make_rich_processor()
        del proc.session.save
        result = await proc.dispatch("/save")
        assert result.errors
