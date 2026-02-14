"""API package -- Ollama API client, config, and provider routing.

This package contains:
- errors: Unified error hierarchy for all API-layer exceptions
- ollama_client: Async HTTP client for the Ollama REST API
- config: Configuration management with environment variable support
- provider_router: Multi-provider routing (Ollama, Claude, Gemini, Codex)
"""

from .errors import (
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
from .ollama_client import (
    OllamaClient,
)
from .ollama_client import (
    OllamaClient as Client,
)
from .provider_router import (
    BaseProvider,
    ClaudeProvider,
    CodexProvider,
    GeminiProvider,
    OllamaProvider,
    ProviderRouter,
)

__all__ = [
    # Unified error hierarchy
    "OllamaCliError",
    "ConfigurationError",
    "SessionError",
    # Client
    "OllamaClient",
    "Client",
    "OllamaError",
    "OllamaConnectionError",
    "OllamaModelNotFoundError",
    # Provider router
    "ProviderRouter",
    "BaseProvider",
    "OllamaProvider",
    "ClaudeProvider",
    "GeminiProvider",
    "CodexProvider",
    "ProviderError",
    "ProviderAuthError",
    "ProviderUnavailableError",
    "ProviderRateLimitError",
    "ProviderResponseError",
]
