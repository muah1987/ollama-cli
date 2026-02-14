"""Tests for the TUI application lifecycle and configuration."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tui.app import ChatApp


class TestChatAppInstantiation:
    """Test ChatApp can be created and has expected properties."""

    def test_app_creates(self):
        """ChatApp can be instantiated without arguments."""
        app = ChatApp()
        assert app.TITLE == "cli-ollama"
        assert app.session is None

    def test_app_sub_title(self):
        """ChatApp has the expected SUB_TITLE."""
        app = ChatApp()
        assert app.SUB_TITLE == "AI Coding Assistant"

    def test_app_with_session(self):
        """ChatApp accepts a session parameter and stores it."""
        session = MagicMock()
        app = ChatApp(session=session)
        assert app.session is session

    def test_app_with_none_session(self):
        """ChatApp defaults to None session when not provided."""
        app = ChatApp()
        assert app.session is None


class TestChatAppBindings:
    """Test ChatApp key bindings are correctly configured."""

    def test_has_bindings(self):
        """ChatApp has BINDINGS list."""
        app = ChatApp()
        assert len(app.BINDINGS) == 5

    def test_binding_ctrl_q_quit(self):
        """Ctrl+Q is bound to quit."""
        app = ChatApp()
        binding_keys = [b.key for b in app.BINDINGS]
        assert "ctrl+q" in binding_keys

    def test_binding_ctrl_p_command_palette(self):
        """Ctrl+P is bound to command palette."""
        app = ChatApp()
        binding_keys = [b.key for b in app.BINDINGS]
        assert "ctrl+p" in binding_keys

    def test_binding_ctrl_b_sidebar(self):
        """Ctrl+B is bound to toggle sidebar."""
        app = ChatApp()
        binding_keys = [b.key for b in app.BINDINGS]
        assert "ctrl+b" in binding_keys

    def test_binding_f1_help(self):
        """F1 is bound to help."""
        app = ChatApp()
        binding_keys = [b.key for b in app.BINDINGS]
        assert "f1" in binding_keys

    def test_binding_descriptions(self):
        """All bindings have descriptions."""
        app = ChatApp()
        for b in app.BINDINGS:
            assert b.description, f"Binding {b.key} missing description"


class TestChatAppCSS:
    """Test ChatApp CSS configuration."""

    def test_css_path(self):
        """ChatApp has CSS_PATH set to the correct file."""
        assert ChatApp.CSS_PATH == "styles/app.tcss"


class TestChatAppActions:
    """Test ChatApp action methods exist."""

    def test_action_command_palette_exists(self):
        """action_command_palette method exists on ChatApp."""
        app = ChatApp()
        assert hasattr(app, "action_command_palette")
        assert callable(app.action_command_palette)

    def test_action_toggle_sidebar_exists(self):
        """action_toggle_sidebar method exists on ChatApp."""
        app = ChatApp()
        assert hasattr(app, "action_toggle_sidebar")
        assert callable(app.action_toggle_sidebar)

    def test_action_help_exists(self):
        """action_help method exists on ChatApp."""
        app = ChatApp()
        assert hasattr(app, "action_help")
        assert callable(app.action_help)

    def test_action_command_palette_does_not_raise(self):
        """action_command_palette is a no-op stub and should not raise."""
        app = ChatApp()
        # Should not raise (it's a pass-through stub)
        app.action_command_palette()

    def test_action_toggle_sidebar_does_not_raise_without_app(self):
        """action_toggle_sidebar gracefully handles missing sidebar."""
        app = ChatApp()
        # Should not raise -- the except block catches when no sidebar is found
        app.action_toggle_sidebar()


@pytest.mark.asyncio
class TestChatAppRunTest:
    """Test ChatApp with Textual's run_test for mounted behavior."""

    async def test_app_mounts_and_exits(self):
        """ChatApp can mount and exit cleanly via run_test."""
        app = ChatApp()
        async with app.run_test() as pilot:
            # App should be running at this point
            assert app.is_running
            await pilot.exit(None)

    async def test_app_pushes_chat_screen_on_mount(self):
        """ChatApp pushes ChatScreen on mount."""
        from tui.screens.chat import ChatScreen

        app = ChatApp()
        async with app.run_test() as pilot:
            # After mount, the screen stack should include ChatScreen
            assert isinstance(app.screen, ChatScreen)
            await pilot.exit(None)

    async def test_app_with_mock_session_mounts(self):
        """ChatApp with a mock session mounts without error."""
        session = MagicMock()
        session.model = "llama3.2"
        session.provider = "ollama"
        session.session_id = "test-session"
        session.context_manager = MagicMock()
        session.context_manager.usage_ratio = 0.1
        session.token_counter = MagicMock()
        session.token_counter.total_tokens = 50
        session.token_counter.estimated_cost = 0.0

        app = ChatApp(session=session)
        async with app.run_test() as pilot:
            assert app.is_running
            assert app.session is session
            await pilot.exit(None)
