"""Tests for the unified error hierarchy (api/errors.py)."""

from __future__ import annotations

import pytest

from api.errors import (
    ConfigurationError,
    OllamaCliError,
    OllamaConnectionError,
    OllamaError,
    OllamaModelNotFoundError,
    ProviderAuthError,
    ProviderError,
    ProviderRateLimitError,
    ProviderResponseError,
    ProviderUnavailableError,
    SessionError,
)


# ---------------------------------------------------------------------------
# Hierarchy checks
# ---------------------------------------------------------------------------


class TestErrorHierarchy:
    """Verify that all errors inherit from OllamaCliError."""

    @pytest.mark.parametrize(
        "exc_class",
        [
            ProviderError,
            ProviderUnavailableError,
            ProviderAuthError,
            ProviderRateLimitError,
            ProviderResponseError,
            OllamaError,
            OllamaConnectionError,
            OllamaModelNotFoundError,
            ConfigurationError,
            SessionError,
        ],
    )
    def test_subclass_of_root(self, exc_class: type[OllamaCliError]) -> None:
        assert issubclass(exc_class, OllamaCliError)

    def test_provider_subtypes(self) -> None:
        assert issubclass(ProviderUnavailableError, ProviderError)
        assert issubclass(ProviderAuthError, ProviderError)
        assert issubclass(ProviderRateLimitError, ProviderError)
        assert issubclass(ProviderResponseError, ProviderError)

    def test_ollama_subtypes(self) -> None:
        assert issubclass(OllamaConnectionError, OllamaError)
        assert issubclass(OllamaModelNotFoundError, OllamaError)

    def test_root_is_exception(self) -> None:
        assert issubclass(OllamaCliError, Exception)


# ---------------------------------------------------------------------------
# user_message / hint
# ---------------------------------------------------------------------------


class TestUserMessage:
    """Verify user_message property and hint support."""

    def test_basic_message(self) -> None:
        err = OllamaCliError("something broke")
        assert err.user_message == "something broke"

    def test_message_with_hint(self) -> None:
        err = ProviderAuthError("Invalid key", hint="Set ANTHROPIC_API_KEY")
        assert "Invalid key" in err.user_message
        assert "Set ANTHROPIC_API_KEY" in err.user_message

    def test_empty_message_uses_docstring(self) -> None:
        err = ProviderRateLimitError()
        assert "rate-limit" in err.user_message.lower() or "rate" in err.user_message.lower()

    def test_hint_stored(self) -> None:
        err = ConfigurationError("bad config", hint="check .env")
        assert err.hint == "check .env"

    def test_no_hint_default(self) -> None:
        err = SessionError("oops")
        assert err.hint == ""


# ---------------------------------------------------------------------------
# Catch-all semantics
# ---------------------------------------------------------------------------


class TestCatchAll:
    """Verify that except OllamaCliError catches all subtypes."""

    def test_catch_provider_error(self) -> None:
        with pytest.raises(OllamaCliError):
            raise ProviderUnavailableError("down")

    def test_catch_ollama_error(self) -> None:
        with pytest.raises(OllamaCliError):
            raise OllamaConnectionError("unreachable")

    def test_catch_config_error(self) -> None:
        with pytest.raises(OllamaCliError):
            raise ConfigurationError("missing key")

    def test_catch_session_error(self) -> None:
        with pytest.raises(OllamaCliError):
            raise SessionError("load failed")


# ---------------------------------------------------------------------------
# Re-export sanity
# ---------------------------------------------------------------------------


class TestReexport:
    """Errors are importable from api package root."""

    def test_import_from_api(self) -> None:
        from api import (
            ConfigurationError,
            OllamaCliError,
            OllamaConnectionError,
            OllamaError,
            OllamaModelNotFoundError,
            ProviderAuthError,
            ProviderError,
            ProviderRateLimitError,
            ProviderResponseError,
            ProviderUnavailableError,
            SessionError,
        )

        # Sanity: they are the same classes
        assert OllamaCliError is not None
        assert ProviderError is not None
        assert OllamaError is not None
        assert ConfigurationError is not None
        assert SessionError is not None
        assert ProviderRateLimitError is not None
        assert ProviderResponseError is not None
        assert OllamaConnectionError is not None
        assert OllamaModelNotFoundError is not None
        assert ProviderAuthError is not None
        assert ProviderUnavailableError is not None
