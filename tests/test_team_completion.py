"""Tests for the team completion loop (runner/team_completion.py)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from runner.team_completion import (
    TEAM_ROLE_TYPES,
    TEAM_ROLES,
    PhaseResult,
    TeamCompletionLoop,
    TeamCompletionResult,
    build_command_knowledge,
    extract_command_requests,
)

# ---------------------------------------------------------------------------
# build_command_knowledge
# ---------------------------------------------------------------------------


class TestBuildCommandKnowledge:
    """Tests for the command knowledge block builder."""

    def test_returns_string(self) -> None:
        text = build_command_knowledge()
        assert isinstance(text, str)

    def test_contains_commands(self) -> None:
        text = build_command_knowledge()
        assert "/status" in text
        assert "/model" in text
        assert "/pull" in text
        assert "/chain" in text

    def test_excludes_blocked_commands(self) -> None:
        text = build_command_knowledge()
        # /quit and /exit should not appear as available
        lines = text.splitlines()
        cmd_lines = [ln for ln in lines if ln.strip().startswith("/quit") or ln.strip().startswith("/exit")]
        assert len(cmd_lines) == 0

    def test_includes_usage_instructions(self) -> None:
        text = build_command_knowledge()
        assert "[CMD:" in text
        assert "orchestrator" in text.lower() or "execute" in text.lower()

    def test_includes_complete_w_team(self) -> None:
        text = build_command_knowledge()
        assert "/complete_w_team" in text


# ---------------------------------------------------------------------------
# extract_command_requests
# ---------------------------------------------------------------------------


class TestExtractCommandRequests:
    """Tests for extracting [CMD: ...] directives from agent output."""

    def test_single_command(self) -> None:
        text = "Let me check status: [CMD: /status]"
        assert extract_command_requests(text) == ["/status"]

    def test_command_with_args(self) -> None:
        text = "I need this model: [CMD: /pull llama3.2]"
        assert extract_command_requests(text) == ["/pull llama3.2"]

    def test_multiple_commands(self) -> None:
        text = "First [CMD: /status] then [CMD: /memory]"
        result = extract_command_requests(text)
        assert "/status" in result
        assert "/memory" in result
        assert len(result) == 2

    def test_no_commands(self) -> None:
        assert extract_command_requests("No commands here") == []

    def test_blocked_commands_filtered(self) -> None:
        text = "[CMD: /quit] and [CMD: /status]"
        result = extract_command_requests(text)
        assert "/status" in result
        assert len(result) == 1

    def test_exit_blocked(self) -> None:
        text = "[CMD: /exit]"
        assert extract_command_requests(text) == []

    def test_clear_blocked(self) -> None:
        text = "[CMD: /clear]"
        assert extract_command_requests(text) == []

    def test_empty_string(self) -> None:
        assert extract_command_requests("") == []

    def test_malformed_directive(self) -> None:
        text = "[CMD: incomplete"
        assert extract_command_requests(text) == []


# ---------------------------------------------------------------------------
# TEAM_ROLES / TEAM_ROLE_TYPES
# ---------------------------------------------------------------------------


class TestTeamRoles:
    """Verify that team role definitions are consistent."""

    def test_all_roles_have_types(self) -> None:
        for role in TEAM_ROLES:
            assert role in TEAM_ROLE_TYPES, f"Role {role!r} missing from TEAM_ROLE_TYPES"

    def test_all_roles_have_contracts(self) -> None:
        for role in TEAM_ROLE_TYPES:
            assert role in TEAM_ROLES, f"Role {role!r} missing from TEAM_ROLES"

    def test_roles_mention_cmd_capability(self) -> None:
        for role, contract in TEAM_ROLES.items():
            assert "[CMD:" in contract, f"Role {role!r} contract missing CMD capability"

    def test_expected_roles_present(self) -> None:
        expected = {"analyst", "planner", "validator", "spec_writer", "reviewer"}
        assert set(TEAM_ROLES.keys()) == expected


# ---------------------------------------------------------------------------
# PhaseResult
# ---------------------------------------------------------------------------


class TestPhaseResult:
    def test_defaults(self) -> None:
        pr = PhaseResult()
        assert pr.phase_name == ""
        assert pr.content == ""
        assert pr.commands_executed == []
        assert pr.duration_seconds == 0.0

    def test_with_commands(self) -> None:
        pr = PhaseResult(
            phase_name="analyst",
            content="analysis",
            commands_executed=[{"command": "/status", "result": "ok"}],
        )
        assert len(pr.commands_executed) == 1


# ---------------------------------------------------------------------------
# TeamCompletionResult
# ---------------------------------------------------------------------------


class TestTeamCompletionResult:
    def test_defaults(self) -> None:
        r = TeamCompletionResult()
        assert r.run_id == ""
        assert r.total_commands == 0
        assert r.phases == []

    def test_as_dict(self) -> None:
        r = TeamCompletionResult(
            run_id="abc",
            task_description="test task",
            spec_path=".ollama/spec/test.md",
            phases=[
                PhaseResult(phase_name="analyst", agent_role="analyst", content="ok", duration_seconds=1.0),
            ],
            total_duration=5.0,
            total_commands=2,
        )
        d = r.as_dict()
        assert d["run_id"] == "abc"
        assert d["total_commands"] == 2
        assert len(d["phases"]) == 1
        assert d["phases"][0]["phase"] == "analyst"


# ---------------------------------------------------------------------------
# TeamCompletionLoop
# ---------------------------------------------------------------------------


def _make_mock_session() -> MagicMock:
    """Create a mock session with the required interface."""
    session = MagicMock()
    session.session_id = "test-session"
    session.model = "llama3.2"
    session.provider = "ollama"
    session.create_sub_context = MagicMock()
    session.agent_comm = MagicMock()
    session.agent_comm.send = MagicMock()
    session.agent_comm.get_token_savings = MagicMock(
        return_value={"total_messages": 0, "context_tokens_saved": 0}
    )
    session.memory_layer = MagicMock()
    session.memory_layer.get_context_block = MagicMock(return_value="")
    session.memory_layer.store = MagicMock()

    async def mock_send(prompt: str, agent_type: str = "", context_id: str = "") -> dict:
        return {"content": f"[placeholder response for {agent_type}]"}

    session.send = AsyncMock(side_effect=mock_send)
    return session


class TestTeamCompletionLoop:
    def test_init(self) -> None:
        session = _make_mock_session()
        loop = TeamCompletionLoop(session)
        assert loop.session is session
        assert loop.command_processor is None
        assert len(loop._run_id) == 8

    def test_init_with_command_processor(self) -> None:
        session = _make_mock_session()
        cp = MagicMock()
        loop = TeamCompletionLoop(session, command_processor=cp)
        assert loop.command_processor is cp

    def test_slug(self) -> None:
        session = _make_mock_session()
        loop = TeamCompletionLoop(session)
        assert loop._slug("Build a REST API") == "build-a-rest-api"
        assert loop._slug("Hello World!!!") == "hello-world"
        assert len(loop._slug("x" * 200)) <= 60

    def test_command_knowledge_injected(self) -> None:
        session = _make_mock_session()
        loop = TeamCompletionLoop(session)
        assert "Available CLI Commands" in loop._command_knowledge

    def test_run_executes_all_phases(self, tmp_path: Path) -> None:
        session = _make_mock_session()
        loop = TeamCompletionLoop(session)

        with (
            patch("runner.team_completion.SPEC_DIR", tmp_path / "spec"),
            patch("runner.team_completion.TASKS_DIR", tmp_path / "tasks"),
        ):
            result = asyncio.run(loop.run("Build a widget"))

        assert isinstance(result, TeamCompletionResult)
        assert len(result.phases) == 5
        phase_names = [p.phase_name for p in result.phases]
        assert phase_names == ["analyst", "planner", "validator", "spec_writer", "reviewer"]

    def test_run_creates_spec_file(self, tmp_path: Path) -> None:
        session = _make_mock_session()
        loop = TeamCompletionLoop(session)

        with (
            patch("runner.team_completion.SPEC_DIR", tmp_path / "spec"),
            patch("runner.team_completion.TASKS_DIR", tmp_path / "tasks"),
        ):
            result = asyncio.run(loop.run("Build a widget"))

        spec_path = Path(result.spec_path)
        assert spec_path.exists()
        content = spec_path.read_text()
        assert "team-completion" in content

    def test_run_creates_task_record(self, tmp_path: Path) -> None:
        session = _make_mock_session()
        loop = TeamCompletionLoop(session)

        with (
            patch("runner.team_completion.SPEC_DIR", tmp_path / "spec"),
            patch("runner.team_completion.TASKS_DIR", tmp_path / "tasks"),
        ):
            result = asyncio.run(loop.run("Test task"))
            assert result.run_id
            assert result.task_description == "Test task"

    def test_run_stores_memory(self, tmp_path: Path) -> None:
        session = _make_mock_session()
        loop = TeamCompletionLoop(session)

        with (
            patch("runner.team_completion.SPEC_DIR", tmp_path / "spec"),
            patch("runner.team_completion.TASKS_DIR", tmp_path / "tasks"),
        ):
            asyncio.run(loop.run("Memory test"))

        session.memory_layer.store.assert_called()

    def test_autonomous_command_execution(self, tmp_path: Path) -> None:
        """When agent output contains [CMD: ...], commands are executed."""
        session = _make_mock_session()

        # Make the analyst return a command directive
        call_count = 0

        async def mock_send_with_cmd(prompt: str, agent_type: str = "", context_id: str = "") -> dict:
            nonlocal call_count
            call_count += 1
            if call_count == 1:  # analyst phase
                return {"content": "Analysis: [CMD: /status]\nKey insights: ..."}
            return {"content": f"[placeholder for {agent_type}]"}

        session.send = AsyncMock(side_effect=mock_send_with_cmd)

        # Create a mock command processor
        cp = MagicMock()

        async def mock_dispatch(line: str):
            from tui.command_processor import CommandResult

            return CommandResult(output=["session info here"])

        cp.dispatch = AsyncMock(side_effect=mock_dispatch)

        loop = TeamCompletionLoop(session, command_processor=cp)
        with (
            patch("runner.team_completion.SPEC_DIR", tmp_path / "spec"),
            patch("runner.team_completion.TASKS_DIR", tmp_path / "tasks"),
        ):
            result = asyncio.run(loop.run("CMD test"))

        # The analyst phase should have executed 1 command
        assert result.phases[0].commands_executed
        assert result.total_commands >= 1


# ---------------------------------------------------------------------------
# Command registration
# ---------------------------------------------------------------------------


class TestCommandRegistration:
    """Verify /complete_w_team is registered in the command processor."""

    def test_registered(self) -> None:
        from tui.command_processor import COMMAND_REGISTRY

        assert "/complete_w_team" in COMMAND_REGISTRY

    def test_handler_name(self) -> None:
        from tui.command_processor import COMMAND_REGISTRY

        handler_name = COMMAND_REGISTRY["/complete_w_team"][0]
        assert handler_name == "_cmd_complete_w_team"

    def test_category(self) -> None:
        from tui.command_processor import COMMAND_REGISTRY

        category = COMMAND_REGISTRY["/complete_w_team"][2]
        assert category == "Agents"
