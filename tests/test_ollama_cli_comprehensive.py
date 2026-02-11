"""
Comprehensive tests for Ollama CLI components.
"""
import asyncio
import json
import sys
import tempfile
from pathlib import Path

import pytest

# Add ollama-cli/src to path so we can import our modules
ollama_src_path = str(Path(__file__).parent.parent / "ollama-cli" / "src")
if ollama_src_path not in sys.path:
    sys.path.insert(0, ollama_src_path)

from context_manager import ContextManager
from token_counter import TokenCounter
from session import Session


class TestTokenCounterComprehensive:
    """Comprehensive tests for TokenCounter with all providers."""

    def test_ollama_provider(self):
        """Test token counter with Ollama provider."""
        tc = TokenCounter(provider="ollama")
        assert tc.provider == "ollama"
        assert tc.context_max == 4096

    def test_anthropic_provider(self):
        """Test token counter with Anthropic (Claude) provider."""
        tc = TokenCounter(provider="anthropic")
        assert tc.provider == "anthropic"

        # Test cost estimation for Anthropic
        tc.prompt_tokens = 1000000  # 1M tokens
        tc.completion_tokens = 1000000  # 1M tokens
        cost = tc._estimate_cost()
        # Anthropic pricing: $3.00/input million, $15.00/output million
        assert cost == 18.0  # (1 * 3) + (1 * 15)

    def test_openai_provider(self):
        """Test token counter with OpenAI provider."""
        tc = TokenCounter(provider="openai")
        assert tc.provider == "openai"

        # Test cost estimation for OpenAI
        tc.prompt_tokens = 1000000  # 1M tokens
        tc.completion_tokens = 1000000  # 1M tokens
        cost = tc._estimate_cost()
        # OpenAI pricing: $1.00/input million, $2.00/output million
        assert cost == 3.0  # (1 * 1) + (1 * 2)

    def test_update_with_ollama_response(self):
        """Test updating token counter with Ollama response metrics."""
        tc = TokenCounter(provider="ollama")
        metrics = {
            "prompt_eval_count": 128,
            "eval_count": 256,
            "eval_duration": 5000000000,  # 5 seconds in nanoseconds
        }

        tc.update(metrics)

        assert tc.prompt_tokens == 128
        assert tc.completion_tokens == 256
        assert tc.tokens_per_second == 51.2  # 256 tokens / 5 seconds

    def test_update_with_anthropic_response(self):
        """Test updating token counter with Anthropic (Claude) response metrics."""
        tc = TokenCounter(provider="anthropic")
        metrics = {
            "usage": {
                "input_tokens": 5000,
                "output_tokens": 1000
            },
            "response_ms": 2000  # 2 seconds
        }

        tc.update(metrics)

        assert tc.prompt_tokens == 5000
        assert tc.completion_tokens == 1000
        assert tc.tokens_per_second == 500.0  # 1000 tokens / 2 seconds

    def test_format_display(self):
        """Test formatting display string."""
        tc = TokenCounter(provider="anthropic", context_max=200000)
        tc.prompt_tokens = 5000
        tc.completion_tokens = 1000
        tc.tokens_per_second = 42.0
        tc.context_used = 5000

        display = tc.format_display()
        assert "[tok:" in display
        assert "5,000/200,000" in display
        assert "42.0 tok/s" in display

    def test_format_json(self):
        """Test formatting JSON output."""
        tc = TokenCounter(provider="google")
        tc.prompt_tokens = 1000
        tc.completion_tokens = 500
        tc.tokens_per_second = 25.0
        tc.context_used = 1000
        tc.context_max = 4096
        tc.cost_estimate = 0.0123

        result = tc.format_json()
        assert result["prompt_tokens"] == 1000
        assert result["completion_tokens"] == 500
        assert result["total_tokens"] == 1500
        assert result["tokens_per_second"] == 25.0
        assert result["context_used"] == 1000
        assert result["context_max"] == 4096
        assert result["cost_estimate"] == 0.0123
        assert result["provider"] == "google"


class TestContextManagerComprehensive:
    """Comprehensive tests for ContextManager."""

    def test_init(self):
        """Test ContextManager initialization."""
        cm = ContextManager(
            max_context_length=8192,
            compact_threshold=0.9,
            auto_compact=False,
            keep_last_n=6
        )

        assert cm.max_context_length == 8192
        assert cm.compact_threshold == 0.9
        assert cm.auto_compact is False
        assert cm.keep_last_n == 6

    def test_add_message(self):
        """Test adding messages to context."""
        cm = ContextManager()
        cm.add_message("user", "Hello, world!")
        cm.add_message("assistant", "Hello!", thinking="Processing user greeting")

        assert len(cm.messages) == 2
        assert cm.messages[0]["role"] == "user"
        assert cm.messages[0]["content"] == "Hello, world!"
        assert cm.messages[1]["role"] == "assistant"
        assert cm.messages[1]["content"] == "Hello!"
        assert cm.messages[1]["thinking"] == "Processing user greeting"

    def test_set_system_message(self):
        """Test setting system message."""
        cm = ContextManager()
        cm.set_system_message("You are a helpful assistant.")

        assert cm.system_message == "You are a helpful assistant."

    def test_should_compact(self):
        """Test compaction threshold checking."""
        cm = ContextManager(max_context_length=1000, compact_threshold=0.8)

        # Add messages that use 850 tokens
        cm._estimated_context_tokens = 850

        assert cm.should_compact() is True

        # Reduce to 750 tokens
        cm._estimated_context_tokens = 750

        assert cm.should_compact() is False

    def test_update_metrics(self):
        """Test updating token metrics."""
        cm = ContextManager()
        metrics = {
            "prompt_eval_count": 100,
            "eval_count": 50,
            "eval_duration": 1000000000,  # 1 second
        }

        cm.update_metrics(metrics)

        assert cm.total_prompt_tokens == 100
        assert cm.total_completion_tokens == 50
        assert cm._tokens_per_second == 50.0  # 50 tokens / 1 second

    def test_get_token_metrics(self):
        """Test getting token metrics."""
        cm = ContextManager(max_context_length=4096)
        cm._estimated_context_tokens = 500
        cm.total_prompt_tokens = 1000
        cm.total_completion_tokens = 500
        cm._tokens_per_second = 25.0

        metrics = cm.get_token_metrics()

        assert metrics["prompt_tokens"] == 1000
        assert metrics["completion_tokens"] == 500
        assert metrics["total_tokens"] == 1500
        assert metrics["tokens_per_second"] == 25.0
        assert metrics["context_used"] == 500
        assert metrics["context_max"] == 4096
        assert metrics["context_percentage"] == 12.21  # (500/4096)*100 rounded

    def test_save_and_load_session(self):
        """Test saving and loading session data."""
        cm = ContextManager(context_id="test_session")
        cm.set_system_message("Test system message")
        cm.add_message("user", "Test message")
        cm.add_message("assistant", "Test response")

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_path = f.name

        try:
            cm.save_session(temp_path)

            # Load session back
            new_cm = ContextManager()
            new_cm.load_session(temp_path)

            assert new_cm.context_id == "test_session"
            assert new_cm.system_message == "Test system message"
            assert len(new_cm.messages) == 2
            assert new_cm.messages[0]["content"] == "Test message"
            assert new_cm.messages[1]["content"] == "Test response"

        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestSessionComprehensive:
    """Comprehensive tests for Session."""

    def test_init(self):
        """Test Session initialization."""
        session = Session(
            session_id="test123",
            model="llama3.2",
            provider="anthropic"
        )

        assert session.session_id == "test123"
        assert session.model == "llama3.2"
        assert session.provider == "anthropic"
        assert isinstance(session.context_manager, ContextManager)
        assert isinstance(session.token_counter, TokenCounter)

    def test_get_status(self):
        """Test getting session status."""
        session = Session()

        status = session.get_status()

        assert "session_id" in status
        assert "model" in status
        assert "provider" in status
        assert "uptime_seconds" in status
        assert "messages" in status
        assert "token_metrics" in status
        assert "context_usage" in status


if __name__ == "__main__":
    pytest.main([__file__])