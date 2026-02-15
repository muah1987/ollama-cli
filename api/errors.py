"""Unified error hierarchy for the Ollama CLI API layer.

This module centralises all custom exceptions used across the API package
so that consumers can catch errors at the desired level of granularity.

Hierarchy
---------
::

    QarinCliError
    ├── ProviderError
    │   ├── ProviderUnavailableError
    │   ├── ProviderAuthError
    │   ├── ProviderRateLimitError
    │   └── ProviderResponseError
    ├── OllamaError
    │   ├── OllamaConnectionError
    │   └── OllamaModelNotFoundError
    ├── ConfigurationError
    └── SessionError
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------


class QarinCliError(Exception):
    """Base exception for all Ollama CLI errors.

    Every custom exception in the project inherits from this class so that
    callers can use a single ``except QarinCliError`` clause to catch all
    application-level errors.
    """

    def __init__(self, message: str = "", *, hint: str = "") -> None:
        self.hint = hint
        super().__init__(message)

    @property
    def user_message(self) -> str:
        """Return a user-friendly description of the error."""
        base = str(self) or self.__class__.__doc__ or "An unexpected error occurred."
        if self.hint:
            return f"{base}\nHint: {self.hint}"
        return base


# ---------------------------------------------------------------------------
# Provider errors
# ---------------------------------------------------------------------------


class ProviderError(QarinCliError):
    """Base exception for provider-related errors."""


class ProviderUnavailableError(ProviderError):
    """Raised when a provider cannot be reached or is not responding."""


class ProviderAuthError(ProviderError):
    """Raised when authentication with a provider fails (missing or invalid key)."""


class ProviderRateLimitError(ProviderError):
    """Raised when the provider returns a rate-limit (HTTP 429) response."""


class ProviderResponseError(ProviderError):
    """Raised when the provider returns an unexpected or malformed response."""


# ---------------------------------------------------------------------------
# Ollama-specific errors
# ---------------------------------------------------------------------------


class OllamaError(QarinCliError):
    """Base exception for Ollama API errors."""


class OllamaConnectionError(OllamaError):
    """Raised when the Ollama server is unreachable."""


class OllamaModelNotFoundError(OllamaError):
    """Raised when a requested model does not exist."""


# ---------------------------------------------------------------------------
# Configuration / session errors
# ---------------------------------------------------------------------------


class ConfigurationError(QarinCliError):
    """Raised when a configuration value is missing or invalid."""


class SessionError(QarinCliError):
    """Raised when a session operation fails (save, load, resume)."""
