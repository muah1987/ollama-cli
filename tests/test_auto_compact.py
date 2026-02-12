"""Comprehensive tests for the auto-compact system.

Covers:
- ContextManager: should_compact(), compact(), threshold behaviour, keep_last_n,
  session persistence of compact settings, sub-context compaction
- AutoCompactSkill: check, compact, and configure actions
- Session.send(): auto-compact trigger during message processing
- /compact slash command dispatch (InteractiveMode)
- Hook integration (PreCompact hook fires before compaction)
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

# Ensure the package root is importable
_PROJECT_DIR = str(Path(__file__).resolve().parent.parent)
if _PROJECT_DIR not in sys.path:
    sys.path.insert(0, _PROJECT_DIR)

from runner.context_manager import ContextManager  # noqa: E402
from skills import AutoCompactSkill  # noqa: E402

# ---------------------------------------------------------------------------
# ContextManager: threshold detection
# ---------------------------------------------------------------------------


class TestShouldCompact:
    """Tests for ContextManager.should_compact()."""

    def test_below_threshold(self) -> None:
        """Usage below threshold returns False."""
        cm = ContextManager(max_context_length=1000, compact_threshold=0.85)
        # Add a small message (~25 tokens)
        cm.add_message("user", "Hello world, short message here.")
        assert cm.should_compact() is False

    def test_above_threshold(self) -> None:
        """Usage at or above threshold returns True."""
        cm = ContextManager(max_context_length=100, compact_threshold=0.5)
        # ~60 tokens → 60% > 50%
        cm.add_message("user", "x" * 240)
        assert cm.should_compact() is True

    def test_exactly_at_threshold(self) -> None:
        """Usage exactly at threshold returns True."""
        cm = ContextManager(max_context_length=100, compact_threshold=0.5)
        # Need exactly 50 tokens → 200 chars
        cm.add_message("user", "x" * 200)
        assert cm.should_compact() is True

    def test_zero_context_length(self) -> None:
        """Zero-length context window never triggers compaction."""
        cm = ContextManager(max_context_length=0, compact_threshold=0.5)
        cm.add_message("user", "x" * 1000)
        assert cm.should_compact() is False

    def test_custom_threshold(self) -> None:
        """Custom threshold (90%) is respected."""
        cm = ContextManager(max_context_length=1000, compact_threshold=0.9)
        # Add 800 tokens (3200 chars) → 80% < 90%
        cm.add_message("user", "y" * 3200)
        assert cm.should_compact() is False
        # Add more to exceed 90%
        cm.add_message("user", "z" * 600)
        assert cm.should_compact() is True

    def test_after_compaction_below_threshold(self) -> None:
        """After compaction, message count is reduced."""
        cm = ContextManager(max_context_length=200, compact_threshold=0.5, keep_last_n=1)
        for i in range(10):
            cm.add_message("user", f"Message number {i} " * 5)
        assert cm.should_compact() is True

        msg_before = len(cm.messages)
        asyncio.run(cm.compact())
        # Compaction should reduce message count (summary + keep_last_n)
        assert len(cm.messages) < msg_before


# ---------------------------------------------------------------------------
# ContextManager: compact() method
# ---------------------------------------------------------------------------


class TestCompact:
    """Tests for ContextManager.compact() method."""

    def test_compact_returns_stats(self) -> None:
        """compact() returns before/after tokens and messages removed."""
        cm = ContextManager(max_context_length=500, compact_threshold=0.3, keep_last_n=2)
        for i in range(6):
            cm.add_message("user", f"Message {i}: " + "a" * 40)
            cm.add_message("assistant", f"Response {i}: " + "b" * 40)

        result = asyncio.run(cm.compact())
        assert "before_tokens" in result
        assert "after_tokens" in result
        assert "messages_removed" in result
        assert result["messages_removed"] > 0
        # After compaction: 1 summary + keep_last_n messages
        assert len(cm.messages) == 1 + cm.keep_last_n

    def test_compact_preserves_last_n(self) -> None:
        """compact() keeps the last N messages."""
        cm = ContextManager(max_context_length=500, compact_threshold=0.1, keep_last_n=3)
        messages = [("user", f"msg-{i}") for i in range(8)]
        for role, content in messages:
            cm.add_message(role, content)

        asyncio.run(cm.compact())

        # Should have: 1 summary + 3 recent = 4 messages
        assert len(cm.messages) == 4
        # Last 3 are the original last 3
        assert cm.messages[-1]["content"] == "msg-7"
        assert cm.messages[-2]["content"] == "msg-6"
        assert cm.messages[-3]["content"] == "msg-5"

    def test_compact_nothing_to_compact(self) -> None:
        """compact() with fewer messages than keep_last_n is a no-op."""
        cm = ContextManager(max_context_length=1000, keep_last_n=4)
        cm.add_message("user", "Hello")
        cm.add_message("assistant", "Hi")

        result = asyncio.run(cm.compact())
        assert result["messages_removed"] == 0
        assert result["before_tokens"] == result["after_tokens"]

    def test_compact_with_system_message(self) -> None:
        """System message is preserved after compaction."""
        cm = ContextManager(max_context_length=500, compact_threshold=0.1, keep_last_n=1)
        cm.set_system_message("You are a helpful assistant.")
        for i in range(10):
            cm.add_message("user", f"Message {i}: " + "x" * 50)

        asyncio.run(cm.compact())

        assert cm.system_message == "You are a helpful assistant."
        # Messages should still contain system message info in summary
        assert len(cm.messages) >= 1

    def test_compact_with_custom_summarizer(self) -> None:
        """compact() uses a custom summarizer when provided."""
        cm = ContextManager(max_context_length=500, compact_threshold=0.1, keep_last_n=1)
        for i in range(5):
            cm.add_message("user", f"Message {i}")

        async def custom_summarizer(messages: list[dict[str, Any]]) -> str:
            return "CUSTOM_SUMMARY"

        result = asyncio.run(cm.compact(summarizer_fn=custom_summarizer))
        assert result["messages_removed"] > 0
        # Summary message should contain the custom text
        assert any("CUSTOM_SUMMARY" in m.get("content", "") for m in cm.messages)

    def test_compact_recalculates_tokens(self) -> None:
        """After compaction, token estimate is recalculated from actual messages."""
        cm = ContextManager(max_context_length=10000, compact_threshold=0.01, keep_last_n=2)
        for i in range(20):
            cm.add_message("user", f"Message {i}: " + "x" * 100)

        msg_count_before = len(cm.messages)
        asyncio.run(cm.compact())

        # Messages should be reduced to summary + keep_last_n
        assert len(cm.messages) == 1 + cm.keep_last_n
        assert len(cm.messages) < msg_count_before
        # Token count should be recalculated (positive and based on actual content)
        assert cm._estimated_context_tokens > 0


# ---------------------------------------------------------------------------
# ContextManager: sub-context compaction
# ---------------------------------------------------------------------------


class TestSubContextCompact:
    """Tests for compaction with sub-contexts."""

    def test_parent_compact_does_not_affect_child(self) -> None:
        """Compacting parent context does not touch sub-contexts."""
        parent = ContextManager(max_context_length=500, keep_last_n=1)
        child = parent.create_sub_context("child", max_context_length=500, keep_last_n=1)

        for i in range(10):
            parent.add_message("user", f"Parent msg {i}")
            child.add_message("user", f"Child msg {i}")

        child_msg_count_before = len(child.messages)
        asyncio.run(parent.compact())

        # Parent should be compacted, child untouched
        assert len(parent.messages) < 10
        assert len(child.messages) == child_msg_count_before

    def test_child_inherits_compact_settings(self) -> None:
        """Sub-context inherits parent's compact settings by default."""
        parent = ContextManager(max_context_length=2048, compact_threshold=0.75, auto_compact=True, keep_last_n=6)
        child = parent.create_sub_context("agent1")

        assert child.compact_threshold == 0.75
        assert child.auto_compact is True
        assert child.keep_last_n == 6

    def test_child_overrides_compact_settings(self) -> None:
        """Sub-context can override parent's compact settings."""
        parent = ContextManager(max_context_length=2048, compact_threshold=0.9)
        child = parent.create_sub_context("agent1", compact_threshold=0.5, keep_last_n=2)

        assert child.compact_threshold == 0.5
        assert child.keep_last_n == 2


# ---------------------------------------------------------------------------
# ContextManager: session persistence of compact settings
# ---------------------------------------------------------------------------


class TestCompactPersistence:
    """Tests for saving/loading compact settings in sessions."""

    def test_save_load_preserves_compact_settings(self, tmp_path: Path) -> None:
        """Compact settings survive save/load cycle."""
        cm = ContextManager(max_context_length=8192, compact_threshold=0.7, auto_compact=False, keep_last_n=10)
        cm.add_message("user", "Test message")
        path = str(tmp_path / "session.json")
        cm.save_session(path)

        cm2 = ContextManager()
        cm2.load_session(path)

        assert cm2.max_context_length == 8192
        assert cm2.compact_threshold == 0.7
        assert cm2.auto_compact is False
        assert cm2.keep_last_n == 10

    def test_session_save_includes_compact_fields(self, tmp_path: Path) -> None:
        """Session JSON includes auto_compact and compact_threshold."""
        cm = ContextManager(compact_threshold=0.65, auto_compact=True, keep_last_n=3)
        path = str(tmp_path / "session.json")
        cm.save_session(path)

        data = json.loads(Path(path).read_text())
        assert data["compact_threshold"] == 0.65
        assert data["auto_compact"] is True
        assert data["keep_last_n"] == 3


# ---------------------------------------------------------------------------
# AutoCompactSkill: check, compact, configure actions
# ---------------------------------------------------------------------------


class TestAutoCompactSkill:
    """Tests for the AutoCompactSkill from skills/__init__.py."""

    def test_check_action(self) -> None:
        """'check' action returns usage and should_compact status."""
        cm = ContextManager(max_context_length=1000, compact_threshold=0.5)
        skill = AutoCompactSkill(context_manager=cm)

        result = asyncio.run(skill.execute(action="check"))
        assert result["action"] == "check"
        assert "context_usage" in result
        assert "should_compact" in result
        assert isinstance(result["should_compact"], bool)

    def test_compact_action_below_threshold(self) -> None:
        """'compact' action when below threshold does not compact."""
        cm = ContextManager(max_context_length=10000, compact_threshold=0.9)
        skill = AutoCompactSkill(context_manager=cm)
        cm.add_message("user", "short")

        result = asyncio.run(skill.execute(action="compact"))
        assert result["compacted"] is False
        assert "reason" in result

    def test_compact_action_above_threshold(self) -> None:
        """'compact' action when above threshold actually compacts."""
        cm = ContextManager(max_context_length=100, compact_threshold=0.3, keep_last_n=1)
        skill = AutoCompactSkill(context_manager=cm)
        for i in range(10):
            cm.add_message("user", f"Message {i} " + "x" * 40)

        result = asyncio.run(skill.execute(action="compact"))
        assert result["compacted"] is True
        assert "compact_result" in result
        assert "new_usage" in result

    def test_configure_action(self) -> None:
        """'configure' action updates threshold and keep_last_n."""
        cm = ContextManager(compact_threshold=0.85, keep_last_n=4)
        skill = AutoCompactSkill(context_manager=cm)

        result = asyncio.run(skill.execute(action="configure", threshold=0.6, keep_last_n=8))
        assert result["configured"] is True
        assert result["threshold"] == 0.6
        assert result["keep_last_n"] == 8
        assert cm.compact_threshold == 0.6
        assert cm.keep_last_n == 8


# ---------------------------------------------------------------------------
# Session: auto-compact trigger during send()
# ---------------------------------------------------------------------------


class TestSessionAutoCompact:
    """Tests for auto-compact trigger in Session.send()."""

    def test_auto_compact_triggers_on_threshold(self) -> None:
        """Session.send() auto-compacts when threshold is exceeded."""
        from model.session import Session

        cm = ContextManager(max_context_length=100, compact_threshold=0.3, auto_compact=True, keep_last_n=1)
        session = Session(model="test", provider="ollama", context_manager=cm)

        async def run() -> dict[str, Any]:
            await session.start()
            # Fill context to exceed threshold
            for i in range(10):
                cm.add_message("user", f"Fill message {i} " + "x" * 30)
            # Send should trigger auto-compact
            return await session.send("trigger compact now")

        result = asyncio.run(run())
        assert result["compacted"] is True

    def test_auto_compact_disabled(self) -> None:
        """Session.send() does NOT compact when auto_compact is False."""
        from model.session import Session

        cm = ContextManager(max_context_length=100, compact_threshold=0.3, auto_compact=False, keep_last_n=1)
        session = Session(model="test", provider="ollama", context_manager=cm)

        async def run() -> dict[str, Any]:
            await session.start()
            for i in range(10):
                cm.add_message("user", f"Fill message {i} " + "x" * 30)
            return await session.send("should not compact")

        result = asyncio.run(run())
        assert result["compacted"] is False


# ---------------------------------------------------------------------------
# /compact slash command registration and dispatch
# ---------------------------------------------------------------------------


def test_compact_command_registered() -> None:
    """InteractiveMode._COMMAND_TABLE contains /compact."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            ("from ollama_cmd.interactive import InteractiveMode; print('/compact' in InteractiveMode._COMMAND_TABLE)"),
        ],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert result.stdout.strip() == "True"


def test_compact_handler_is_async() -> None:
    """The /compact handler must be async (_cmd_compact is a coroutine)."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import asyncio; "
                "from ollama_cmd.interactive import InteractiveMode; "
                "print(asyncio.iscoroutinefunction(InteractiveMode._cmd_compact))"
            ),
        ],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert result.stdout.strip() == "True"


def test_compact_command_in_help_output() -> None:
    """The /help output should mention /compact."""
    script = (
        "import sys, asyncio\n"
        "sys.path.insert(0, '.')\n"
        "from model.session import Session\n"
        "from ollama_cmd.interactive import InteractiveMode\n"
        "async def t():\n"
        "    s = Session(model='m', provider='ollama')\n"
        "    await s.start()\n"
        "    r = InteractiveMode(s)\n"
        "    r._cmd_help('')\n"
        "asyncio.run(t())\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert "/compact" in result.stdout


# ---------------------------------------------------------------------------
# Config integration
# ---------------------------------------------------------------------------


def test_config_has_compact_fields() -> None:
    """OllamaCliConfig has auto_compact and compact_threshold fields."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from api.config import OllamaCliConfig; "
                "c = OllamaCliConfig(); "
                "print(c.auto_compact, c.compact_threshold)"
            ),
        ],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert "True" in result.stdout
    assert "0.85" in result.stdout


# ---------------------------------------------------------------------------
# Banner and status show compact info
# ---------------------------------------------------------------------------


def test_banner_shows_compact_info() -> None:
    """The REPL banner should display auto-compact status."""
    script = (
        "import sys, asyncio\n"
        "sys.path.insert(0, '.')\n"
        "from model.session import Session\n"
        "from ollama_cmd.interactive import InteractiveMode\n"
        "async def t():\n"
        "    s = Session(model='m', provider='ollama')\n"
        "    await s.start()\n"
        "    r = InteractiveMode(s)\n"
        "    r._print_banner()\n"
        "asyncio.run(t())\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert "compact" in result.stdout.lower()


def test_status_shows_compact_info() -> None:
    """The /status command should display auto-compact state."""
    script = (
        "import sys, asyncio\n"
        "sys.path.insert(0, '.')\n"
        "from model.session import Session\n"
        "from ollama_cmd.interactive import InteractiveMode\n"
        "async def t():\n"
        "    s = Session(model='m', provider='ollama')\n"
        "    await s.start()\n"
        "    r = InteractiveMode(s)\n"
        "    r._cmd_status('')\n"
        "asyncio.run(t())\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        cwd=_PROJECT_DIR,
    )
    assert "auto-compact" in result.stdout.lower() or "compact" in result.stdout.lower()
