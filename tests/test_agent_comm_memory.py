"""Tests for AgentCommBus and MemoryLayer modules."""

from __future__ import annotations

import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from runner.agent_comm import AgentCommBus
from runner.memory_layer import MemoryLayer

_PROJECT_DIR = str(Path(__file__).resolve().parent.parent)

# ===========================================================================
# AgentCommBus tests
# ===========================================================================


class TestAgentCommBus:
    """Tests for :class:`AgentCommBus`."""

    def test_send_and_receive(self) -> None:
        """Send a message, verify receive gets it."""
        bus = AgentCommBus()
        bus.send("planner", "coder", "Implement the function")
        msgs = bus.receive("coder")
        assert len(msgs) == 1
        assert msgs[0].sender == "planner"
        assert msgs[0].recipient == "coder"
        assert msgs[0].content == "Implement the function"
        assert msgs[0].message_type == "info"

    def test_broadcast(self) -> None:
        """Broadcast reaches all agents except sender."""
        bus = AgentCommBus()
        bus.broadcast("reviewer", "Code review complete")
        # Any agent (except the sender) should see the broadcast
        msgs_coder = bus.receive("coder")
        msgs_planner = bus.receive("planner")
        msgs_reviewer = bus.receive("reviewer")
        assert len(msgs_coder) == 1
        assert len(msgs_planner) == 1
        assert len(msgs_reviewer) == 0  # sender excluded
        assert msgs_coder[0].message_type == "broadcast"

    def test_receive_since(self) -> None:
        """Filter messages by timestamp."""
        bus = AgentCommBus()
        bus.send("a", "b", "first message")
        cutoff = datetime.now(tz=timezone.utc)
        time.sleep(0.01)  # ensure timestamp differs
        bus.send("a", "b", "second message")

        msgs = bus.receive("b", since=cutoff)
        assert len(msgs) == 1
        assert msgs[0].content == "second message"

    def test_get_conversation(self) -> None:
        """Verify bilateral conversation retrieval."""
        bus = AgentCommBus()
        bus.send("planner", "coder", "Please implement")
        bus.send("coder", "planner", "Done")
        bus.send("reviewer", "coder", "Fix the bug")  # should not appear

        convo = bus.get_conversation("planner", "coder")
        assert len(convo) == 2
        assert convo[0].content == "Please implement"
        assert convo[1].content == "Done"

    def test_token_savings(self) -> None:
        """Verify savings calculation."""
        bus = AgentCommBus(context_overhead_multiplier=3)
        bus.send("a", "b", "Hello world")  # ~2 tokens

        savings = bus.get_token_savings()
        assert savings["total_messages"] == 1
        assert savings["direct_tokens"] > 0
        assert savings["context_tokens_saved"] == savings["direct_tokens"] * 2

    def test_clear_specific(self) -> None:
        """Clear one agent's messages only."""
        bus = AgentCommBus()
        bus.send("a", "b", "msg1")
        bus.send("c", "d", "msg2")
        bus.clear("a")

        # Messages involving 'a' should be gone
        assert len(bus.receive("b")) == 0
        # Messages not involving 'a' should remain
        assert bus.get_token_savings()["total_messages"] == 1

    def test_clear_all(self) -> None:
        """Clear everything."""
        bus = AgentCommBus()
        bus.send("a", "b", "msg1")
        bus.send("c", "d", "msg2")
        bus.clear()
        assert bus.get_token_savings()["total_messages"] == 0


# ===========================================================================
# MemoryLayer tests
# ===========================================================================


class TestMemoryLayer:
    """Tests for :class:`MemoryLayer`."""

    def test_store_and_recall(self) -> None:
        """Store, recall, verify content."""
        ml = MemoryLayer()
        ml.store("lang", "Python 3.11+", category="fact", importance=5)
        entry = ml.recall("lang")
        assert entry is not None
        assert entry.content == "Python 3.11+"
        assert entry.category == "fact"
        assert entry.importance == 5

    def test_recall_relevant(self) -> None:
        """Keyword matching returns correct results."""
        ml = MemoryLayer()
        ml.store("python_ver", "Uses Python 3.11", category="fact", importance=5)
        ml.store("theme", "Dark theme preferred", category="preference", importance=2)
        ml.store("api", "REST API at /v1", category="context", importance=4)

        results = ml.recall_relevant("python")
        assert len(results) >= 1
        assert any(e.key == "python_ver" for e in results)

    def test_forget(self) -> None:
        """Remove entry."""
        ml = MemoryLayer()
        ml.store("temp", "temporary data")
        assert ml.forget("temp") is True
        assert ml.recall("temp") is None
        assert ml.forget("nonexistent") is False

    def test_compact(self) -> None:
        """Remove low-priority entries."""
        ml = MemoryLayer(compact_threshold=2.0)
        # importance=1, access_count=0 -> score = 1 * log2(1) = 0 < 2.0
        ml.store("low", "low priority", importance=1)
        # importance=5, access_count=0 -> score = 5 * log2(1) = 0 < 2.0
        ml.store("high", "high priority", importance=5)
        # Boost access so score rises: 5 * log2(4) = 10 >= 2.0
        ml.recall("high")
        ml.recall("high")
        ml.recall("high")

        result = ml.compact()
        assert result["entries_removed"] >= 1
        assert ml.recall("high") is not None

    def test_get_context_block(self) -> None:
        """Token budget respected."""
        ml = MemoryLayer()
        ml.store("a", "short", importance=5)
        ml.store("b", "x" * 2000, importance=5)  # ~500 tokens

        block = ml.get_context_block(max_tokens=50)
        # Should include 'a' but not the long entry 'b'
        assert "short" in block
        tokens = max(1, len(block) // 4)
        assert tokens <= 50

    def test_token_savings(self) -> None:
        """Verify savings calculation."""
        ml = MemoryLayer()
        ml.store("k1", "Some content here", importance=3)
        ml.store("k2", "More content", importance=3)
        stats = ml.get_token_savings()
        assert stats["total_entries"] == 2
        assert stats["total_raw_tokens"] > 0
        assert isinstance(stats["context_tokens_used"], int)
        assert isinstance(stats["tokens_saved"], int)

    def test_save_load(self) -> None:
        """Persistence roundtrip."""
        ml = MemoryLayer()
        ml.store("key1", "value1", category="fact", importance=4)
        ml.store("key2", "value2", category="preference", importance=2)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name

        ml.save(path)

        ml2 = MemoryLayer()
        ml2.load(path)
        entry = ml2.recall("key1")
        assert entry is not None
        assert entry.content == "value1"
        assert entry.category == "fact"
        assert entry.importance == 4

        entry2 = ml2.recall("key2")
        assert entry2 is not None
        assert entry2.content == "value2"

    def test_access_count_updates(self) -> None:
        """Recall increments access_count."""
        ml = MemoryLayer()
        ml.store("item", "data")
        assert ml.recall("item").access_count == 1
        assert ml.recall("item").access_count == 2
        assert ml.recall("item").access_count == 3

    def test_importance_scoring(self) -> None:
        """Higher importance memories appear first in context."""
        ml = MemoryLayer()
        ml.store("low", "low importance", importance=1)
        ml.store("high", "high importance", importance=5)
        # Recall both once to give them the same access_count
        ml.recall("low")
        ml.recall("high")

        block = ml.get_context_block(max_tokens=500)
        # High importance should appear before low importance
        high_pos = block.find("high importance")
        low_pos = block.find("low importance")
        assert high_pos < low_pos


# ===========================================================================
# Integration tests
# ===========================================================================


class TestSessionIntegration:
    """Integration tests for Session with AgentCommBus and MemoryLayer."""

    def test_session_has_agent_comm(self) -> None:
        """Session creates AgentCommBus."""
        from model.session import Session

        session = Session(model="test", provider="ollama")
        assert hasattr(session, "agent_comm")
        assert isinstance(session.agent_comm, AgentCommBus)

    def test_session_has_memory_layer(self) -> None:
        """Session creates MemoryLayer."""
        from model.session import Session

        session = Session(model="test", provider="ollama")
        assert hasattr(session, "memory_layer")
        assert isinstance(session.memory_layer, MemoryLayer)

    def test_status_includes_agent_comm(self) -> None:
        """Status shows comm stats."""
        from model.session import Session

        session = Session(model="test", provider="ollama")
        status = session.get_status()
        assert "agent_comm" in status
        assert "total_messages" in status["agent_comm"]
        assert "context_tokens_saved" in status["agent_comm"]

    def test_status_includes_memory(self) -> None:
        """Status shows memory stats."""
        from model.session import Session

        session = Session(model="test", provider="ollama")
        status = session.get_status()
        assert "memory" in status
        assert "total_entries" in status["memory"]
        assert "total_raw_tokens" in status["memory"]
        assert "context_tokens_used" in status["memory"]
        assert "tokens_saved" in status["memory"]


class TestInteractiveCommands:
    """Integration tests for InteractiveMode new commands."""

    def test_interactive_agents_command(self) -> None:
        """/agents is registered."""
        import subprocess

        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.');\n"
             "from ollama_cmd.interactive import InteractiveMode\n"
             "assert '/agents' in InteractiveMode._COMMAND_TABLE\n"
             "assert InteractiveMode._COMMAND_TABLE['/agents'] == '_cmd_agents'\n"
             "print('OK')"],
            capture_output=True, text=True, cwd=_PROJECT_DIR,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_interactive_remember_command(self) -> None:
        """/remember is registered."""
        import subprocess

        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.');\n"
             "from ollama_cmd.interactive import InteractiveMode\n"
             "assert '/remember' in InteractiveMode._COMMAND_TABLE\n"
             "assert InteractiveMode._COMMAND_TABLE['/remember'] == '_cmd_remember'\n"
             "print('OK')"],
            capture_output=True, text=True, cwd=_PROJECT_DIR,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_interactive_recall_command(self) -> None:
        """/recall is registered."""
        import subprocess

        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, '.');\n"
             "from ollama_cmd.interactive import InteractiveMode\n"
             "assert '/recall' in InteractiveMode._COMMAND_TABLE\n"
             "assert InteractiveMode._COMMAND_TABLE['/recall'] == '_cmd_recall'\n"
             "print('OK')"],
            capture_output=True, text=True, cwd=_PROJECT_DIR,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout
