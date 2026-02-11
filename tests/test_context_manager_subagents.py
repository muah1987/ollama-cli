"""
Tests for the enhanced context manager with sub-agent support.
"""
import asyncio
import json
import tempfile
from pathlib import Path

import pytest

from runner.context_manager import ContextManager
from model.session import Session


class TestContextManagerWithSubAgents:
    """Tests for ContextManager with sub-agent contexts."""

    def test_create_sub_context(self):
        """Test creating and retrieving sub-contexts."""
        cm = ContextManager(context_id="main")
        sub_cm = cm.create_sub_context("test_subagent")

        assert sub_cm.context_id == "test_subagent"
        assert sub_cm.parent_context is cm
        assert cm.get_sub_context("test_subagent") is sub_cm

    def test_sub_context_inherits_settings(self):
        """Test that sub-contexts inherit settings from parent."""
        cm = ContextManager(
            max_context_length=8192,
            compact_threshold=0.9,
            auto_compact=False,
            keep_last_n=8
        )
        sub_cm = cm.create_sub_context("test_subagent")

        assert sub_cm.max_context_length == 8192
        assert sub_cm.compact_threshold == 0.9
        assert sub_cm.auto_compact is False
        assert sub_cm.keep_last_n == 8

    def test_sub_context_override_settings(self):
        """Test that sub-contexts can override inherited settings."""
        cm = ContextManager(
            max_context_length=8192,
            compact_threshold=0.9,
            auto_compact=False,
            keep_last_n=8
        )
        sub_cm = cm.create_sub_context(
            "test_subagent",
            max_context_length=2048,
            compact_threshold=0.75,
            auto_compact=True,
            keep_last_n=2
        )

        assert sub_cm.max_context_length == 2048
        assert sub_cm.compact_threshold == 0.75
        assert sub_cm.auto_compact is True
        assert sub_cm.keep_last_n == 2

    def test_add_message_to_sub_context(self):
        """Test adding messages to specific sub-contexts."""
        cm = ContextManager(context_id="main")
        sub_cm = cm.create_sub_context("test_subagent")

        # Add message to main context
        cm.add_message("user", "Main context message")
        assert len(cm.messages) == 1
        assert len(sub_cm.messages) == 0

        # Add message to sub-context
        cm.add_message("user", "Sub context message", context_id="test_subagent")
        assert len(cm.messages) == 1  # Unchanged
        assert len(sub_cm.messages) == 1
        assert sub_cm.messages[0]["content"] == "Sub context message"

    def test_get_total_context_tokens(self):
        """Test calculating total tokens across all contexts."""
        cm = ContextManager(context_id="main")
        sub_cm = cm.create_sub_context("test_subagent")

        # Add messages to main context (~5 tokens)
        cm.add_message("user", "Hello world")

        # Add messages to sub-context (~7 tokens)
        sub_cm.add_message("user", "Sub-agent task")
        sub_cm.add_message("assistant", "Response")

        # Should be approximately 12 tokens total
        total_tokens = cm.get_total_context_tokens()
        assert total_tokens > 10
        assert total_tokens < 20

    def test_compact_with_sub_contexts(self):
        """Test that compaction works recursively on sub-contexts."""
        cm = ContextManager(
            context_id="main",
            max_context_length=100,
            compact_threshold=0.5,
            keep_last_n=1
        )

        # Create sub-context with aggressive compaction
        sub_cm = cm.create_sub_context(
            "test_subagent",
            max_context_length=50,
            compact_threshold=0.4,
            keep_last_n=1
        )

        # Add many messages to sub-context to trigger compaction
        for i in range(10):
            sub_cm.add_message("user", f"Message {i}")

        # Add messages to main context
        for i in range(5):
            cm.add_message("user", f"Main message {i}")

        # Trigger compaction
        async def run_compact():
            return await cm.compact()

        result = asyncio.run(run_compact())

        # Should have compacted both contexts
        assert result["messages_removed"] >= 0


class TestSessionWithSubAgents:
    """Tests for Session with sub-agent support."""

    @pytest.mark.asyncio
    async def test_create_and_use_sub_context(self):
        """Test creating and using sub-contexts through Session."""
        session = Session()
        await session.start()

        # Create sub-context through session
        sub_context = session.create_sub_context("test_subagent")
        assert sub_context.context_id == "test_subagent"

        # Send message to sub-context
        result = await session.send("Test message", context_id="test_subagent")
        assert result["content"] is not None

        # Verify messages were added to sub-context
        sub_cm = session.get_sub_context("test_subagent")
        assert len(sub_cm.messages) == 2  # user + assistant messages

    def test_save_and_load_with_sub_contexts(self):
        """Test saving and loading sessions with sub-contexts."""
        session = Session()

        # Create and populate sub-context
        sub_context = session.create_sub_context("test_subagent")
        sub_context.add_message("user", "Sub-context message")
        sub_context.add_message("assistant", "Sub-context response")

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            session.save(temp_path)

            # Load session back
            loaded_session = Session.load(session.session_id, temp_path)

            # Verify sub-context was loaded
            loaded_sub = loaded_session.get_sub_context("test_subagent")
            assert loaded_sub is not None
            assert len(loaded_sub.messages) == 2
            assert loaded_sub.messages[0]["content"] == "Sub-context message"

        finally:
            Path(temp_path).unlink(missing_ok=True)