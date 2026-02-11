# Adding New Providers to Ollama CLI

Guide for extending Ollama CLI with additional AI providers.

---

## Overview

Ollama CLI is designed with a modular architecture that makes it easy to add new providers. This guide explains how to implement a new provider that integrates seamlessly with the existing system.

## Provider Architecture

### Core Interface

All providers must implement the `BaseProvider` abstract class:

```python
class BaseProvider(abc.ABC):
    name: str = ""

    @abc.abstractmethod
    async def chat(...)
    async def complete(...)
    async def health_check(...)
    async def list_models(...)
```

### Registration Process

Providers are registered in two places:
1. `_build_provider()` method in `ProviderRouter`
2. `list_available_providers()` method for API key checking
3. `_DEFAULT_MODELS` dictionary for default model assignment

## Step-by-Step Implementation

### 1. Create Your Provider Class

Create a new class that extends `BaseProvider`:

```python
class MyProvider(BaseProvider):
    name = "my_provider"

    def __init__(self, api_key: str | None = None) -> None:
        # Handle authentication
        self._api_key = api_key or os.environ.get("MY_API_KEY", "")
        if not self._api_key:
            raise ProviderAuthError("MY_API_KEY is not set")

        # Initialize HTTP client
        self._client = httpx.AsyncClient(
            base_url="https://api.myprovider.com",
            headers={"Authorization": f"Bearer {self._api_key}"}
        )
```

### 2. Implement Required Methods

#### Chat Method
Handles multi-turn conversations:

```python
async def chat(
    self,
    messages: list[dict[str, str]],
    model: str | None = None,
    stream: bool = False,
    **kwargs: Any,
) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
    # Convert messages to provider format
    # Make API request
    # Handle streaming if requested
    # Return standardized response
```

#### Complete Method
Handles single-turn prompts:

```python
async def complete(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
    # Convert prompt to message format
    # Call chat method
    # Extract and return text response
```

#### Health Check Method
Verifies provider availability:

```python
async def health_check(self) -> bool:
    # Make minimal API request to verify connectivity
    # Return True if healthy, False otherwise
```

#### List Models Method
Returns available models:

```python
async def list_models(self) -> list[str]:
    # Query provider API for model list
    # Return list of model identifiers
```

### 3. Add to Provider Router

Update `provider_router.py`:

```python
# Add to _DEFAULT_MODELS
_DEFAULT_MODELS: dict[str, str] = {
    # existing providers...
    "my_provider": "default-model-name",
}

# Add to _build_provider method
def _build_provider(self, name: str) -> BaseProvider:
    # existing providers...
    if name == "my_provider":
        return MyProvider()

# Add to list_available_providers method
def list_available_providers(self) -> list[str]:
    key_map: dict[str, str] = {
        # existing providers...
        "my_provider": "MY_API_KEY",
    }
```

### 4. Add to Fallback Chain

Update the fallback priority order:

```python
_FALLBACK_CHAIN: list[str] = ["ollama", "claude", "gemini", "codex", "my_provider"]
```

## Best Practices

### Error Handling

Always raise appropriate exceptions:
- `ProviderAuthError` for authentication issues
- `ProviderError` for API errors
- Standard exceptions for network issues

### Streaming Support

Implement streaming when possible:
- Use the same streaming interface as existing providers
- Handle server-sent events correctly
- Clean up resources properly

### Resource Management

Close HTTP clients properly:

```python
async def close(self) -> None:
    if not self._client.is_closed:
        await self._client.aclose()
```

## Example Implementation

Here's a complete example for a fictional provider:

```python
class ExampleProvider(BaseProvider):
    """Provider for Example AI Service."""

    name = "example"
    _BASE_URL = "https://api.example.com"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("EXAMPLE_API_KEY", "")
        if not self._api_key:
            raise ProviderAuthError("EXAMPLE_API_KEY is not set")
        self._client = httpx.AsyncClient(
            base_url=self._BASE_URL,
            timeout=httpx.Timeout(_DEFAULT_TIMEOUT),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any] | AsyncIterator[dict[str, Any]]:
        payload = {
            "model": model or self._default_model,
            "messages": messages,
            "stream": stream,
        }
        payload.update(kwargs)

        if stream:
            req = self._client.build_request("POST", "/chat", json=payload)
            response = await self._client.send(req, stream=True)
            # Handle streaming response...
            return self._stream_response(response)

        response = await self._client.post("/chat", json=payload)
        # Handle non-streaming response...
        return response.json()

    async def complete(self, prompt: str, model: str | None = None, **kwargs: Any) -> str:
        # Implementation...

    async def health_check(self) -> bool:
        # Implementation...

    async def list_models(self) -> list[str]:
        # Implementation...

    async def close(self) -> None:
        if not self._client.is_closed:
            await self._client.aclose()
```

## Testing Your Provider

### Unit Tests

Add tests to verify your implementation:

```python
# In tests/test_provider_router.py
async def test_example_provider_chat():
    provider = ExampleProvider(api_key="test-key")
    # Test chat functionality
    # Verify response format
    # Test error conditions

async def test_example_provider_health_check():
    provider = ExampleProvider(api_key="test-key")
    # Test health check
```

### Integration Tests

Test with the ProviderRouter:

```python
async def test_example_provider_routing():
    router = ProviderRouter()
    # Test routing to your provider
    # Verify fallback behavior
```

## Documentation

### Update Multi-Provider Guide

Add your provider to `docs/multi_provider.md`:
- Supported Providers table
- Setup instructions
- Usage examples
- Provider comparison

### Create Provider-Specific Doc

Create `docs/example.md` with:
- Introduction and features
- Setup guide
- Usage examples
- Troubleshooting

## Checklist

Before submitting your provider:

- [ ] Implements all abstract methods from `BaseProvider`
- [ ] Handles authentication properly
- [ ] Supports streaming responses
- [ ] Implements proper error handling
- [ ] Manages HTTP client resources
- [ ] Follows code style and conventions
- [ ] Includes unit tests
- [ ] Updates documentation
- [ ] Works with ProviderRouter
- [ ] Handles fallback behavior correctly

## Support

For questions about provider development, please:
1. Check existing provider implementations
2. Review the HfProvider implementation as an example
3. File an issue on GitHub for assistance