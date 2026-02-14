"""Tests for TUI widgets -- ChatMessage, InputArea, StatusPanel, IntentBadge, LlamaSpinner."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# ChatMessage widget tests
# ---------------------------------------------------------------------------


class TestChatMessageInit:
    """Test ChatMessage instantiation and attribute storage."""

    def test_creates_user_message(self):
        """ChatMessage stores content and role for user messages."""
        from tui.widgets.chat_message import ChatMessage

        msg = ChatMessage(content="Hello", role="user")
        assert msg.content == "Hello"
        assert msg.role == "user"
        assert msg.agent_type is None
        assert msg.timestamp is None

    def test_creates_assistant_message(self):
        """ChatMessage stores content, role, and agent_type for assistant messages."""
        from tui.widgets.chat_message import ChatMessage

        msg = ChatMessage(content="Hi there", role="assistant", agent_type="code")
        assert msg.content == "Hi there"
        assert msg.role == "assistant"
        assert msg.agent_type == "code"

    def test_creates_with_timestamp(self):
        """ChatMessage stores an optional timestamp."""
        from tui.widgets.chat_message import ChatMessage

        msg = ChatMessage(content="Test", role="user", timestamp="12:34")
        assert msg.timestamp == "12:34"

    def test_creates_without_timestamp(self):
        """ChatMessage defaults timestamp to None."""
        from tui.widgets.chat_message import ChatMessage

        msg = ChatMessage(content="Test", role="user")
        assert msg.timestamp is None

    def test_agent_type_none_for_user(self):
        """User messages default agent_type to None."""
        from tui.widgets.chat_message import ChatMessage

        msg = ChatMessage(content="test", role="user")
        assert msg.agent_type is None

    def test_various_agent_types(self):
        """ChatMessage accepts various agent type strings."""
        from tui.widgets.chat_message import ChatMessage

        for agent in ("code", "review", "test", "plan", "docs", "debug"):
            msg = ChatMessage(content="x", role="assistant", agent_type=agent)
            assert msg.agent_type == agent

    def test_content_reactive_attribute(self):
        """ChatMessage.content is a reactive attribute and can be updated."""
        from tui.widgets.chat_message import ChatMessage

        msg = ChatMessage(content="original", role="user")
        msg.content = "updated"
        assert msg.content == "updated"

    def test_role_reactive_attribute(self):
        """ChatMessage.role is a reactive attribute."""
        from tui.widgets.chat_message import ChatMessage

        msg = ChatMessage(content="x", role="user")
        msg.role = "assistant"
        assert msg.role == "assistant"

    def test_has_default_css(self):
        """ChatMessage has DEFAULT_CSS defined."""
        from tui.widgets.chat_message import ChatMessage

        assert ChatMessage.DEFAULT_CSS is not None
        assert "ChatMessage" in ChatMessage.DEFAULT_CSS


# ---------------------------------------------------------------------------
# InputArea widget tests
# ---------------------------------------------------------------------------


class TestInputAreaInit:
    """Test InputArea instantiation."""

    def test_creates(self):
        """InputArea initializes with empty history."""
        from tui.widgets.input_area import InputArea

        area = InputArea()
        assert area._history == []
        assert area._history_index == -1

    def test_history_starts_empty(self):
        """InputArea history list starts as empty."""
        from tui.widgets.input_area import InputArea

        area = InputArea()
        assert len(area._history) == 0

    def test_history_index_starts_negative(self):
        """InputArea history index starts at -1 (no selection)."""
        from tui.widgets.input_area import InputArea

        area = InputArea()
        assert area._history_index == -1


class TestInputAreaSubmitted:
    """Test InputArea.Submitted message class."""

    def test_submitted_is_message_subclass(self):
        """InputArea.Submitted is a Textual Message subclass."""
        from textual.message import Message

        from tui.widgets.input_area import InputArea

        assert issubclass(InputArea.Submitted, Message)

    def test_submitted_stores_value(self):
        """InputArea.Submitted stores the submitted text value."""
        from tui.widgets.input_area import InputArea

        msg = InputArea.Submitted("hello world")
        assert msg.value == "hello world"

    def test_submitted_stores_empty_value(self):
        """InputArea.Submitted can store an empty string."""
        from tui.widgets.input_area import InputArea

        msg = InputArea.Submitted("")
        assert msg.value == ""

    def test_submitted_stores_command_value(self):
        """InputArea.Submitted can store slash command text."""
        from tui.widgets.input_area import InputArea

        msg = InputArea.Submitted("/help")
        assert msg.value == "/help"

    def test_submitted_stores_multiword_value(self):
        """InputArea.Submitted preserves full text including spaces."""
        from tui.widgets.input_area import InputArea

        msg = InputArea.Submitted("write a function to sort a list")
        assert msg.value == "write a function to sort a list"


class TestInputAreaCSS:
    """Test InputArea CSS configuration."""

    def test_has_default_css(self):
        """InputArea has DEFAULT_CSS defined."""
        from tui.widgets.input_area import InputArea

        assert InputArea.DEFAULT_CSS is not None
        assert "InputArea" in InputArea.DEFAULT_CSS

    def test_css_has_dock_bottom(self):
        """InputArea CSS does not dock individually (parent #bottom-zone docks)."""
        from tui.widgets.input_area import InputArea

        assert "dock: bottom" not in InputArea.DEFAULT_CSS


# ---------------------------------------------------------------------------
# StatusPanel widget tests
# ---------------------------------------------------------------------------


class TestStatusPanelInit:
    """Test StatusPanel instantiation and defaults."""

    def test_creates_with_defaults(self):
        """StatusPanel initializes with default reactive values."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        assert panel.model_name == "llama3.2"
        assert panel.provider_name == "ollama"
        assert panel.context_pct == 0.0
        assert panel.token_count == 0
        assert panel.cost == 0.0
        assert panel.job_status == "idle"

    def test_model_name_reactive(self):
        """StatusPanel.model_name can be set directly."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        panel.model_name = "codellama"
        assert panel.model_name == "codellama"

    def test_provider_name_reactive(self):
        """StatusPanel.provider_name can be set directly."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        panel.provider_name = "claude"
        assert panel.provider_name == "claude"

    def test_context_pct_reactive(self):
        """StatusPanel.context_pct can be set directly."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        panel.context_pct = 0.75
        assert panel.context_pct == 0.75

    def test_token_count_reactive(self):
        """StatusPanel.token_count can be set directly."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        panel.token_count = 500
        assert panel.token_count == 500

    def test_cost_reactive(self):
        """StatusPanel.cost can be set directly."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        panel.cost = 0.0123
        assert panel.cost == pytest.approx(0.0123)

    def test_job_status_reactive(self):
        """StatusPanel.job_status can be set directly."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        panel.job_status = "thinking"
        assert panel.job_status == "thinking"


class TestStatusPanelUpdateFromSession:
    """Test StatusPanel.update_from_session method."""

    def test_update_model_and_provider(self):
        """update_from_session sets model_name and provider_name from session."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        session = MagicMock()
        session.model = "codellama"
        session.provider = "claude"
        # Remove attributes we do not need for this test
        del session.context_manager
        del session.token_counter

        panel.update_from_session(session)
        assert panel.model_name == "codellama"
        assert panel.provider_name == "claude"

    def test_update_with_context_manager(self):
        """update_from_session reads context usage_ratio when available."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        session = MagicMock()
        session.model = "llama3.2"
        session.provider = "ollama"
        session.context_manager.usage_ratio = 0.42
        del session.token_counter

        panel.update_from_session(session)
        assert panel.context_pct == pytest.approx(0.42)

    def test_update_with_token_counter(self):
        """update_from_session reads token counts when available."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        session = MagicMock()
        session.model = "llama3.2"
        session.provider = "ollama"
        session.token_counter.total_tokens = 1234
        session.token_counter.estimated_cost = 0.05
        del session.context_manager

        panel.update_from_session(session)
        assert panel.token_count == 1234
        assert panel.cost == pytest.approx(0.05)

    def test_update_with_full_session(self):
        """update_from_session reads all fields when all are present."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        session = MagicMock()
        session.model = "mixtral"
        session.provider = "openai"
        session.context_manager.usage_ratio = 0.65
        session.token_counter.total_tokens = 9999
        session.token_counter.estimated_cost = 1.23

        panel.update_from_session(session)
        assert panel.model_name == "mixtral"
        assert panel.provider_name == "openai"
        assert panel.context_pct == pytest.approx(0.65)
        assert panel.token_count == 9999
        assert panel.cost == pytest.approx(1.23)

    def test_update_with_missing_attributes(self):
        """update_from_session handles session without optional attributes."""
        from tui.widgets.status_panel import StatusPanel

        panel = StatusPanel()

        # A bare object with only model and provider
        class BareSession:
            model = "tiny"
            provider = "local"

        panel.update_from_session(BareSession())
        assert panel.model_name == "tiny"
        assert panel.provider_name == "local"
        # Other values unchanged from defaults
        assert panel.context_pct == 0.0
        assert panel.token_count == 0
        assert panel.cost == 0.0


class TestStatusPanelCSS:
    """Test StatusPanel CSS configuration."""

    def test_has_default_css(self):
        """StatusPanel has DEFAULT_CSS defined."""
        from tui.widgets.status_panel import StatusPanel

        assert StatusPanel.DEFAULT_CSS is not None
        assert "StatusPanel" in StatusPanel.DEFAULT_CSS

    def test_css_has_dock_bottom(self):
        """StatusPanel CSS does not dock individually (parent #bottom-zone docks)."""
        from tui.widgets.status_panel import StatusPanel

        assert "dock: bottom" not in StatusPanel.DEFAULT_CSS


# ---------------------------------------------------------------------------
# IntentBadge widget tests
# ---------------------------------------------------------------------------


class TestIntentBadgeInit:
    """Test IntentBadge instantiation."""

    def test_creates_with_defaults(self):
        """IntentBadge initializes with empty agent_type and zero confidence."""
        from tui.widgets.intent_badge import IntentBadge

        badge = IntentBadge()
        assert badge.agent_type == ""
        assert badge.confidence == 0.0


class TestIntentBadgeShowHide:
    """Test IntentBadge show/hide methods."""

    def test_show_sets_values(self):
        """show() sets agent_type and confidence."""
        from tui.widgets.intent_badge import IntentBadge

        badge = IntentBadge()
        badge.show("code", 0.95)
        assert badge.agent_type == "code"
        assert badge.confidence == pytest.approx(0.95)

    def test_hide_clears_values(self):
        """hide() resets agent_type and confidence to defaults."""
        from tui.widgets.intent_badge import IntentBadge

        badge = IntentBadge()
        badge.show("debug", 0.8)
        badge.hide()
        assert badge.agent_type == ""
        assert badge.confidence == 0.0

    def test_show_multiple_times(self):
        """show() can be called multiple times to update values."""
        from tui.widgets.intent_badge import IntentBadge

        badge = IntentBadge()
        badge.show("code", 0.9)
        assert badge.agent_type == "code"

        badge.show("review", 0.7)
        assert badge.agent_type == "review"
        assert badge.confidence == pytest.approx(0.7)

    def test_show_then_hide_then_show(self):
        """show/hide/show cycle works correctly."""
        from tui.widgets.intent_badge import IntentBadge

        badge = IntentBadge()
        badge.show("test", 0.85)
        badge.hide()
        badge.show("plan", 0.6)
        assert badge.agent_type == "plan"
        assert badge.confidence == pytest.approx(0.6)


class TestIntentBadgeReactives:
    """Test IntentBadge reactive attributes."""

    def test_agent_type_reactive(self):
        """agent_type can be set directly."""
        from tui.widgets.intent_badge import IntentBadge

        badge = IntentBadge()
        badge.agent_type = "docs"
        assert badge.agent_type == "docs"

    def test_confidence_reactive(self):
        """confidence can be set directly."""
        from tui.widgets.intent_badge import IntentBadge

        badge = IntentBadge()
        badge.confidence = 0.42
        assert badge.confidence == pytest.approx(0.42)


class TestIntentBadgeColors:
    """Test the agent badge color map."""

    def test_color_map_has_expected_agents(self):
        """The color map covers the standard agent types."""
        from tui.widgets.intent_badge import _AGENT_BADGE_COLORS

        expected_agents = ["code", "review", "test", "plan", "docs", "debug", "orchestrator"]
        for agent in expected_agents:
            assert agent in _AGENT_BADGE_COLORS, f"Missing color for agent: {agent}"

    def test_color_values_are_hex(self):
        """All color values are hex color strings."""
        from tui.widgets.intent_badge import _AGENT_BADGE_COLORS

        for agent, color in _AGENT_BADGE_COLORS.items():
            assert color.startswith("#"), f"Color for {agent} is not hex: {color}"
            assert len(color) == 7, f"Color for {agent} is not #RRGGBB: {color}"


# ---------------------------------------------------------------------------
# LlamaSpinner widget tests
# ---------------------------------------------------------------------------


class TestLlamaSpinnerInit:
    """Test LlamaSpinner instantiation."""

    def test_creates_with_defaults(self):
        """LlamaSpinner initializes as not spinning with frame_index 0."""
        from tui.widgets.spinner import LlamaSpinner

        spinner = LlamaSpinner()
        assert spinner.spinning is False
        assert spinner.frame_index == 0


class TestLlamaSpinnerFrames:
    """Test the spinner frame definitions."""

    def test_has_eight_frames(self):
        """There are 8 spinner frames defined."""
        from tui.widgets.spinner import _LLAMA_SPINNER_FRAMES

        assert len(_LLAMA_SPINNER_FRAMES) == 8

    def test_all_frames_contain_llama_emoji(self):
        """Every frame contains the llama emoji."""
        from tui.widgets.spinner import _LLAMA_SPINNER_FRAMES

        for i, frame in enumerate(_LLAMA_SPINNER_FRAMES):
            assert "\U0001f999" in frame, f"Frame {i} missing llama emoji: {frame}"

    def test_all_frames_are_non_empty_strings(self):
        """Every frame is a non-empty string."""
        from tui.widgets.spinner import _LLAMA_SPINNER_FRAMES

        for i, frame in enumerate(_LLAMA_SPINNER_FRAMES):
            assert isinstance(frame, str), f"Frame {i} is not a string"
            assert len(frame) > 0, f"Frame {i} is empty"

    def test_frames_are_unique(self):
        """All spinner frames are unique."""
        from tui.widgets.spinner import _LLAMA_SPINNER_FRAMES

        assert len(set(_LLAMA_SPINNER_FRAMES)) == len(_LLAMA_SPINNER_FRAMES)


class TestLlamaSpinnerReactives:
    """Test LlamaSpinner reactive attributes."""

    def test_spinning_reactive(self):
        """spinning can be toggled directly."""
        from tui.widgets.spinner import LlamaSpinner

        spinner = LlamaSpinner()
        spinner.spinning = True
        assert spinner.spinning is True
        spinner.spinning = False
        assert spinner.spinning is False

    def test_frame_index_reactive(self):
        """frame_index can be set directly."""
        from tui.widgets.spinner import LlamaSpinner

        spinner = LlamaSpinner()
        spinner.frame_index = 5
        assert spinner.frame_index == 5


class TestLlamaSpinnerCSS:
    """Test LlamaSpinner CSS configuration."""

    def test_has_default_css(self):
        """LlamaSpinner has DEFAULT_CSS defined."""
        from tui.widgets.spinner import LlamaSpinner

        assert LlamaSpinner.DEFAULT_CSS is not None
        assert "LlamaSpinner" in LlamaSpinner.DEFAULT_CSS


# ---------------------------------------------------------------------------
# ChatScreen bottom-zone layout tests (regression for input visibility)
# ---------------------------------------------------------------------------


class TestChatScreenBottomZone:
    """Verify InputArea and StatusPanel are stacked in #bottom-zone."""

    def test_bottom_zone_has_dock_bottom(self):
        """The #bottom-zone container should dock to bottom in ChatScreen CSS."""
        from tui.screens.chat import ChatScreen

        assert "#bottom-zone" in ChatScreen.DEFAULT_CSS
        assert "dock: bottom" in ChatScreen.DEFAULT_CSS
