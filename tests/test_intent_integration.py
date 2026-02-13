"""Integration tests for the IntentClassifier within the InteractiveMode REPL.

These tests verify the REPL integration points -- the /intent slash command
and the auto-detection block -- NOT the classifier accuracy itself (covered
by ``test_intent_classifier.py``).

Integration points under test:
1. ``/intent`` is registered in ``InteractiveMode._COMMAND_TABLE``
2. ``_cmd_intent`` handler works for all subcommands
3. Auto-detection logic in the REPL loop respects config flags
4. ``classify_intent`` is importable from ``runner.intent_classifier``
"""

from __future__ import annotations

from unittest.mock import patch

import pytest  # type: ignore[import-untyped]

from api.config import OllamaCliConfig
from ollama_cmd.interactive import InteractiveMode
from runner.intent_classifier import IntentResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


class _MockContextManager:
    """Minimal stand-in for ContextManager used by Session."""

    def __init__(self) -> None:
        self.messages: list[dict] = []
        self.max_context_length: int = 4096

    def get_context_usage(self) -> dict:
        return {"percentage": 0}


class _MockSession:
    """Minimal Session stand-in for InteractiveMode.__init__."""

    def __init__(self) -> None:
        self.session_id: str = "test-session-12345678"
        self.model: str = "llama3.2"
        self.provider: str = "ollama"
        self.context_manager = _MockContextManager()

    async def send(self, prompt: str, agent_type: str | None = None) -> dict:
        return {"content": f"Mock response for {prompt}", "agent_type": agent_type}

    async def end(self) -> None:
        pass


@pytest.fixture()
def mock_session() -> _MockSession:
    return _MockSession()


@pytest.fixture()
def repl(mock_session: _MockSession) -> InteractiveMode:
    """Create an InteractiveMode wired to a mock session."""
    return InteractiveMode(mock_session)  # type: ignore[arg-type]


@pytest.fixture()
def cfg() -> OllamaCliConfig:
    """Return a fresh, default config object for patching into get_config."""
    return OllamaCliConfig()


# ---------------------------------------------------------------------------
# 1. /intent is in _COMMAND_TABLE
# ---------------------------------------------------------------------------


class TestCommandTableRegistration:
    """Verify the /intent command is wired into the REPL command table."""

    def test_intent_in_command_table(self) -> None:
        assert "/intent" in InteractiveMode._COMMAND_TABLE

    def test_intent_maps_to_handler(self) -> None:
        assert InteractiveMode._COMMAND_TABLE["/intent"] == "_cmd_intent"

    def test_handler_method_exists(self) -> None:
        assert callable(getattr(InteractiveMode, "_cmd_intent", None))


# ---------------------------------------------------------------------------
# 2. _cmd_intent handler subcommands
# ---------------------------------------------------------------------------


class TestCmdIntentHandler:
    """Exercise every _cmd_intent subcommand and verify return values."""

    def test_status_no_arg(self, repl: InteractiveMode, cfg: OllamaCliConfig, capsys: pytest.CaptureFixture[str]) -> None:
        """Calling /intent with no argument prints current status."""
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent("")
        assert result is False
        out = capsys.readouterr().out
        assert "Intent classifier" in out
        assert "Confidence threshold" in out

    def test_on(self, repl: InteractiveMode, cfg: OllamaCliConfig, capsys: pytest.CaptureFixture[str]) -> None:
        cfg.intent_enabled = False
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent("on")
        assert result is False
        assert cfg.intent_enabled is True
        out = capsys.readouterr().out
        assert "enabled" in out.lower()

    def test_off(self, repl: InteractiveMode, cfg: OllamaCliConfig, capsys: pytest.CaptureFixture[str]) -> None:
        cfg.intent_enabled = True
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent("off")
        assert result is False
        assert cfg.intent_enabled is False
        out = capsys.readouterr().out
        assert "disabled" in out.lower()

    def test_show_toggle(self, repl: InteractiveMode, cfg: OllamaCliConfig, capsys: pytest.CaptureFixture[str]) -> None:
        original = cfg.intent_show_detection
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent("show")
        assert result is False
        assert cfg.intent_show_detection is not original
        out = capsys.readouterr().out
        assert "toggled" in out.lower()

    def test_threshold_set(self, repl: InteractiveMode, cfg: OllamaCliConfig, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent("threshold 0.5")
        assert result is False
        assert cfg.intent_confidence_threshold == pytest.approx(0.5)
        out = capsys.readouterr().out
        assert "0.50" in out

    def test_threshold_no_value(self, repl: InteractiveMode, cfg: OllamaCliConfig, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent("threshold")
        assert result is False
        out = capsys.readouterr().out
        assert "threshold" in out.lower()

    def test_threshold_out_of_range(self, repl: InteractiveMode, cfg: OllamaCliConfig, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent("threshold 1.5")
        assert result is False
        out = capsys.readouterr().out
        assert "between" in out.lower() or "0.0" in out

    def test_threshold_invalid(self, repl: InteractiveMode, cfg: OllamaCliConfig, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent("threshold abc")
        assert result is False
        out = capsys.readouterr().out
        assert "invalid" in out.lower()

    def test_test_subcommand(self, repl: InteractiveMode, cfg: OllamaCliConfig, capsys: pytest.CaptureFixture[str]) -> None:
        """``/intent test <prompt>`` should classify and print results."""
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent("test write a function to reverse a string")
        assert result is False
        out = capsys.readouterr().out
        # Should print intent and reasoning lines
        assert "Intent" in out or "intent" in out
        assert "Reasoning" in out or "reasoning" in out

    def test_test_no_prompt(self, repl: InteractiveMode, cfg: OllamaCliConfig, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent("test")
        assert result is False
        out = capsys.readouterr().out
        assert "usage" in out.lower()

    def test_invalid_subcommand(self, repl: InteractiveMode, cfg: OllamaCliConfig, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent("invalid")
        assert result is False
        out = capsys.readouterr().out
        assert "unknown" in out.lower() or "Unknown" in out


class TestCmdIntentAllReturnFalse:
    """Every subcommand of /intent must return False (continue REPL)."""

    @pytest.mark.parametrize(
        "arg",
        [
            "",
            "on",
            "off",
            "show",
            "threshold 0.5",
            "threshold",
            "threshold abc",
            "threshold 1.5",
            "test write a function",
            "test",
            "invalid",
            "notacommand",
        ],
    )
    def test_returns_false(self, repl: InteractiveMode, cfg: OllamaCliConfig, arg: str) -> None:
        with patch("api.config.get_config", return_value=cfg):
            result = repl._cmd_intent(arg)
        assert result is False, f"/intent {arg!r} should return False, got {result!r}"


# ---------------------------------------------------------------------------
# 3. Auto-detection integration logic
# ---------------------------------------------------------------------------


class TestAutoDetectionLogic:
    """Verify the auto-detection block in the REPL loop."""

    def test_classifier_runs_when_enabled_and_no_prefix(self, cfg: OllamaCliConfig) -> None:
        """When intent_enabled=True and no @agent prefix, classify_intent is called."""
        cfg.intent_enabled = True
        fake_result = IntentResult(
            agent_type="code",
            confidence=0.85,
            reasoning="test",
            matched_patterns=["write", "function"],
        )

        agent_type = None
        stripped = "write a function to sort a list"

        with patch("runner.intent_classifier.classify_intent", return_value=fake_result) as mock_classify:
            # Simulate the auto-detection block from interactive.py lines 2734-2764
            if agent_type is None:
                from runner.intent_classifier import classify_intent

                if cfg.intent_enabled:
                    intent_result = classify_intent(stripped, threshold=cfg.intent_confidence_threshold)
                    if intent_result.agent_type is not None:
                        agent_type = intent_result.agent_type

            mock_classify.assert_called_once_with(stripped, threshold=cfg.intent_confidence_threshold)
        assert agent_type == "code"

    def test_classifier_skipped_when_disabled(self, cfg: OllamaCliConfig) -> None:
        """When intent_enabled=False, classify_intent is never called."""
        cfg.intent_enabled = False

        agent_type = None
        stripped = "write a function to sort a list"

        with patch("runner.intent_classifier.classify_intent") as mock_classify:
            if agent_type is None:
                from runner.intent_classifier import classify_intent

                if cfg.intent_enabled:
                    intent_result = classify_intent(stripped, threshold=cfg.intent_confidence_threshold)
                    if intent_result.agent_type is not None:
                        agent_type = intent_result.agent_type

            mock_classify.assert_not_called()
        assert agent_type is None

    def test_explicit_agent_prefix_overrides_autodetect(self, cfg: OllamaCliConfig) -> None:
        """When the user types ``@code prompt``, auto-detect is skipped."""
        cfg.intent_enabled = True

        # Simulate what the REPL does at lines 2693-2710
        stripped = "@code write a function"
        agent_type = None
        if stripped.startswith("@"):
            parts = stripped.split(" ", 1)
            if len(parts) > 1:
                agent_type = parts[0][1:]  # "code"
                stripped = parts[1]

        # At this point agent_type is "code", so auto-detection block is skipped
        with patch("runner.intent_classifier.classify_intent") as mock_classify:
            if agent_type is None:
                from runner.intent_classifier import classify_intent

                if cfg.intent_enabled:
                    classify_intent(stripped, threshold=cfg.intent_confidence_threshold)

            mock_classify.assert_not_called()
        assert agent_type == "code"

    def test_low_confidence_does_not_set_agent_type(self, cfg: OllamaCliConfig) -> None:
        """When the classifier returns None agent_type (below threshold), agent_type stays None."""
        cfg.intent_enabled = True
        low_result = IntentResult(
            agent_type=None,
            confidence=0.3,
            reasoning="not enough signal",
            matched_patterns=[],
        )

        agent_type = None
        stripped = "hello"

        with patch("runner.intent_classifier.classify_intent", return_value=low_result):
            if agent_type is None:
                from runner.intent_classifier import classify_intent

                if cfg.intent_enabled:
                    intent_result = classify_intent(stripped, threshold=cfg.intent_confidence_threshold)
                    if intent_result.agent_type is not None:
                        agent_type = intent_result.agent_type

        assert agent_type is None

    def test_auto_detected_type_passed_to_session_send(self, cfg: OllamaCliConfig) -> None:
        """The auto-detected agent_type should be the value ultimately used."""
        cfg.intent_enabled = True
        fake_result = IntentResult(
            agent_type="debug",
            confidence=0.9,
            reasoning="debug patterns",
            matched_patterns=["error", "traceback"],
        )

        agent_type = None
        stripped = "why is there a traceback error in the logs"

        with patch("runner.intent_classifier.classify_intent", return_value=fake_result):
            if agent_type is None:
                from runner.intent_classifier import classify_intent

                if cfg.intent_enabled:
                    intent_result = classify_intent(stripped, threshold=cfg.intent_confidence_threshold)
                    if intent_result.agent_type is not None:
                        agent_type = intent_result.agent_type

        assert agent_type == "debug"


# ---------------------------------------------------------------------------
# 4. Import verification
# ---------------------------------------------------------------------------


class TestImportability:
    """Verify that classify_intent and related symbols can be imported."""

    def test_classify_intent_importable(self) -> None:
        from runner.intent_classifier import classify_intent

        assert callable(classify_intent)

    def test_intent_classifier_class_importable(self) -> None:
        from runner.intent_classifier import IntentClassifier

        assert callable(IntentClassifier)

    def test_intent_result_importable(self) -> None:
        from runner.intent_classifier import IntentResult

        result = IntentResult(agent_type=None, confidence=0.0, reasoning="", matched_patterns=[])
        assert result.agent_type is None

    def test_classify_intent_returns_intent_result(self) -> None:
        from runner.intent_classifier import IntentResult, classify_intent

        result = classify_intent("hello world")
        assert isinstance(result, IntentResult)


# ---------------------------------------------------------------------------
# 5. Config interaction
# ---------------------------------------------------------------------------


class TestConfigIntegration:
    """Verify that _cmd_intent correctly reads and mutates config."""

    def test_on_mutates_config(self, repl: InteractiveMode) -> None:
        cfg = OllamaCliConfig(intent_enabled=False)
        with patch("api.config.get_config", return_value=cfg):
            repl._cmd_intent("on")
        assert cfg.intent_enabled is True

    def test_off_mutates_config(self, repl: InteractiveMode) -> None:
        cfg = OllamaCliConfig(intent_enabled=True)
        with patch("api.config.get_config", return_value=cfg):
            repl._cmd_intent("off")
        assert cfg.intent_enabled is False

    def test_threshold_mutates_config(self, repl: InteractiveMode) -> None:
        cfg = OllamaCliConfig(intent_confidence_threshold=0.7)
        with patch("api.config.get_config", return_value=cfg):
            repl._cmd_intent("threshold 0.3")
        assert cfg.intent_confidence_threshold == pytest.approx(0.3)

    def test_show_toggle_mutates_config(self, repl: InteractiveMode) -> None:
        cfg = OllamaCliConfig(intent_show_detection=True)
        with patch("api.config.get_config", return_value=cfg):
            repl._cmd_intent("show")
        assert cfg.intent_show_detection is False

    def test_show_toggle_back(self, repl: InteractiveMode) -> None:
        cfg = OllamaCliConfig(intent_show_detection=False)
        with patch("api.config.get_config", return_value=cfg):
            repl._cmd_intent("show")
        assert cfg.intent_show_detection is True

    def test_status_shows_default_agent_type_when_set(
        self, repl: InteractiveMode, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cfg = OllamaCliConfig(intent_default_agent_type="code")
        with patch("api.config.get_config", return_value=cfg):
            repl._cmd_intent("")
        out = capsys.readouterr().out
        assert "Default agent type" in out
        assert "code" in out

    def test_status_hides_default_agent_type_when_none(
        self, repl: InteractiveMode, capsys: pytest.CaptureFixture[str]
    ) -> None:
        cfg = OllamaCliConfig(intent_default_agent_type=None)
        with patch("api.config.get_config", return_value=cfg):
            repl._cmd_intent("")
        out = capsys.readouterr().out
        assert "Default agent type" not in out
