#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///
"""
Context manager with auto-compact -- GOTCHA Tools layer, ATLAS Architect phase.

Manages conversation history and context window with automatic compaction.
Tracks token usage from Ollama responses and provides session persistence.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ContextManager
# ---------------------------------------------------------------------------


class ContextManager:
    """Manages conversation history, context window usage, and auto-compaction.

    Tracks token consumption from Ollama API responses, estimates context
    window fill level, and automatically compacts the conversation when the
    configured threshold is reached.

    Parameters
    ----------
    max_context_length:
        Maximum context window size in tokens.
    compact_threshold:
        Fraction of context window usage at which compaction triggers (0.0-1.0).
    auto_compact:
        Whether to automatically compact when the threshold is exceeded.
    keep_last_n:
        Number of recent messages to preserve during compaction.
    """

    def __init__(
        self,
        max_context_length: int = 4096,
        compact_threshold: float = 0.85,
        auto_compact: bool = True,
        keep_last_n: int = 4,
    ) -> None:
        self.max_context_length = max_context_length
        self.compact_threshold = compact_threshold
        self.auto_compact = auto_compact
        self.keep_last_n = keep_last_n

        # Conversation state
        self.messages: list[dict[str, Any]] = []
        self.system_message: str | None = None

        # Token metrics (running totals across the session)
        self.total_prompt_tokens: int = 0
        self.total_completion_tokens: int = 0

        # Current context window estimate
        self._estimated_context_tokens: int = 0

        # Latest generation speed
        self._tokens_per_second: float = 0.0

    # -- public methods ------------------------------------------------------

    def add_message(
        self,
        role: str,
        content: str,
        thinking: str | None = None,
        tool_calls: list[Any] | None = None,
    ) -> None:
        """Add a message to the conversation history.

        Parameters
        ----------
        role:
            Message role (``user``, ``assistant``, ``system``, ``tool``).
        content:
            The message text.
        thinking:
            Optional chain-of-thought text (for assistant messages).
        tool_calls:
            Optional list of tool call objects (for assistant messages).
        """
        message: dict[str, Any] = {"role": role, "content": content}
        if thinking is not None:
            message["thinking"] = thinking
        if tool_calls is not None:
            message["tool_calls"] = tool_calls

        self.messages.append(message)
        self._estimated_context_tokens += self._estimate_tokens(content)
        if thinking:
            self._estimated_context_tokens += self._estimate_tokens(thinking)

    def set_system_message(self, content: str) -> None:
        """Set the system prompt.  Always preserved during compaction.

        Parameters
        ----------
        content:
            The system prompt text.
        """
        old_tokens = self._estimate_tokens(self.system_message) if self.system_message else 0
        self.system_message = content
        new_tokens = self._estimate_tokens(content)
        self._estimated_context_tokens += new_tokens - old_tokens

    def get_messages(self, max_tokens: int | None = None) -> list[dict[str, str]]:
        """Return messages formatted for the Ollama API.

        If *max_tokens* is specified, messages are trimmed (oldest first,
        preserving the system message) so that the estimated total fits.

        Parameters
        ----------
        max_tokens:
            Optional token budget.  When ``None``, all messages are returned.

        Returns
        -------
        List of message dicts with ``role`` and ``content`` keys.
        """
        result: list[dict[str, str]] = []

        # System message always comes first
        if self.system_message:
            result.append({"role": "system", "content": self.system_message})

        if max_tokens is None:
            for msg in self.messages:
                result.append({"role": msg["role"], "content": msg["content"]})
            return result

        # Budget-aware message selection: newest messages first
        budget = max_tokens
        if self.system_message:
            budget -= self._estimate_tokens(self.system_message)

        selected: list[dict[str, str]] = []
        for msg in reversed(self.messages):
            cost = self._estimate_tokens(msg["content"])
            if cost > budget:
                break
            selected.append({"role": msg["role"], "content": msg["content"]})
            budget -= cost

        # Restore chronological order and prepend system message
        selected.reverse()
        result.extend(selected)
        return result

    def get_context_usage(self) -> dict[str, Any]:
        """Return current context window usage statistics.

        Returns
        -------
        Dict with ``used``, ``max``, ``percentage``, and ``remaining`` keys.
        """
        used = self._estimated_context_tokens
        remaining = max(0, self.max_context_length - used)
        percentage = (used / self.max_context_length * 100.0) if self.max_context_length > 0 else 0.0
        return {
            "used": used,
            "max": self.max_context_length,
            "percentage": round(percentage, 2),
            "remaining": remaining,
        }

    def should_compact(self) -> bool:
        """Return ``True`` if context usage has reached the compact threshold."""
        if self.max_context_length <= 0:
            return False
        usage_fraction = self._estimated_context_tokens / self.max_context_length
        return usage_fraction >= self.compact_threshold

    async def compact(
        self,
        summarizer_fn: Callable[..., Any] | None = None,
    ) -> dict[str, int]:
        """Compact the conversation to free context space.

        Steps:
        1. Save a snapshot of the pre-compaction state.
        2. Separate and preserve the system message.
        3. Keep the last *keep_last_n* messages.
        4. Summarize older messages (via *summarizer_fn* if provided, otherwise
           simple truncation keeping the first message and last N).
        5. Replace removed messages with a summary message.

        Parameters
        ----------
        summarizer_fn:
            Optional async callable that takes a list of message dicts and
            returns a summary string.  When ``None``, a basic concatenation
            summary is used.

        Returns
        -------
        Dict with ``before_tokens``, ``after_tokens``, and ``messages_removed``.
        """
        before_tokens = self._estimated_context_tokens
        total_messages = len(self.messages)

        # Nothing to compact
        if total_messages <= self.keep_last_n:
            return {"before_tokens": before_tokens, "after_tokens": before_tokens, "messages_removed": 0}

        # Split messages: older ones to summarize, recent ones to keep
        older_messages = self.messages[: total_messages - self.keep_last_n]
        recent_messages = self.messages[total_messages - self.keep_last_n :]

        # Build summary of older messages
        try:
            if summarizer_fn is not None:
                summary_text = await summarizer_fn(older_messages)
            else:
                summary_text = self._simple_summary(older_messages)
        except Exception:
            logger.warning("Summarizer function failed; falling back to simple summary", exc_info=True)
            summary_text = self._simple_summary(older_messages)

        # Replace conversation with summary + recent messages
        summary_message: dict[str, Any] = {
            "role": "system",
            "content": f"Previous conversation summary: {summary_text}",
        }

        self.messages = [summary_message, *recent_messages]

        # Recalculate estimated tokens
        self._recalculate_estimated_tokens()

        after_tokens = self._estimated_context_tokens
        messages_removed = len(older_messages)

        logger.info(
            "Compacted conversation: %d -> %d tokens, %d messages removed",
            before_tokens,
            after_tokens,
            messages_removed,
        )

        return {
            "before_tokens": before_tokens,
            "after_tokens": after_tokens,
            "messages_removed": messages_removed,
        }

    def update_metrics(self, response_metrics: dict[str, Any]) -> None:
        """Update token tracking from an Ollama API response.

        Expects keys from ``OllamaClient.extract_metrics()``:
        ``prompt_eval_count``, ``eval_count``, ``total_duration``,
        ``eval_duration``.

        Parameters
        ----------
        response_metrics:
            Metrics dict extracted from an Ollama response.
        """
        prompt_tokens = response_metrics.get("prompt_eval_count", 0)
        completion_tokens = response_metrics.get("eval_count", 0)
        eval_duration = response_metrics.get("eval_duration", 0)

        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

        # Update context estimate with actual Ollama token count when available
        if prompt_tokens > 0:
            self._estimated_context_tokens = prompt_tokens

        # Calculate tokens per second (Ollama durations are in nanoseconds)
        if eval_duration > 0 and completion_tokens > 0:
            self._tokens_per_second = round(completion_tokens / (eval_duration / 1e9), 2)

    def get_token_metrics(self) -> dict[str, Any]:
        """Return comprehensive token usage metrics.

        Returns
        -------
        Dict with prompt/completion/total tokens, generation speed, and
        context window usage.
        """
        usage = self.get_context_usage()
        return {
            "prompt_tokens": self.total_prompt_tokens,
            "completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
            "tokens_per_second": self._tokens_per_second,
            "context_used": usage["used"],
            "context_max": usage["max"],
            "context_percentage": usage["percentage"],
        }

    def save_session(self, path: str) -> None:
        """Persist the conversation and metrics to a JSON file.

        Parameters
        ----------
        path:
            File path for the session JSON.
        """
        session_data = {
            "system_message": self.system_message,
            "messages": self.messages,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "estimated_context_tokens": self._estimated_context_tokens,
            "tokens_per_second": self._tokens_per_second,
            "max_context_length": self.max_context_length,
            "compact_threshold": self.compact_threshold,
            "auto_compact": self.auto_compact,
            "keep_last_n": self.keep_last_n,
            "saved_at": datetime.now(tz=timezone.utc).isoformat(),
        }

        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(session_data, f, indent=2)
            logger.info("Session saved to %s", path)
        except OSError:
            logger.warning("Failed to save session to %s", path, exc_info=True)

    def load_session(self, path: str) -> None:
        """Restore conversation and metrics from a JSON file.

        Parameters
        ----------
        path:
            File path to the session JSON.
        """
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            logger.warning("Failed to load session from %s", path, exc_info=True)
            return

        self.system_message = data.get("system_message")
        self.messages = data.get("messages", [])
        self.total_prompt_tokens = data.get("total_prompt_tokens", 0)
        self.total_completion_tokens = data.get("total_completion_tokens", 0)
        self._estimated_context_tokens = data.get("estimated_context_tokens", 0)
        self._tokens_per_second = data.get("tokens_per_second", 0.0)
        self.max_context_length = data.get("max_context_length", self.max_context_length)
        self.compact_threshold = data.get("compact_threshold", self.compact_threshold)
        self.auto_compact = data.get("auto_compact", self.auto_compact)
        self.keep_last_n = data.get("keep_last_n", self.keep_last_n)

        logger.info("Session loaded from %s (%d messages)", path, len(self.messages))

    def clear(self) -> None:
        """Reset conversation history, keeping the system message."""
        self.messages.clear()
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self._tokens_per_second = 0.0

        # Recalculate: only system message tokens remain
        self._estimated_context_tokens = 0
        if self.system_message:
            self._estimated_context_tokens = self._estimate_tokens(self.system_message)

    # -- private helpers -----------------------------------------------------

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length.

        Uses the rough approximation of 1 token per 4 characters, which is
        reasonable for English text with most LLM tokenizers.

        Parameters
        ----------
        text:
            The text to estimate.

        Returns
        -------
        Estimated token count (always >= 0).
        """
        if not text:
            return 0
        return max(1, len(text) // 4)

    def _recalculate_estimated_tokens(self) -> None:
        """Recalculate the estimated context token count from all messages."""
        total = 0
        if self.system_message:
            total += self._estimate_tokens(self.system_message)
        for msg in self.messages:
            total += self._estimate_tokens(msg.get("content", ""))
            if "thinking" in msg:
                total += self._estimate_tokens(msg["thinking"])
        self._estimated_context_tokens = total

    @staticmethod
    def _simple_summary(messages: list[dict[str, Any]]) -> str:
        """Build a simple summary by concatenating message snippets.

        Takes the first message in full (to preserve initial context) and
        truncates the rest to keep the summary compact.

        Parameters
        ----------
        messages:
            List of message dicts to summarize.

        Returns
        -------
        A condensed string summary of the conversation.
        """
        if not messages:
            return "No previous conversation."

        parts: list[str] = []
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if i == 0:
                # Keep the first message fully for context
                parts.append(f"[{role}]: {content}")
            else:
                # Truncate subsequent messages to 200 chars
                snippet = content[:200] + ("..." if len(content) > 200 else "")
                parts.append(f"[{role}]: {snippet}")

        return " | ".join(parts)


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def _test() -> None:
        cm = ContextManager(max_context_length=4096, compact_threshold=0.85)
        cm.set_system_message("You are a coding assistant.")
        cm.add_message("user", "Hello, write me a function")
        cm.add_message("assistant", "def hello(): return 'world'")
        print(f"Usage: {cm.get_context_usage()}")
        print(f"Should compact: {cm.should_compact()}")
        print(f"Metrics: {cm.get_token_metrics()}")

    asyncio.run(_test())
