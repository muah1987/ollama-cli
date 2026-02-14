"""
Tests for the chain controller module -- multi-wave subagent orchestration.
"""

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

_PROJECT_ROOT = str(Path(__file__).parent.parent)


# ---------------------------------------------------------------------------
# Chain controller module tests
# ---------------------------------------------------------------------------


class TestChainControllerModule:
    """Tests for chain controller data structures and helpers."""

    def test_module_exists(self) -> None:
        """runner/chain_controller.py should exist."""
        path = Path(__file__).parent.parent / "runner" / "chain_controller.py"
        assert path.is_file()

    def test_default_waves(self) -> None:
        """DEFAULT_WAVES should have 4 waves with expected names."""
        from runner.chain_controller import DEFAULT_WAVES

        assert len(DEFAULT_WAVES) == 4
        names = [w.name for w in DEFAULT_WAVES]
        assert "analysis" in names
        assert "plan_validate_optimize" in names
        assert "execution" in names
        assert "finalize" in names

    def test_agent_contracts(self) -> None:
        """AGENT_CONTRACTS should have at least 10 entries with expected keys."""
        from runner.chain_controller import AGENT_CONTRACTS

        assert len(AGENT_CONTRACTS) >= 10
        expected_keys = [
            "analyzer_a",
            "analyzer_b",
            "planner",
            "validator",
            "optimizer",
            "executor_1",
            "executor_2",
            "monitor",
            "reporter",
            "cleaner",
        ]
        for key in expected_keys:
            assert key in AGENT_CONTRACTS

    def test_wave_config_dataclass(self) -> None:
        """WaveConfig should have name, agents, description fields."""
        from runner.chain_controller import WaveConfig

        wc = WaveConfig(name="test", agents=["a", "b"], description="desc")
        assert wc.name == "test"
        assert wc.agents == ["a", "b"]
        assert wc.description == "desc"

    def test_shared_state_dataclass(self) -> None:
        """SharedState should have all required fields."""
        from runner.chain_controller import SharedState

        ss = SharedState()
        assert hasattr(ss, "run_id")
        assert hasattr(ss, "problem_statement")
        assert hasattr(ss, "success_criteria")
        assert hasattr(ss, "constraints")
        assert hasattr(ss, "assumptions")
        assert hasattr(ss, "risks")
        assert hasattr(ss, "plan")
        assert hasattr(ss, "artifacts")
        assert hasattr(ss, "final_answer_outline")
        assert hasattr(ss, "wave_outputs")

    def test_shared_state_to_context_block(self) -> None:
        """to_context_block() should return formatted text with Problem and key sections."""
        from runner.chain_controller import SharedState

        ss = SharedState(
            run_id="abc123",
            problem_statement="Fix the bug",
            success_criteria=["Tests pass"],
            constraints=["No breaking changes"],
        )
        block = ss.to_context_block()
        assert "Problem" in block
        assert "Fix the bug" in block
        assert "abc123" in block
        assert "Success Criteria" in block
        assert "Constraints" in block

    def test_shared_state_as_dict(self) -> None:
        """as_dict() should return a serializable dict with all fields."""
        from runner.chain_controller import SharedState

        ss = SharedState(run_id="x", problem_statement="test")
        d = ss.as_dict()
        assert isinstance(d, dict)
        assert d["run_id"] == "x"
        assert d["problem_statement"] == "test"
        for key in (
            "success_criteria",
            "constraints",
            "assumptions",
            "risks",
            "plan",
            "artifacts",
            "final_answer_outline",
        ):
            assert key in d

    def test_parse_chain_config(self) -> None:
        """parse_chain_config() should parse a config dict into WaveConfig list."""
        from runner.chain_controller import parse_chain_config

        config = {
            "waves": [
                {"name": "w1", "agents": ["a1", "a2"], "description": "first wave"},
                {"name": "w2", "agents": ["b1"]},
            ]
        }
        waves = parse_chain_config(config)
        assert len(waves) == 2
        assert waves[0].name == "w1"
        assert waves[0].agents == ["a1", "a2"]
        assert waves[0].description == "first wave"
        assert waves[1].name == "w2"
        assert waves[1].description == ""


# ---------------------------------------------------------------------------
# ChainController init tests
# ---------------------------------------------------------------------------


class TestChainControllerInit:
    """Tests for ChainController construction and ingest."""

    def test_init_with_session(self) -> None:
        """ChainController can be initialized with a mock session."""
        from runner.chain_controller import ChainController

        mock_session = MagicMock()
        cc = ChainController(session=mock_session)
        assert cc.session is mock_session
        assert len(cc.waves) == 4

    def test_ingest(self) -> None:
        """ingest() should initialize SharedState with run_id and problem_statement."""
        from runner.chain_controller import ChainController

        mock_session = MagicMock()
        cc = ChainController(session=mock_session)
        state = cc.ingest("Build a CLI tool")
        assert state.run_id != ""
        assert len(state.run_id) == 8
        assert state.problem_statement == "Build a CLI tool"

    def test_custom_waves(self) -> None:
        """ChainController should accept custom waves list."""
        from runner.chain_controller import ChainController, WaveConfig

        custom = [WaveConfig(name="only_wave", agents=["agent_x"])]
        mock_session = MagicMock()
        cc = ChainController(session=mock_session, waves=custom)
        assert len(cc.waves) == 1
        assert cc.waves[0].name == "only_wave"


# ---------------------------------------------------------------------------
# Chain command tests (subprocess to avoid cmd module collision)
# ---------------------------------------------------------------------------


class TestChainCommand:
    """Tests for /chain command registration and config file."""

    def test_chain_command_in_command_table(self) -> None:
        """'/chain' should be in InteractiveMode._COMMAND_TABLE."""
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from model.session import Session; "
                    "from ollama_cmd.interactive import InteractiveMode; "
                    "s = Session(model='llama3.2', provider='ollama'); "
                    "r = InteractiveMode(s); "
                    "print('/chain' in r._COMMAND_TABLE)"
                ),
            ],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
        )
        assert result.returncode == 0
        assert result.stdout.strip() == "True"

    def test_chain_config_file_exists(self) -> None:
        """.ollama/chain.json should exist."""
        path = Path(__file__).parent.parent / ".ollama" / "chain.json"
        assert path.is_file()
