"""API package -- Ollama API client, config, and provider routing.

This package contains:
- ollama_client: Async HTTP client for the Ollama REST API
- config: Configuration management with environment variable support
- provider_router: Multi-provider routing (Ollama, Claude, Gemini, Codex)
"""

from .ollama_client import (
    OllamaClient,
    OllamaClient as Client,
    OllamaConnectionError,
    OllamaError,
    OllamaModelNotFoundError,
)
from .provider_router import (
    BaseProvider,
    ClaudeProvider,
    CodexProvider,
    GeminiProvider,
    OllamaProvider,
    ProviderAuthError,
    ProviderError,
    ProviderRouter,
    ProviderUnavailableError,
)

__all__ = [
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
]