#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Token counter utility -- GOTCHA Tools layer, ATLAS Trace phase.

Real-time token tracking with cost estimation.  Aggregates prompt and
completion token counts from Ollama API responses, calculates generation
speed, and provides formatted display strings for status lines.
"""

from __future__ import annotations

import logging
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cost tables (USD per 1M tokens: input / output)
# ---------------------------------------------------------------------------

_COST_PER_MILLION: dict[str, tuple[float, float]] = {
    "ollama": (0.0, 0.0),
    "claude": (3.0, 15.0),
    "gemini": (1.25, 5.0),
    "codex": (2.50, 10.0),
}

# ---------------------------------------------------------------------------
# TokenCounter
# ---------------------------------------------------------------------------


class TokenCounter:
    """Real-time token counter with cost estimation.

    Tracks prompt and completion tokens across an entire session, computes
    generation speed from Ollama timing fields, and estimates cost based on
    the active provider's pricing.

    Parameters
    ----------
    provider:
        Provider name used for cost estimation (``ollama``, ``claude``,
        ``gemini``, ``codex``).  Defaults to ``ollama``.
    context_max:
        Maximum context window size in tokens.  Used for the context-usage
        display.  Defaults to ``4096``.
    """

    def __init__(
        self,
        provider: str = "ollama",
        context_max: int = 4096,
    ) -> None:
        self.provider = provider

        # Running totals
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.tokens_per_second: float = 0.0

        # Context window tracking
        self.context_used: int = 0
        self.context_max: int = context_max

        # Accumulated cost
        self.cost_estimate: float = 0.0

    # -- public properties ---------------------------------------------------

    @property
    def total_tokens(self) -> int:
        """Combined prompt + completion tokens for the session."""
        return self.prompt_tokens + self.completion_tokens

    # -- public methods ------------------------------------------------------

    def update(self, response_metrics: dict[str, Any]) -> None:
        """Update counters from an Ollama API response metrics dict.

        Expects the dict returned by ``OllamaClient.extract_metrics()``,
        containing ``prompt_eval_count``, ``eval_count``, ``eval_duration``,
        and ``total_duration``.

        Parameters
        ----------
        response_metrics:
            Metrics dict extracted from an Ollama response.
        """
        prompt = response_metrics.get("prompt_eval_count", 0)
        completion = response_metrics.get("eval_count", 0)
        eval_duration = response_metrics.get("eval_duration", 0)

        self.prompt_tokens += prompt
        self.completion_tokens += completion

        # Ollama reports durations in nanoseconds
        if eval_duration > 0 and completion > 0:
            self.tokens_per_second = round(completion / (eval_duration / 1e9), 2)

        # Update context-used to reflect the latest prompt size
        if prompt > 0:
            self.context_used = prompt

        # Recalculate cost
        self.cost_estimate = self._estimate_cost(self.provider)

    def format_display(self) -> str:
        """Return an ANSI-formatted status string for terminal display.

        Format: ``[tok: 1,234/4,096 | 42.0 tok/s | $0.02]``

        Returns
        -------
        Formatted string suitable for embedding in a Rich or ANSI status bar.
        """
        used = f"{self.context_used:,}"
        cap = f"{self.context_max:,}"
        speed = f"{self.tokens_per_second:.1f}"
        cost = f"${self.cost_estimate:.4f}" if self.cost_estimate > 0 else "$0.00"
        return f"[tok: {used}/{cap} | {speed} tok/s | {cost}]"

    def format_json(self) -> dict[str, Any]:
        """Return token metrics as a plain dict for programmatic use.

        Returns
        -------
        Dict with all counter values, speed, context info, and cost.
        """
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "tokens_per_second": self.tokens_per_second,
            "context_used": self.context_used,
            "context_max": self.context_max,
            "cost_estimate": round(self.cost_estimate, 6),
            "provider": self.provider,
        }

    def reset(self) -> None:
        """Reset all counters to zero."""
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.tokens_per_second = 0.0
        self.context_used = 0
        self.cost_estimate = 0.0

    def set_context(self, used: int, max_tokens: int) -> None:
        """Update context window tracking values.

        Parameters
        ----------
        used:
            Current number of tokens in the context window.
        max_tokens:
            Maximum context window size.
        """
        self.context_used = used
        self.context_max = max_tokens

    # -- private helpers -----------------------------------------------------

    def _estimate_cost(self, provider: str) -> float:
        """Calculate estimated cost based on provider pricing.

        Uses per-million-token rates from ``_COST_PER_MILLION``.  Unknown
        providers default to $0.00.

        Parameters
        ----------
        provider:
            Provider name (case-insensitive).

        Returns
        -------
        Estimated cost in USD.
        """
        key = provider.lower()
        input_rate, output_rate = _COST_PER_MILLION.get(key, (0.0, 0.0))

        if input_rate == 0.0 and output_rate == 0.0:
            return 0.0

        input_cost = (self.prompt_tokens / 1_000_000) * input_rate
        output_cost = (self.completion_tokens / 1_000_000) * output_rate
        return round(input_cost + output_cost, 6)


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tc = TokenCounter(provider="ollama", context_max=4096)

    # Simulate an Ollama response
    tc.update({
        "prompt_eval_count": 128,
        "eval_count": 256,
        "eval_duration": 5_000_000_000,  # 5 seconds in nanoseconds
        "total_duration": 6_000_000_000,
    })

    print(f"Display: {tc.format_display()}")
    print(f"Total tokens: {tc.total_tokens}")
    print(f"JSON: {tc.format_json()}")

    # Simulate with Claude pricing
    tc_cloud = TokenCounter(provider="claude", context_max=200_000)
    tc_cloud.update({
        "prompt_eval_count": 5000,
        "eval_count": 1000,
        "eval_duration": 2_000_000_000,
        "total_duration": 3_000_000_000,
    })
    print(f"\nClaude display: {tc_cloud.format_display()}")
    print(f"Claude JSON: {tc_cloud.format_json()}")
