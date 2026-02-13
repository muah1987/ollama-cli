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

    def test_registry_has_31_commands(self):
        """The registry contains exactly 31 slash commands."""
        assert len(COMMAND_REGISTRY) == 31

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
            "/bug",
            "/update_status_line",
        ]
        for cmd in expected:
            assert cmd in COMMAND_REGISTRY, f"Missing command: {cmd}"

    def test_no_unexpected_commands(self):
        """The registry does not contain commands outside the expected set."""
        expected = {
            "/help", "/quit", "/exit", "/status", "/clear", "/model",
            "/provider", "/save", "/load", "/history", "/compact",
            "/memory", "/remember", "/recall", "/tools", "/tool",
            "/pull", "/diff", "/mcp", "/agents", "/set-agent-model",
            "/list-agent-models", "/chain", "/team_planning", "/build",
            "/resume", "/intent", "/init", "/config", "/bug",
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
            assert handler.startswith("_cmd_"), (
                f"{cmd} handler '{handler}' does not start with _cmd_"
            )

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
        """get_command_names() returns all 31 command names."""
        names = CommandProcessor.get_command_names()
        assert len(names) == 31

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
