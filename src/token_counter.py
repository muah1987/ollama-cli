#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Token counter utility -- GOTCHA Tools layer, ATLAS Trace phase.

Real-time token tracking with cost estimation. Aggregates prompt and
token counts from various LLM APIs, calculates generation
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
    "anthropic": (3.0, 15.0),
    "gemini": (1.25, 5.0),
    "codex": (2.50, 10.0),
    "openai": (1.0, 2.0),  # Standard GPT-4 pricing
}

# ---------------------------------------------------------------------------
# Provider-specific response extractors
# ---------------------------------------------------------------------------
_EXTRACTORS = {
    "ollama": lambda response: {
        "prompt_tokens": response.get("prompt_eval_count", 0),
        "completion_tokens": response.get("eval_count", 0),
        "duration_ns": response.get("eval_duration", 0),
    },
    "anthropic": lambda response: {
        "prompt_tokens": response.get("usage", {}).get("input_tokens", 0),
        "completion_tokens": response.get("usage", {}).get("output_tokens", 0),
        "duration_ns": response.get("response_ms", 0) * 1_000_000,
    },
    "google": lambda response: {
        "prompt_tokens": response.get("prompt_token_count", 0),
        "completion_tokens": sum(
            c.get("token_count", 0)
            for c in response.get("candidates", [])
        ),
        "duration_ns": response.get("total_latency", 0) * 1_000_000,
    },
    "openai": lambda response: {
        "prompt_tokens": response.get("usage", {}).get("prompt_tokens", 0),
        "completion_tokens": response.get("usage", {}).get("completion_tokens", 0),
        "duration_ns": response.get("request_latency_ms", 0) * 1_000_000,
    },
}

# ---------------------------------------------------------------------------
# TokenCounter
# ---------------------------------------------------------------------------
class TokenCounter:
    """Real-time token counter with cost estimation.

    Tracks prompt and completion tokens across an entire session, computes
    generation speed from API response timing fields, and provides formatted
    display strings for status lines.

    Parameters
    ----------
    provider:
        Provider name used for cost estimation and token extraction (e.g.
        "ollama", "anthropic", "google", "openai"). Defaults to "ollama".
    context_max:
        Maximum context window size in tokens. Used for the context-usage
        display. Defaults to 4096.
    """

    def __init__(
        self,
        provider: str = "ollama",
        context_max: int = 4096,
    ) -> None:
        self.provider = provider
        self.context_max = context_max

        # Running totals
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
        self.tokens_per_second: float = 0.0
        self.context_used: int = 0
        self.cost_estimate: float = 0.0

    # -- public properties ---------------------------------------------------
    @property
    def total_tokens(self) -> int:
        """Combined prompt + completion tokens for the session."""
        return self.prompt_tokens + self.completion_tokens

    # -- public methods ------------------------------------------------------
    def update(self, response: dict[str, Any]) -> None:
        """Update counters from a provider response.

        Automatically selects the correct extraction logic based on provider.
        For new providers, add an extractor to _EXTRACTORS.

        Parameters
        ----------
        response:
            Raw API response from the model provider. Must be formatted
            according to provider-specific requirements.
        """
        extractor = _EXTRACTORS.get(self.provider.lower())
        if not extractor:
            logger.warning(f"No token extractor available for provider: {self.provider}")
            return

        data = extractor(response)
        self.prompt_tokens += data["prompt_tokens"]
        self.completion_tokens += data["completion_tokens"]

        # Calculate tokens per second if duration available
        duration_ns = data.get("duration_ns", 0)
        if duration_ns > 0 and self.completion_tokens > 0:
            self.tokens_per_second = round(
                self.completion_tokens / (duration_ns / 1e9), 2
            )

        # Update context usage from prompt tokens
        if data["prompt_tokens"] > 0:
            self.context_used = data["prompt_tokens"]

        # Recalculate cost
        self.cost_estimate = self._estimate_cost()

    def format_display(self) -> str:
        """Return an ANSI-formatted status string for terminal display.

        Format: [tok: 1,234/4,096 | 42.0 tok/s | $0.02]
        """
        used = f"{self.context_used:,}"
        cap = f"{self.context_max:,}"
        speed = f"{self.tokens_per_second:.1f}"
        cost = f"${self.cost_estimate:.4f}" if self.cost_estimate > 0 else "$0.00"
        return f"[tok: {used}/{cap} | {speed} tok/s | {cost}]"

    def format_json(self) -> dict[str, Any]:
        """Return token metrics as a plain dict for programmatic use."""
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
        """Update context window tracking values."""
        self.context_used = used
        self.context_max = max_tokens

    # -- private helpers -----------------------------------------------------
    def _estimate_cost(self) -> float:
        """Calculate estimated cost based on provider pricing.

        Uses per-million-token rates from _COST_PER_MILLION. Unknown
        providers default to $0.00.
        """
        key = self.provider.lower()
        input_rate, output_rate = _COST_PER_MILLION.get(key, (0.0, 0.0))

        if input_rate == 0.0 and output_rate == 0.0:
            return 0.0

        input_cost = (self.prompt_tokens / 1_000_000) * input_rate
        output_cost = (self.completion_tokens / 1_000_000) * output_rate
        return round(input_cost + output_cost, 6)
"}"