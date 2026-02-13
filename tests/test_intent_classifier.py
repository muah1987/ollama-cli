"""Tests for the intent classifier module.

Tests cover:
1. Pattern matching for each of the 7 agent types
2. Confidence scoring mechanics (normalization, early-position bonus)
3. Threshold behavior at various levels
4. Edge cases (empty input, ambiguous prompts, short prompts)
5. IntentResult dataclass field validation
6. classify_intent convenience function
"""

import pytest  # type: ignore[import-untyped]
from runner.intent_classifier import IntentClassifier, IntentResult, classify_intent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify(prompt: str, threshold: float = 0.7) -> IntentResult:
    """Shorthand for creating a classifier and classifying a prompt."""
    return IntentClassifier(confidence_threshold=threshold).classify(prompt)


# ---------------------------------------------------------------------------
# 1. Pattern matching per agent type
# ---------------------------------------------------------------------------


class TestPatternMatching:
    """Verify that prompts with clear intent map to the correct agent type.

    The classifier requires multiple pattern hits (or high-weight hits) to
    reach the default 0.7 confidence threshold.  Each parametrized prompt is
    crafted to trigger at least two patterns for the target agent type so
    that the normalised score exceeds the threshold.
    """

    # -- code ---------------------------------------------------------------

    @pytest.mark.parametrize(
        "prompt",
        [
            "write a function that reverses a string",
            "implement a REST API endpoint",
            "create class for user authentication",
            "refactor the module to use dependency injection",
            "build a component and add an endpoint",
            "code a module with a class and method",
        ],
    )
    def test_code_agent(self, prompt: str) -> None:
        result = _classify(prompt)
        assert result.agent_type == "code", (
            f"Expected 'code' for {prompt!r}, got {result.agent_type!r} "
            f"(confidence={result.confidence:.2f}, patterns={result.matched_patterns})"
        )

    # -- review -------------------------------------------------------------

    @pytest.mark.parametrize(
        "prompt",
        [
            "check the pull request changes",
            "do a code review of the utils package",
            "review and inspect the code for issues",
            "audit and examine the module carefully",
            "check and analyze code for bugs",
        ],
    )
    def test_review_agent(self, prompt: str) -> None:
        result = _classify(prompt)
        assert result.agent_type == "review", (
            f"Expected 'review' for {prompt!r}, got {result.agent_type!r} "
            f"(confidence={result.confidence:.2f}, patterns={result.matched_patterns})"
        )

    # -- test ---------------------------------------------------------------

    @pytest.mark.parametrize(
        "prompt",
        [
            "add unit test for the parser",
            "increase test coverage for utils",
            "add tests for the payment handler with pytest",
            "create a test suite for the API client",
            "write tests and add test coverage",
            "test the module and add pytest cases",
        ],
    )
    def test_test_agent(self, prompt: str) -> None:
        result = _classify(prompt)
        assert result.agent_type == "test", (
            f"Expected 'test' for {prompt!r}, got {result.agent_type!r} "
            f"(confidence={result.confidence:.2f}, patterns={result.matched_patterns})"
        )

    # -- debug --------------------------------------------------------------

    @pytest.mark.parametrize(
        "prompt",
        [
            "debug the crash in the payment handler",
            "investigate why the API is not working",
            "troubleshoot the segfault in the worker process",
            "debug the crash and fix error",
            "investigate the exception and troubleshoot",
            "the traceback shows a crash, debug it",
        ],
    )
    def test_debug_agent(self, prompt: str) -> None:
        result = _classify(prompt)
        assert result.agent_type == "debug", (
            f"Expected 'debug' for {prompt!r}, got {result.agent_type!r} "
            f"(confidence={result.confidence:.2f}, patterns={result.matched_patterns})"
        )

    # -- plan ---------------------------------------------------------------

    @pytest.mark.parametrize(
        "prompt",
        [
            "design a caching strategy",
            "plan the design and strategy for the feature",
            "architect the approach and write a spec",
            "design a roadmap and plan for the release",
        ],
    )
    def test_plan_agent(self, prompt: str) -> None:
        result = _classify(prompt)
        assert result.agent_type == "plan", (
            f"Expected 'plan' for {prompt!r}, got {result.agent_type!r} "
            f"(confidence={result.confidence:.2f}, patterns={result.matched_patterns})"
        )

    # -- docs ---------------------------------------------------------------

    @pytest.mark.parametrize(
        "prompt",
        [
            "describe the usage of the CLI tool",
            "document and explain the API",
            "add docstring and describe the usage",
            "document the readme and usage instructions",
        ],
    )
    def test_docs_agent(self, prompt: str) -> None:
        result = _classify(prompt)
        assert result.agent_type == "docs", (
            f"Expected 'docs' for {prompt!r}, got {result.agent_type!r} "
            f"(confidence={result.confidence:.2f}, patterns={result.matched_patterns})"
        )

    # -- orchestrator -------------------------------------------------------

    @pytest.mark.parametrize(
        "prompt",
        [
            "orchestrate the deployment pipeline",
            "automate the CI/CD workflow",
            "coordinate the multi-step release process",
            "set up the deployment pipeline and ship it",
            "chain together the build, test, and deploy steps",
            "automate the workflow and deploy the release",
        ],
    )
    def test_orchestrator_agent(self, prompt: str) -> None:
        result = _classify(prompt)
        assert result.agent_type == "orchestrator", (
            f"Expected 'orchestrator' for {prompt!r}, got {result.agent_type!r} "
            f"(confidence={result.confidence:.2f}, patterns={result.matched_patterns})"
        )

    # -- matched_patterns populated -----------------------------------------

    def test_matched_patterns_populated(self) -> None:
        """The matched_patterns list should contain the actual patterns that hit."""
        result = _classify("write a function and implement a method")
        assert result.agent_type == "code"
        assert len(result.matched_patterns) >= 2
        assert "write" in result.matched_patterns
        assert "implement" in result.matched_patterns

    def test_reasoning_contains_agent_type(self) -> None:
        """Reasoning string should reference the chosen agent type."""
        result = _classify("debug the crash and investigate the traceback")
        assert result.agent_type == "debug"
        assert "debug" in result.reasoning.lower()


# ---------------------------------------------------------------------------
# 1b. Single-keyword pattern matching (lower threshold)
# ---------------------------------------------------------------------------


class TestSingleKeywordPatternMatching:
    """Verify that prompts with a single strong keyword classify correctly
    when the threshold is lowered.

    A single keyword in the first 5 words produces raw_score=2.0 which
    normalises to 0.667, below the default 0.7 threshold.  Using
    threshold=0.5 lets us verify pattern matching in isolation.
    """

    @pytest.mark.parametrize(
        ("prompt", "expected"),
        [
            ("build a CLI tool for data migration", "code"),
            ("scaffold a new microservice project", "code"),
            ("review the authentication module", "review"),
            ("audit this code for security issues", "review"),
            ("examine the database query performance", "review"),
            ("plan the architecture for microservices", "plan"),
            ("document the API endpoints", "docs"),
            ("explain how the routing works", "docs"),
            ("add a docstring to the utils function", "docs"),
        ],
    )
    def test_single_keyword_with_low_threshold(
        self, prompt: str, expected: str
    ) -> None:
        """With threshold=0.5 a single early keyword should be enough."""
        result = _classify(prompt, threshold=0.5)
        assert result.agent_type == expected, (
            f"Expected {expected!r} for {prompt!r}, got {result.agent_type!r} "
            f"(confidence={result.confidence:.2f}, patterns={result.matched_patterns})"
        )


# ---------------------------------------------------------------------------
# 2. Confidence scoring
# ---------------------------------------------------------------------------


class TestConfidenceScoring:
    """Verify confidence calculation: normalization, bonuses, and ranges."""

    def test_high_confidence_multiple_keywords(self) -> None:
        """A prompt with many matching keywords should score high confidence."""
        result = _classify("write a function, implement a method, and build a class")
        assert result.confidence > 0.7
        assert result.agent_type == "code"

    def test_low_confidence_single_keyword(self) -> None:
        """A prompt with a single keyword not in the first 5 words scores low."""
        result = _classify("I was thinking about maybe discussing a class sometime")
        # "class" is not in first 5 words -> weight 1.0 -> 1.0/3.0 = 0.333
        assert result.confidence <= 0.7

    def test_single_early_keyword_confidence(self) -> None:
        """A single keyword in the first 5 words gives confidence ~0.667."""
        result = _classify("review the authentication module")
        # "review" at position 0 -> weight 2.0 -> 2.0/3.0 ~ 0.667
        assert 0.6 < result.confidence < 0.7

    def test_confidence_clamped_to_one(self) -> None:
        """Confidence should never exceed 1.0 even with many matches."""
        result = _classify(
            "write implement build code refactor generate scaffold function method class"
        )
        assert result.confidence <= 1.0

    def test_confidence_exactly_one_with_enough_matches(self) -> None:
        """A prompt with 3+ raw score should have confidence exactly 1.0."""
        result = _classify(
            "write implement build code refactor generate scaffold function method class"
        )
        assert result.confidence == 1.0

    def test_confidence_zero_for_empty(self) -> None:
        """Empty prompts get confidence 0.0."""
        result = _classify("")
        assert result.confidence == 0.0

    def test_early_position_bonus(self) -> None:
        """Keywords in the first 5 words should receive a 2x weight bonus."""
        # "write" is the very first word -> 2x bonus -> raw 2.0
        early = _classify("write something for me please")
        # "write" appears after 7 words -> no bonus -> raw 1.0
        late = _classify(
            "I would really appreciate it if you could write something"
        )
        assert early.confidence > late.confidence, (
            f"Early ({early.confidence:.2f}) should beat late ({late.confidence:.2f})"
        )

    def test_early_position_bonus_multi_word(self) -> None:
        """Multi-word patterns also get the 2x early-position bonus."""
        # "fix bug" appears in first five words' substring
        early = _classify("fix bug in the login handler")
        # "fix bug" is pushed past the first five words
        late = _classify(
            "I have a problem and I need you to fix bug in the handler"
        )
        assert early.confidence >= late.confidence

    def test_normalization_formula(self) -> None:
        """Confidence = min(1.0, raw_score / 3.0). Verify directly."""
        # "debug" matches at position 0, with early bonus -> weight 2.0
        # No other debug patterns match -> raw_score = 2.0
        # Normalised: 2.0 / 3.0 ~ 0.6667
        result = _classify("debug something for me")
        assert abs(result.confidence - 2.0 / 3.0) < 0.01, (
            f"Expected ~0.667, got {result.confidence:.4f}"
        )

    def test_late_keyword_no_bonus(self) -> None:
        """A keyword outside the first 5 words gets weight 1.0, not 2.0."""
        result = _classify(
            "I was thinking about maybe discussing debug later"
        )
        # "debug" is word index 6+ -> weight 1.0 -> raw 1.0 -> conf 0.333
        assert abs(result.confidence - 1.0 / 3.0) < 0.01


# ---------------------------------------------------------------------------
# 3. Threshold behavior
# ---------------------------------------------------------------------------


class TestThresholdBehavior:
    """Verify that the confidence threshold gates agent_type assignment."""

    def test_default_threshold_rejects_low_confidence(self) -> None:
        """At the default 0.7, a single-keyword prompt (conf ~0.667) is rejected."""
        result = _classify("plan something", threshold=0.7)
        assert result.agent_type is None
        assert result.confidence < 0.7

    def test_low_threshold_accepts_weak_match(self) -> None:
        """At threshold=0.3, even a single keyword in first 5 words passes."""
        result = _classify("plan something", threshold=0.3)
        assert result.agent_type == "plan"
        assert result.confidence >= 0.3

    def test_very_high_threshold_rejects_most(self) -> None:
        """At threshold=1.0, a two-match prompt (conf ~0.667) is rejected."""
        result = _classify("review and check the code", threshold=1.0)
        if result.confidence < 1.0:
            assert result.agent_type is None

    def test_high_threshold_passes_with_many_matches(self) -> None:
        """A prompt with many matches should pass even a high threshold."""
        result = _classify(
            "debug the crash, investigate the traceback, troubleshoot the exception",
            threshold=0.9,
        )
        assert result.agent_type == "debug"
        assert result.confidence >= 0.9

    def test_threshold_zero_accepts_any_match(self) -> None:
        """At threshold=0.0, any non-zero score should yield an agent type."""
        result = _classify("hello world build", threshold=0.0)
        assert result.agent_type is not None

    def test_below_threshold_reasoning_mentions_threshold(self) -> None:
        """When below threshold, reasoning should mention the threshold value."""
        result = _classify("plan something", threshold=0.7)
        assert result.agent_type is None
        assert "0.7" in result.reasoning

    def test_below_threshold_still_has_matched_patterns(self) -> None:
        """Even when below threshold, matched_patterns should be populated."""
        result = _classify("plan something", threshold=0.7)
        assert result.agent_type is None
        assert len(result.matched_patterns) > 0
        assert "plan" in result.matched_patterns

    def test_exact_threshold_boundary(self) -> None:
        """A prompt scoring exactly at the threshold should be accepted.

        Two keywords, both in early position: raw = 2.0 + 2.0 = 4.0,
        normalised = min(1.0, 4.0/3.0) = 1.0.  Threshold 1.0 -> accepted.
        """
        result = _classify("debug the crash now", threshold=1.0)
        # "debug" (2.0) + "crash" (2.0) = 4.0 -> conf 1.0 >= threshold 1.0
        assert result.agent_type == "debug"
        assert result.confidence >= 1.0

    def test_threshold_just_above_rejects(self) -> None:
        """Confirm a single early keyword (conf 0.667) is rejected at 0.68."""
        result = _classify("debug something", threshold=0.68)
        assert result.agent_type is None


# ---------------------------------------------------------------------------
# 4. Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Boundary conditions and unusual inputs."""

    def test_empty_string(self) -> None:
        result = _classify("")
        assert result.agent_type is None
        assert result.confidence == 0.0
        assert result.matched_patterns == []

    def test_whitespace_only(self) -> None:
        result = _classify("   \t\n  ")
        assert result.agent_type is None
        assert result.confidence == 0.0

    def test_very_short_prompt_hi(self) -> None:
        result = _classify("hi")
        assert result.agent_type is None

    def test_very_short_prompt_hello(self) -> None:
        result = _classify("hello")
        assert result.agent_type is None

    def test_general_chat(self) -> None:
        result = _classify("what is the meaning of life")
        assert result.agent_type is None

    def test_no_pattern_match_gives_zero_confidence(self) -> None:
        """A prompt with zero pattern matches should have confidence 0.0."""
        result = _classify("just chatting about nothing relevant")
        assert result.confidence == 0.0
        assert result.agent_type is None

    def test_mixed_intent_picks_one(self) -> None:
        """When a prompt mixes intents, the classifier picks one winner."""
        # Use low threshold so the mixed prompt actually classifies.
        result = _classify("fix the bug and write tests", threshold=0.5)
        assert result.agent_type in {"debug", "test", "code"}
        assert result.agent_type is not None

    def test_case_insensitivity(self) -> None:
        """Classification should be case-insensitive."""
        lower = _classify("write a function")
        upper = _classify("WRITE A FUNCTION")
        mixed = _classify("Write A Function")
        assert lower.agent_type == upper.agent_type == mixed.agent_type == "code"

    def test_punctuation_does_not_break_matching(self) -> None:
        """Punctuation adjacent to keywords should not prevent matching."""
        result = _classify("debug the crash and investigate the traceback!")
        assert result.agent_type == "debug"

    def test_very_long_prompt(self) -> None:
        """A very long prompt should still classify without error."""
        filler = "some random words here " * 200
        result = _classify(f"write a function {filler}")
        # "write" and "function" are in early positions -> code
        assert result.agent_type == "code"

    def test_numbers_in_prompt(self) -> None:
        """Prompts with numbers should still work."""
        result = _classify("write 3 functions for the api v2 endpoint")
        assert result.agent_type == "code"

    def test_tie_breaking_by_position(self) -> None:
        """When two types tie on score, the one whose first match appears
        earliest in the prompt should win.  Use a low threshold so the
        single-keyword matches are accepted."""
        result = _classify("review the test results", threshold=0.5)
        # Both "review" (review type) and "test" (test type) match with
        # identical scores.  "review" appears at a lower character position.
        assert result.agent_type == "review"

    def test_multiword_pattern_ci_cd(self) -> None:
        """The multi-word pattern 'ci/cd' should match via substring."""
        result = _classify("set up the ci/cd pipeline and automate deployment")
        assert result.agent_type == "orchestrator"

    def test_multiword_pattern_not_working(self) -> None:
        """The multi-word pattern 'not working' should match."""
        result = _classify(
            "the server is not working at all, please investigate"
        )
        assert result.agent_type == "debug"

    def test_multiword_pattern_fix_error(self) -> None:
        """The multi-word 'fix error' must appear as an exact substring."""
        # "fix error" as an exact substring (no intervening words)
        result = _classify("fix error in the handler and debug it")
        assert result.agent_type == "debug"

    def test_multiword_mismatch_fix_the_error(self) -> None:
        """'fix the error' does NOT match the 'fix error' pattern (substring)."""
        result = _classify("fix the error in user registration")
        # No debug patterns match because "fix error" != "fix the error"
        # and no other debug keywords appear, so confidence should be 0.
        assert result.confidence == 0.0

    def test_special_characters(self) -> None:
        """Prompts with special characters should not crash."""
        result = _classify("write @#$%^& a function!!!")
        # Should still detect "write" and "function"
        assert result.agent_type == "code"

    def test_cross_type_keyword_pollution(self) -> None:
        """'write tests' could match code ('write') or test ('write tests').

        The multi-word 'write tests' pattern gives test type a match, while
        'write' alone gives code type a match.  The module keyword 'module'
        also matches code.  This tests that the classifier resolves the
        conflict deterministically.
        """
        result = _classify("write tests and add coverage", threshold=0.5)
        # "write tests" (test) + "test" (test) + "coverage" (test) vs
        # "write" (code).  Test type should win.
        assert result.agent_type == "test"


# ---------------------------------------------------------------------------
# 5. IntentResult dataclass
# ---------------------------------------------------------------------------


class TestIntentResult:
    """Verify IntentResult dataclass fields and defaults."""

    def test_all_fields_present(self) -> None:
        result = IntentResult(
            agent_type="code",
            confidence=0.85,
            reasoning="Matched code patterns.",
            matched_patterns=["write", "function"],
        )
        assert result.agent_type == "code"
        assert result.confidence == 0.85
        assert result.reasoning == "Matched code patterns."
        assert result.matched_patterns == ["write", "function"]

    def test_default_matched_patterns(self) -> None:
        """matched_patterns should default to an empty list."""
        result = IntentResult(
            agent_type=None,
            confidence=0.0,
            reasoning="Empty prompt.",
        )
        assert result.matched_patterns == []
        assert isinstance(result.matched_patterns, list)

    def test_agent_type_can_be_none(self) -> None:
        result = IntentResult(agent_type=None, confidence=0.0, reasoning="No match.")
        assert result.agent_type is None

    def test_field_types(self) -> None:
        """Verify field types from a real classification result."""
        result = _classify("write a function")
        assert isinstance(result.agent_type, str) or result.agent_type is None
        assert isinstance(result.confidence, float)
        assert isinstance(result.reasoning, str)
        assert isinstance(result.matched_patterns, list)

    def test_field_types_below_threshold(self) -> None:
        """Types are correct even when the result is below threshold."""
        result = _classify("plan something", threshold=0.7)
        assert result.agent_type is None
        assert isinstance(result.confidence, float)
        assert isinstance(result.reasoning, str)
        assert isinstance(result.matched_patterns, list)

    def test_default_factory_isolation(self) -> None:
        """Each IntentResult should get its own list instance, not a shared one."""
        r1 = IntentResult(agent_type=None, confidence=0.0, reasoning="a")
        r2 = IntentResult(agent_type=None, confidence=0.0, reasoning="b")
        r1.matched_patterns.append("test_pattern")
        assert r2.matched_patterns == [], "Default list should not be shared."


# ---------------------------------------------------------------------------
# 6. Convenience function
# ---------------------------------------------------------------------------


class TestConvenienceFunction:
    """Verify the module-level classify_intent() wrapper."""

    def test_returns_same_as_classifier(self) -> None:
        """classify_intent(prompt) should match IntentClassifier().classify(prompt)."""
        prompt = "write a function that reverses a string"
        direct = IntentClassifier().classify(prompt)
        convenience = classify_intent(prompt)
        assert direct.agent_type == convenience.agent_type
        assert direct.confidence == convenience.confidence
        assert direct.matched_patterns == convenience.matched_patterns

    def test_custom_threshold(self) -> None:
        """classify_intent(prompt, threshold=X) should use that threshold."""
        prompt = "plan something"
        high = classify_intent(prompt, threshold=0.7)
        low = classify_intent(prompt, threshold=0.3)
        # Both see the same patterns, so confidence is identical.
        assert high.confidence == low.confidence
        # But the high threshold rejects while the low threshold accepts.
        assert high.agent_type is None
        assert low.agent_type == "plan"

    def test_default_threshold_is_0_7(self) -> None:
        """The default threshold should be 0.7."""
        # A prompt scoring ~0.667 should be rejected with the default.
        result = classify_intent("plan something")
        assert result.agent_type is None

    def test_returns_intent_result_type(self) -> None:
        """The return type should be IntentResult."""
        result = classify_intent("hello world")
        assert isinstance(result, IntentResult)

    def test_empty_prompt_via_convenience(self) -> None:
        """The convenience function should handle empty prompts correctly."""
        result = classify_intent("")
        assert result.agent_type is None
        assert result.confidence == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
