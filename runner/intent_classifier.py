"""
Intent classifier -- GOTCHA Tools layer, ATLAS Trace phase.

Two-tier classification strategy for mapping user prompts to agent types:

**Tier 1 -- Pattern matching (this module):**
    Fast, deterministic classification using a curated registry of keyword and
    multi-word patterns.  Each agent type (code, review, test, debug, plan,
    docs, orchestrator) is associated with a set of patterns.  The prompt is
    scored against every agent type by counting pattern hits, with an early-
    position bonus for matches in the first five words.  The highest-scoring
    type is returned when its normalised confidence meets the threshold.

**Tier 2 -- LLM fallback (external, not in this module):**
    When Tier 1 returns ``agent_type=None`` (confidence below threshold), the
    caller may escalate to a lightweight LLM call for semantic classification.
    This keeps latency low for obvious intents while still handling ambiguous
    prompts gracefully.

Only Python stdlib is used (``re``, ``dataclasses``).  No external dependencies.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pattern registry
# ---------------------------------------------------------------------------

# Maps agent type -> list of keyword / multi-word patterns.
# Single-word patterns are matched with word-boundary regex; multi-word
# patterns use simple substring matching against the lowercased prompt.
PATTERN_REGISTRY: dict[str, list[str]] = {
    "code": [
        "write",
        "implement",
        "create function",
        "add feature",
        "build",
        "code",
        "fix bug",
        "refactor",
        "add endpoint",
        "create class",
        "generate",
        "scaffold",
        "function",
        "method",
        "class",
        "module",
        "api",
        "endpoint",
        "component",
    ],
    "review": [
        "review",
        "check",
        "audit",
        "inspect",
        "analyze code",
        "look at",
        "examine",
        "evaluate quality",
        "code review",
        "pull request",
        "pr review",
    ],
    "test": [
        "test",
        "write tests",
        "add tests",
        "unit test",
        "integration test",
        "coverage",
        "assert",
        "verify behavior",
        "pytest",
        "test case",
        "test suite",
    ],
    "debug": [
        "debug",
        "fix error",
        "traceback",
        "exception",
        "crash",
        "not working",
        "broken",
        "investigate",
        "troubleshoot",
        "stack trace",
        "segfault",
        "error message",
        "why does",
        "fails",
    ],
    "plan": [
        "plan",
        "design",
        "architect",
        "strategy",
        "roadmap",
        "spec",
        "specification",
        "approach",
        "how should",
        "what's the best way",
        "implementation plan",
        "design pattern",
    ],
    "docs": [
        "document",
        "docstring",
        "readme",
        "explain",
        "describe",
        "comment",
        "annotate",
        "documentation",
        "api docs",
        "help text",
        "usage",
    ],
    "orchestrator": [
        "orchestrate",
        "coordinate",
        "multi-step",
        "pipeline",
        "chain",
        "workflow",
        "deploy",
        "ship",
        "release",
        "ci/cd",
        "automate",
        "batch",
    ],
    "team": [
        "complete with team",
        "team planning",
        "complete_w_team",
        "team build",
        "team spec",
        "collaborate",
        "full team",
        "plan and build",
        "plan then build",
        "team loop",
        "agentic loop",
        "multi-agent",
    ],
    "research": [
        "research",
        "compare",
        "summarize",
        "what is",
        "how does",
        "explain how",
        "pros and cons",
        "alternatives",
        "benchmark",
        "evaluate options",
        "best practices",
        "state of the art",
    ],
}

# ---------------------------------------------------------------------------
# IntentResult
# ---------------------------------------------------------------------------


@dataclass
class IntentResult:
    """Result of intent classification for a user prompt.

    Parameters
    ----------
    agent_type:
        The detected agent type (e.g. ``"code"``, ``"debug"``), or ``None``
        if confidence is below the threshold.
    confidence:
        Classification confidence in the range ``[0.0, 1.0]``.
    reasoning:
        Human-readable explanation of why this classification was chosen.
    matched_patterns:
        List of patterns that matched for the winning agent type.
    """

    agent_type: str | None
    confidence: float
    reasoning: str
    matched_patterns: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# IntentClassifier
# ---------------------------------------------------------------------------


class IntentClassifier:
    """Pattern-based intent classifier (Tier 1).

    Scores each agent type by counting pattern matches in the user prompt,
    applying a 2x weight for matches that appear within the first five words.

    Parameters
    ----------
    confidence_threshold:
        Minimum normalised confidence (0.0--1.0) required to return a
        non-None agent type.  Defaults to ``0.7``.
    """

    def __init__(self, confidence_threshold: float = 0.7) -> None:
        self._threshold = confidence_threshold
        self._registry = PATTERN_REGISTRY

        # Pre-compile word-boundary regexes for single-word patterns, and
        # store multi-word patterns as lowercase strings for substring match.
        self._compiled: dict[str, list[tuple[str, re.Pattern[str] | str]]] = {}
        for agent_type, patterns in self._registry.items():
            compiled_patterns: list[tuple[str, re.Pattern[str] | str]] = []
            for pattern in patterns:
                if " " in pattern or "/" in pattern:
                    # Multi-word or special-char pattern -> substring match
                    compiled_patterns.append((pattern, pattern.lower()))
                else:
                    # Single word -> word-boundary regex
                    compiled_patterns.append((pattern, re.compile(rf"\b{re.escape(pattern)}\b", re.IGNORECASE)))
            self._compiled[agent_type] = compiled_patterns

    # -- public API ----------------------------------------------------------

    def classify(self, prompt: str) -> IntentResult:
        """Classify a user prompt into an agent type.

        Parameters
        ----------
        prompt:
            The raw user prompt string.

        Returns
        -------
        An :class:`IntentResult` with the best matching agent type (or
        ``None`` if confidence is below the threshold).
        """
        if not prompt or not prompt.strip():
            return IntentResult(
                agent_type=None,
                confidence=0.0,
                reasoning="Empty prompt cannot be classified.",
                matched_patterns=[],
            )

        prompt_lower = prompt.lower()
        words = re.findall(r"[a-z0-9'/]+", prompt_lower)
        first_five = " ".join(words[:5]) if words else ""

        # Score each agent type.
        scores: dict[str, float] = {}
        matches: dict[str, list[str]] = {}
        first_match_positions: dict[str, int] = {}

        for agent_type, compiled_patterns in self._compiled.items():
            type_score = 0.0
            type_matches: list[str] = []
            earliest_pos: int | None = None

            for pattern_text, matcher in compiled_patterns:
                matched = False
                match_pos: int | None = None

                if isinstance(matcher, re.Pattern):
                    # Single-word: word-boundary regex
                    m = matcher.search(prompt_lower)
                    if m:
                        matched = True
                        match_pos = m.start()
                else:
                    # Multi-word / special: substring match
                    idx = prompt_lower.find(matcher)
                    if idx != -1:
                        matched = True
                        match_pos = idx

                if matched:
                    type_matches.append(pattern_text)
                    weight = 1.0

                    # Early-position bonus: 2x if pattern appears in first 5 words.
                    if isinstance(matcher, re.Pattern):
                        if matcher.search(first_five):
                            weight = 2.0
                    else:
                        if matcher in first_five:
                            weight = 2.0

                    type_score += weight

                    if match_pos is not None and (earliest_pos is None or match_pos < earliest_pos):
                        earliest_pos = match_pos

            scores[agent_type] = type_score
            matches[agent_type] = type_matches
            if earliest_pos is not None:
                first_match_positions[agent_type] = earliest_pos

        # Find the best agent type.
        best_type: str | None = None
        best_score = 0.0

        for agent_type, score in scores.items():
            if score > best_score:
                best_score = score
                best_type = agent_type
            elif score == best_score and score > 0:
                # Tie-breaking: prefer the type whose first match appears
                # earliest in the prompt.
                current_pos = first_match_positions.get(agent_type, len(prompt))
                best_pos = first_match_positions.get(best_type, len(prompt)) if best_type else len(prompt)
                if current_pos < best_pos:
                    best_type = agent_type

        # Normalise confidence: 3+ raw score maps to 1.0.
        confidence = min(1.0, best_score / 3.0) if best_score > 0 else 0.0

        # Apply threshold.
        if confidence < self._threshold:
            return IntentResult(
                agent_type=None,
                confidence=confidence,
                reasoning=(
                    f"No agent type met the confidence threshold ({self._threshold:.1f}). "
                    f"Best candidate was '{best_type}' with confidence {confidence:.2f}."
                ),
                matched_patterns=matches.get(best_type, []) if best_type else [],
            )

        matched_patterns = matches.get(best_type, []) if best_type else []
        reasoning = (
            f"Classified as '{best_type}' with confidence {confidence:.2f} "
            f"based on {len(matched_patterns)} pattern match(es): "
            f"{', '.join(matched_patterns)}."
        )

        logger.debug("Intent: %s (%.2f) -- %s", best_type, confidence, reasoning)

        return IntentResult(
            agent_type=best_type,
            confidence=confidence,
            reasoning=reasoning,
            matched_patterns=matched_patterns,
        )


# ---------------------------------------------------------------------------
# Module-level convenience function
# ---------------------------------------------------------------------------


def classify_intent(prompt: str, threshold: float = 0.7) -> IntentResult:
    """Classify a user prompt into an agent type (convenience wrapper).

    Creates an :class:`IntentClassifier` with the given *threshold* and
    calls :meth:`~IntentClassifier.classify`.

    Parameters
    ----------
    prompt:
        The raw user prompt string.
    threshold:
        Minimum normalised confidence required to return a non-None agent
        type.  Defaults to ``0.7``.

    Returns
    -------
    An :class:`IntentResult`.
    """
    classifier = IntentClassifier(confidence_threshold=threshold)
    return classifier.classify(prompt)


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_prompts = [
        "Write a function to parse JSON",
        "Review the pull request for security issues",
        "Write tests for the authentication module",
        "Debug the crash in the payment handler",
        "Plan the architecture for the new microservice",
        "Document the API endpoints",
        "Orchestrate the deployment pipeline",
        "Complete with team: build a REST API",
        "Research the best practices for error handling",
        "Hello, how are you?",
        "Fix the broken test and refactor the code",
    ]

    classifier = IntentClassifier()
    for p in test_prompts:
        result = classifier.classify(p)
        print(f"  [{result.agent_type or 'None':>13}] ({result.confidence:.2f})  {p}")
        if result.matched_patterns:
            print(f"                patterns: {result.matched_patterns}")
