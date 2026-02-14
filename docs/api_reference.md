# API Reference

Complete API documentation for Ollama CLI - including native Ollama endpoints, OpenAI-compatible endpoints, multi-provider routing, and Python client examples.

---

## Table of Contents

- [Base URLs](#base-urls)
- [Native Ollama API](#native-ollama-api)
- [OpenAI-Compatible API](#openai-compatible-api)
- [Multi-Provider API](#multi-provider-api)
- [Python Client Examples](#python-client-examples)
- [Response Formats](#response-formats)
- [Error Codes](#error-codes)
- [Environment Variables](#environment-variables)

---

## Base URLs

### Native Ollama API

```text
http://localhost:11434/api
```

### OpenAI-Compatible API

```text
http://localhost:11434/v1
```

### Multi-Provider Router

```text
http://localhost:11434/api/v1
```

Configure the host via `OLLAMA_HOST` environment variable.

---

## Native Ollama API

### Chat Completion

Send a chat completion request to a model.

**Endpoint:** `POST /api/chat`

**Request:**

```json
{
  "model": "llama3.2",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false,
  "temperature": 0.7,
  "top_p": 0.9,
  "system": "You are a helpful assistant."
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | Yes | Model name (e.g., `llama3.2`) |
| `messages` | array | Yes | Conversation history |
| `stream` | boolean | No | Enable streaming (default: `false`) |
| `temperature` | number | No | Sampling temperature (0.0 - 1.0) |
| `top_p` | number | No | Nucleus sampling parameter |
| `system` | string | No | System prompt |
| `format` | string | No | Response format (`json` or `text`) |
| `options` | object | No | Additional model options |

**Response (non-streaming):**

```json
{
  "model": "llama3.2",
  "message": {
    "role": "assistant",
    "content": "Hello! How can I help you today?"
  },
  "done": true,
  "total_duration": 123456789,
  "load_duration": 45678900,
  "prompt_eval_count": 12,
  "prompt_eval_duration": 23456789,
  "eval_count": 45,
  "eval_duration": 54321000
}
```

**Streaming Response (NDJSON):**

```
{"model":"llama3.2","message":{"role":"assistant","content":"Hello"},"done":false}
{"model":"llama3.2","message":{"role":"assistant","content":"!"},"done":false}
{"model":"llama3.2","message":{"role":"assistant","content":" How"},"done":false}
{"model":"llama3.2","message":{"role":"assistant","content":" can"},"done":false}
{"model":"llama3.2","message":{"role":"assistant","content":" I"},"done":false}
{"model":"llama3.2","message":{"role":"assistant","content":" help"},"done":false}
{"model":"llama3.2","message":{"role":"assistant","content":" you"},"done":false}
{"model":"llama3.2","message":{"role":"assistant","content":" today"},"done":false}
{"model":"llama3.2","message":{"role":"assistant","content":"?"},"done":false}
{"model":"llama3.2","done":true,"total_duration":123456789,"load_duration":45678900,"prompt_eval_count":12,"prompt_eval_duration":23456789,"eval_count":45,"eval_duration":54321000}
```

---

### Generate Completion

Generate a completion from a single prompt.

**Endpoint:** `POST /api/generate`

**Request:**

```json
{
  "model": "llama3.2",
  "prompt": "Explain recursion in Python",
  "stream": false,
  "temperature": 0.7
}
```

**Response (non-streaming):**

```json
{
  "model": "llama3.2",
  "response": "Recursion is a programming technique where a function calls itself...",
  "done": true,
  "total_duration": 123456789,
  "load_duration": 45678900,
  "prompt_eval_count": 8,
  "prompt_eval_duration": 23456789,
  "eval_count": 156,
  "eval_duration": 54321000
}
```

**Streaming Response:**

```
{"model":"llama3.2","response":"Recursion","done":false}
{"model":"llama3.2","response":" is","done":false}
{"model":"llama3.2","response":" a","done":false}
{"model":"llama3.2","response":" programming","done":false}
{"model":"llama3.2","response":" technique","done":false}
{"model":"llama3.2","response":" where","done":false}
{"model":"llama3.2","response":" a","done":false}
{"model":"llama3.2","response":" function","done":false}
{"model":"llama3.2","response":" calls","done":false}
{"model":"llama3.2","response":" itself","done":false}
{"model":"llama3.2","response":" to","done":false}
{"model":"llama3.2","response":" solve","done":false}
{"model":"llama3.2","response":" problems","done":false}
{"model":"llama3.2","response":" by","done":false}
{"model":"llama3.2","response":" breaking","done":false}
{"model":"llama3.2","response":" them","done":false}
{"model":"llama3.2","response":" into","done":false}
{"model":"llama3.2","response":" smaller","done":false}
{"model":"llama3.2","response":" sub","done":false}
{"model":"llama3.2","response":" problems","done":false}
{"model":"llama3.2","response":".","done":false}
{"model":"llama3.2","done":true,"total_duration":123456789,"load_duration":45678900,"prompt_eval_count":8,"prompt_eval_duration":23456789,"eval_count":156,"eval_duration":54321000}
```

---

### List Models

List all locally available models.

**Endpoint:** `GET /api/tags`

**Response:**

```json
{
  "models": [
    {
      "name": "llama3.2",
      "model": "llama3.2:latest",
      "modified_at": "2024-01-15T10:30:00.000000000Z",
      "size": 1677721600,
      "digest": "sha256:abc123...",
      "size_vram": 2147483648,
      "details": {
        "parent_model": "",
        "format": "gguf",
        "family": "llama",
        "families": ["llama"],
        "parameter_size": "3B",
        "quantization_level": "Q4_K_M"
      }
    },
    {
      "name": "codestral:latest",
      "model": "codestral:latest",
      "modified_at": "2024-01-14T08:15:00.000000000Z",
      "size": 7516192768,
      "digest": "sha256:def456...",
      "size_vram": 8589934592,
      "details": {
        "parent_model": "",
        "format": "gguf",
        "family": "llama",
        "families": ["llama"],
        "parameter_size": "7B",
        "quantization_level": "Q3_K_M"
      }
    }
  ]
}
```

---

### Show Model Information

Get detailed information about a specific model.

**Endpoint:** `POST /api/show`

**Request:**

```json
{
  "model": "llama3.2"
}
```

**Response:**

```json
{
  "license": "MIT",
  "modelfile": "# Modelfile generated by ollama\n\nFROM llama3.2\n\nSYSTEM ```\nYou are a helpful assistant.\n```",
  "parameters": """
  -temperature 0.7
  -top_p 0.9
  -top_k 40
  -num_predict 2048
  -repeat_penalty 1.1
  """,
  "template": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{{.System}}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{{.Prompt}}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
  "details": {
    "parent_model": "",
    "format": "gguf",
    "family": "llama",
    "families": ["llama"],
    "parameter_size": "3B",
    "quantization_level": "Q4_K_M"
  },
  "messages": []
}
```

---

### Create Model

Create a model from a Modelfile.

**Endpoint:** `POST /api/create`

**Request:**

```json
{
  "model": "my-custom-model",
  "modelfile": "FROM llama3.2\nSYSTEM You are a helpful assistant specialized in Python programming.",
  "stream": false
}
```

**Response (streaming):**

```
{"status":"creating model"}
{"status":"creating layer from modelfile"}
{"status":"writing layer"}
{"status":"success"}
```

---

### Pull Model

Pull a model from the Ollama registry.

**Endpoint:** `POST /api/pull`

**Request:**

```json
{
  "model": "llama3.2",
  "stream": true
}
```

**Streaming Response:**

```
{"status":"pulling manifest"}
{"status":"pulling 456789abc...","digest":"456789abc...","total":1677721600,"completed":167772160}
{"status":"pulling 456789abc...","digest":"456789abc...","total":1677721600,"completed":335544320}
{"status":"pulling 456789abc...","digest":"456789abc...","total":1677721600,"completed":503316480}
{"status":"verifying sha256 digest"}
{"status":"writing layer"}
{"status":"writing manifest"}
{"status":"success"}
```

---

### Push Model

Push a model to the Ollama registry.

**Endpoint:** `POST /api/push`

**Request:**

```json
{
  "model": "my-custom-model",
  "stream": true
}
```

**Streaming Response:**

```
{"status":"pushing manifest"}
{"status":"success"}
```

---

### Delete Model

Delete a local model.

**Endpoint:** `DELETE /api/delete`

**Request:**

```json
{
  "model": "my-custom-model"
}
```

**Response:**

```json
{
  "success": true
}
```

---

### Copy Model

Copy a model to a new name.

**Endpoint:** `POST /api/copy`

**Request:**

```json
{
  "source": "llama3.2",
  "destination": "llama3.2-copy"
}
```

**Response:**

```json
{
  "success": true
}
```

---

### Embeddings

Generate embeddings for text.

**Endpoint:** `POST /api/embed`

**Request:**

```json
{
  "model": "nomic-embed-text",
  "input": "Hello, world!"
}
```

**Response:**

```json
{
  "embeddings": [
    [
      0.123, -0.456, 0.789, -0.012, 0.345, -0.678, 0.901, -0.234,
      0.567, -0.890, 0.123, -0.456, 0.789, -0.012, 0.345, -0.678
    ]
  ],
  "total_duration": 123456789,
  "load_duration": 45678900
}
```

---

### List Running Models

List currently running models.

**Endpoint:** `GET /api/ps`

**Response:**

```json
{
  "models": [
    {
      "name": "llama3.2",
      "model": "llama3.2:latest",
      "size": 1677721600,
      "digest": "sha256:abc123...",
      "expires_at": "2024-01-15T11:30:00.000000000Z",
      "size_vram": 2147483648,
      "parameters": "-temperature 0.7 -top_p 0.9",
      "projected_duration": 300000000000
    }
  ]
}
```

---

### Version

Get the Ollama server version.

**Endpoint:** `GET /api/version`

**Response:**

```json
{
  "version": "0.3.9",
  "build_date": "2024-01-10T12:00:00Z",
  "build_commit": "abc123def456",
  "build_duration": "2m30s"
}
```

---

## OpenAI-Compatible API

### Chat Completions

The Ollama server provides an OpenAI-compatible endpoint at `/v1/chat/completions`.

**Endpoint:** `POST /v1/chat/completions`

**Request:**

```json
{
  "model": "llama3.2",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "stream": false,
  "temperature": 0.7,
  "max_tokens": 1024,
  "top_p": 0.9,
  "frequency_penalty": 0.0,
  "presence_penalty": 0.0
}
```

**Response:**

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1705312345,
  "model": "llama3.2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 15,
    "total_tokens": 27
  }
}
```

**Streaming Response:**

```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1705312345,"model":"llama3.2","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1705312345,"model":"llama3.2","choices":[{"index":0,"delta":{"content":"Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1705312345,"model":"llama3.2","choices":[{"index":0,"delta":{"content":"!"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1705312345,"model":"llama3.2","choices":[{"index":0,"delta":{"content":" How"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1705312345,"model":"llama3.2","choices":[{"index":0,"delta":{"content":" can"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1705312345,"model":"llama3.2","choices":[{"index":0,"delta":{"content":" I"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1705312345,"model":"llama3.2","choices":[{"index":0,"delta":{"content":" help"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1705312345,"model":"llama3.2","choices":[{"index":0,"delta":{"content":" you"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1705312345,"model":"llama3.2","choices":[{"index":0,"delta":{"content":" today"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1705312345,"model":"llama3.2","choices":[{"index":0,"delta":{"content":"?"},"finish_reason":"stop"}]}

data: [DONE]
```

---

### List Models

List available models via OpenAI-compatible endpoint.

**Endpoint:** `GET /v1/models`

**Response:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "llama3.2",
      "object": "model",
      "created": 1705312345,
      "owned_by": "ollama"
    },
    {
      "id": "codestral:latest",
      "object": "model",
      "created": 1705312345,
      "owned_by": "ollama"
    }
  ]
}
```

---

### Create Embedding

Create embeddings via OpenAI-compatible endpoint.

**Endpoint:** `POST /v1/embeddings`

**Request:**

```json
{
  "model": "nomic-embed-text",
  "input": "Hello, world!"
}
```

**Response:**

```json
{
  "object": "list",
  "model": "nomic-embed-text",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [
        0.123, -0.456, 0.789, -0.012, 0.345, -0.678, 0.901, -0.234
      ]
    }
  ],
  "usage": {
    "prompt_tokens": 5,
    "total_tokens": 5
  }
}
```

---

## Multi-Provider API

The `ProviderRouter` provides a unified interface for multiple AI providers.

### Provider Architecture

```
User Request
    ↓
ProviderRouter
    ↓
┌─────────────────────────────────────┐
│ OllamaProvider  → Local Ollama      │
│ ClaudeProvider  → Anthropic API     │
│ GeminiProvider  → Google API        │
│ CodexProvider   → OpenAI API        │
└─────────────────────────────────────┘
    ↓
Response
```

---

### Provider Types

| Provider | Environment Variable | API Key Env | Default Model |
|----------|---------------------|-------------|---------------|
| `ollama` | `OLLAMA_CLI_PROVIDER` | None | `llama3.2` |
| `claude` | `OLLAMA_CLI_PROVIDER` | `ANTHROPIC_API_KEY` | `claude-sonnet-4-20250514` |
| `gemini` | `OLLAMA_CLI_PROVIDER` | `GEMINI_API_KEY` | `gemini-2.0-flash` |
| `codex` | `OLLAMA_CLI_PROVIDER` | `OPENAI_API_KEY` | `gpt-4.1` |

---

### BaseProvider Interface

All providers implement the `BaseProvider` interface:

#### `async chat(messages, model=None, stream=False, **kwargs)`

Send a chat completion request.

**Parameters:**
- `messages`: List of `{"role": "user/assistant/system", "content": "..."}` dictionaries
- `model`: Optional model name (uses provider default if not specified)
- `stream`: If `True`, returns an async iterator of response chunks
- `**kwargs`: Additional provider-specific parameters

**Returns:** `dict | AsyncIterator[dict]`

#### `async complete(prompt, model=None, **kwargs)`

Generate a single-turn completion.

**Parameters:**
- `prompt`: The input text prompt
- `model`: Optional model name
- `**kwargs`: Additional provider-specific parameters

**Returns:** `str`

#### `async health_check() -> bool`

Verify provider is reachable and authenticated.

**Returns:** `bool`

#### `async list_models() -> list[str]`

List available models.

**Returns:** `list[str]`

---

### OllamaProvider

Wraps the local Ollama instance.

**Constructor:**
```python
OllamaProvider(host: str | None = None)
```

**Example:**
```python
from provider_router import OllamaProvider

provider = OllamaProvider("http://localhost:11434")
result = await provider.chat([{"role": "user", "content": "Hello!"}])
print(result["message"]["content"])
```

---

### ClaudeProvider

Uses the Anthropic Messages API.

**Constructor:**
```python
ClaudeProvider(api_key: str | None = None)
```

**Environment Variable:** `ANTHROPIC_API_KEY`

**Example:**
```python
from provider_router import ClaudeProvider

provider = ClaudeProvider()  # Reads from ANTHROPIC_API_KEY
result = await provider.chat([{"role": "user", "content": "Explain this"}])
print(result["content"][0]["text"])
```

**Task Routing:**
- Coding tasks: Uses `OLLAMA_CLI_CODING_MODEL` (default: `codestral:latest`)

---

### GeminiProvider

Uses the Google Generative AI REST API.

**Constructor:**
```python
GeminiProvider(api_key: str | None = None)
```

**Environment Variable:** `GEMINI_API_KEY`

**Example:**
```python
from provider_router import GeminiProvider

provider = GeminiProvider()  # Reads from GEMINI_API_KEY
result = await provider.chat([{"role": "user", "content": "Summarize this"}])
# Extract text from candidates[0].content.parts[0].text
```

**Task Routing:**
- Coding tasks: Uses `OLLAMA_CLI_CODING_MODEL` (default: `codestral:latest`)

---

### CodexProvider

Uses the OpenAI Chat Completions API.

**Constructor:**
```python
CodexProvider(api_key: str | None = None)
```

**Environment Variable:** `OPENAI_API_KEY`

**Example:**
```python
from provider_router import CodexProvider

provider = CodexProvider()  # Reads from OPENAI_API_KEY
result = await provider.chat([{"role": "user", "content": "Refactor this"}])
print(result["choices"][0]["message"]["content"])
```

**Task Routing:**
- Coding tasks: Uses `OLLAMA_CLI_CODING_MODEL` (default: `codestral:latest`)

---

### ProviderRouter

Routes requests to the appropriate provider based on configuration.

**Constructor:**
```python
ProviderRouter()
```

**Methods:**

#### `async route(task_type, messages, **kwargs)`

Route a request based on task type.

**Parameters:**
- `task_type`: One of `"coding"`, `"agent"`, `"subagent"`, `"embedding"`
- `messages`: Conversation history
- `**kwargs`: Forwarded to provider's `chat` method

**Returns:** Provider response

**Raises:**
- `ProviderUnavailableError`: If no provider in fallback chain can serve request

#### `get_provider(name)` -> BaseProvider

Get a cached provider instance.

#### `health_check_all() -> dict[str, bool]`

Health check for all providers with valid credentials.

#### `list_available_providers() -> list[str]`

List providers with valid credentials configured.

#### `close() -> None`

Close all provider HTTP clients.

**Example:**
```python
from provider_router import ProviderRouter

router = ProviderRouter()

# Route a coding task
result = await router.route(
    "coding",
    [{"role": "user", "content": "Fix this bug"}]
)

# Check health of all configured providers
health = await router.health_check_all()
# {"ollama": True, "claude": True, "gemini": False, "codex": True}

await router.close()
```

---

### Task Routing Configuration

The router uses environment variables to determine provider-selection per task type:

| Task Type | Provider Env | Model Env | Default Provider | Default Model |
|-----------|--------------|-----------|------------------|---------------|
| `coding` | `OLLAMA_CLI_CODING_PROVIDER` | `OLLAMA_CLI_CODING_MODEL` | `ollama` | `codestral:latest` |
| `agent` | `OLLAMA_CLI_AGENT_PROVIDER` | `OLLAMA_CLI_AGENT_MODEL` | `ollama` | `llama3.2` |
| `subagent` | `OLLAMA_CLI_SUBAGENT_PROVIDER` | `OLLAMA_CLI_SUBAGENT_MODEL` | `ollama` | `llama3.2:3b` |
| `embedding` | N/A | N/A | `ollama` | `nomic-embed-text` |

**Example Configuration:**
```bash
# Use Claude for coding, but Ollama for agent tasks
OLLAMA_CLI_CODING_PROVIDER=claude
OLLAMA_CLI_AGENT_PROVIDER=ollama

# Custom models per task
OLLAMA_CLI_CODING_MODEL=gpt-4.1
OLLAMA_CLI_AGENT_MODEL=claude-opus-4-20250514
```

---

### Fallback Chain

When a provider is unavailable, the router automatically tries other providers in this order:

1. Primary provider (configured for task type)
2. `ollama` (always available, no credentials needed)
3. `codex` (requires `OPENAI_API_KEY`)
4. `claude` (requires `ANTHROPIC_API_KEY`)
5. `gemini` (requires `GEMINI_API_KEY`)

---

## Python Client Examples

### Basic Chat with OllamaClient

```python
import asyncio
from api_client import OllamaClient

async def main():
    client = OllamaClient()

    try:
        # Non-streaming chat
        result = await client.chat(
            model="llama3.2",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Python?"}
            ],
            stream=False
        )
        print(result["message"]["content"])

        # Streaming chat
        async for chunk in await client.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": "Write a haiku"}],
            stream=True
        ):
            print(chunk["message"]["content"], end="", flush=True)

    finally:
        await client.close()

asyncio.run(main())
```

### Chat with OpenAI-Compatible Endpoint

```python
import asyncio
from api_client import OllamaClient

async def main():
    client = OllamaClient()

    try:
        # Use OpenAI-compatible endpoint
        result = await client.chat_openai(
            model="llama3.2",
            messages=[
                {"role": "user", "content": "Explain this code"}
            ],
            stream=False,
            temperature=0.7,
            max_tokens=1024
        )

        print(result["choices"][0]["message"]["content"])

        # Streaming
        async for chunk in await client.chat_openai(
            model="llama3.2",
            messages=[{"role": "user", "content": "Give me 5 ideas"}],
            stream=True
        ):
            if "choices" in chunk and chunk["choices"]:
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                print(content, end="", flush=True)

    finally:
        await client.close()

asyncio.run(main())
```

### Using ProviderRouter

```python
import asyncio
from provider_router import ProviderRouter, ProviderUnavailableError

async def main():
    router = ProviderRouter()

    try:
        # Check available providers
        print("Available providers:", router.list_available_providers())

        # Check health
        health = await router.health_check_all()
        print("Health status:", health)

        # Route a coding task (will use configured coding provider)
        result = await router.route(
            task_type="coding",
            messages=[
                {"role": "system", "content": "You are an expert Python developer."},
                {"role": "user", "content": "Refactor this function"}
            ],
            temperature=0.2,
            max_tokens=2048
        )

        # Handle streaming or non-streaming
        if isinstance(result, dict):
            print(result)
        else:
            async for chunk in result:
                print(chunk)

        # Handle fallback errors
        try:
            result = await router.route(
                task_type="agent",
                messages=[{"role": "user", "content": "Plan my day"}]
            )
        except ProviderUnavailableError as e:
            print(f"All providers failed: {e}")

    finally:
        await router.close()

asyncio.run(main())
```

### Extract Token Metrics

```python
import asyncio
from api_client import OllamaClient

async def main():
    client = OllamaClient()

    try:
        result = await client.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": "Tell me about AI"}],
            stream=False
        )

        # Extract metrics
        metrics = OllamaClient.extract_metrics(result)

        print(f"Prompt tokens: {metrics['prompt_eval_count']}")
        print(f"Completion tokens: {metrics['eval_count']}")
        print(f"Tokens per second: {metrics['tokens_per_second']}")
        print(f"Total duration: {metrics['total_duration'] / 1e9:.2f}s")

    finally:
        await client.close()

asyncio.run(main())
```

### List Models and Check Version

```python
import asyncio
from api_client import OllamaClient

async def main():
    client = OllamaClient()

    try:
        # Check if server is reachable
        if await client.health_check():
            print("Ollama is running!")

            # Get version
            version = await client.get_version()
            print(f"Version: {version}")

            # List models
            models = await client.list_models()
            print("\nAvailable models:")
            for model in models:
                print(f"  - {model['name']} ({model.get('details', {}).get('parameter_size', 'N/A')})")
                if 'size' in model:
                    size_mb = model['size'] / (1024 * 1024)
                    print(f"    Size: {size_mb:.1f} MB")

    finally:
        await client.close()

asyncio.run(main())
```

### Pull Model with Progress

```python
import asyncio
from api_client import OllamaClient

async def main():
    client = OllamaClient()

    try:
        # Pull with progress streaming
        async for progress in await client.pull_model("llama3.2", stream=True):
            if "completed" in progress and "total" in progress:
                completed = progress["completed"]
                total = progress["total"]
                percent = (completed / total * 100) if total > 0 else 0
                print(f"\rDownloading: {percent:.1f}%", end="", flush=True)
            elif "status" in progress:
                print(f"\nStatus: {progress['status']}")

        print("\nDownload complete!")

    finally:
        await client.close()

asyncio.run(main())
```

---

## Response Formats

### Standard Response Fields

All non-streaming API responses include these base fields:

| Field | Type | Description |
|-------|------|-------------|
| `model` | string | The model name used for generation |
| `created_at` | string (ISO 8601) | Timestamp of request creation |
| `done` | boolean | Whether the generation is complete |

### Token Metrics Fields

When available, responses include these metrics:

| Field | Type | Description |
|-------|------|-------------|
| `total_duration` | integer | Total request time in nanoseconds |
| `load_duration` | integer | Model loading time in nanoseconds |
| `prompt_eval_count` | integer | Number of prompt tokens evaluated |
| `prompt_eval_duration` | integer | Prompt evaluation time in nanoseconds |
| `eval_count` | integer | Number of completion tokens generated |
| `eval_duration` | integer | Token generation time in nanoseconds |

### Token Metrics Calculation

The `extract_metrics` helper calculates:

```python
tokens_per_second = eval_count / (eval_duration / 1e9)
```

### OpenAI-Compatible Response Format

The `/v1/chat/completions` endpoint follows OpenAI's format:

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "llama3.2",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Response text"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### Stream Response Format

Streaming responses use NDJSON format (one JSON object per line):

**Ollama Native Stream:**
```json
{"model":"llama3.2","message":{"role":"assistant","content":"..."},"done":false}
{"model":"llama3.2","done":true,"total_duration":123456789,"prompt_eval_count":10,"eval_count":20}
```

**OpenAI Compatible Stream:**
```
data: {"id":"chatcmpl-xxx","object":"chat.completion.chunk","created":1234567890,"model":"llama3.2","choices":[{"index":0,"delta":{"content":"..."},"finish_reason":null}]}
data: [DONE]
```

---

## Error Codes

### HTTP Status Codes

| Code | Name | Description |
|------|------|-------------|
| `200` | OK | Request succeeded |
| `400` | Bad Request | Invalid request parameters |
| `401` | Unauthorized | Invalid or missing API key |
| `403` | Forbidden | Access denied |
| `404` | Not Found | Model not found |
| `429` | Too Many Requests | Rate limit exceeded |
| `500` | Internal Server Error | Server error |
| `503` | Service Unavailable | Service temporarily unavailable |

### Native Ollama API Errors

**400 Bad Request:**
```json
{
  "error": "invalid model name"
}
```

**404 Not Found:**
```json
{
  "error": "model 'missing-model' not found"
}
```

**500 Internal Server Error:**
```json
{
  "error": "failed to generate response"
}
```

### Provider-Specific Errors

**Anthropic (Claude):**
- `401`: Invalid API key
- `429`: Rate limit exceeded
- `400`: Invalid request (max tokens, invalid model)

**Google (Gemini):**
- `401`: Invalid API key
- `403`: API not enabled
- `429`: Quota exceeded
- `400`: Invalid model or request

**OpenAI (Codex):**
- `401`: Invalid API key
- `429`: Rate limit exceeded
- `400`: Invalid model or request parameters

### Python Exception Types

The Python client raises these custom exceptions:

| Exception | Description |
|-----------|-------------|
| `OllamaError` | Base exception for Ollama API errors |
| `OllamaConnectionError` | Unable to connect to Ollama server |
| `OllamaModelNotFoundError` | Requested model does not exist |
| `ProviderError` | Base exception for provider errors |
| `ProviderUnavailableError` | No provider in fallback chain is available |
| `ProviderAuthError` | Missing or invalid API key |

**Example Error Handling:**
```python
import asyncio
from api_client import OllamaClient, OllamaConnectionError, OllamaModelNotFoundError
from provider_router import ProviderRouter, ProviderUnavailableError, ProviderAuthError

async def main():
    client = OllamaClient()

    try:
        result = await client.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": "Hello"}]
        )
    except OllamaConnectionError as e:
        print(f"Connection error: {e}")
    except OllamaModelNotFoundError as e:
        print(f"Model not found: {e}")

    await client.close()

    # Provider routing with fallback
    router = ProviderRouter()

    try:
        result = await router.route("coding", [...])
    except ProviderAuthError as e:
        print(f"Authentication error: {e}")
    except ProviderUnavailableError as e:
        print(f"No providers available: {e}")

    await router.close()

asyncio.run(main())
```

---

## Environment Variables

### Ollama Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Default model name |
| `OLLAMA_CONTEXT_LENGTH` | `4096` | Context window size in tokens |

### Provider Configuration

| Variable | Description |
|----------|-------------|
| `OLLAMA_CLI_PROVIDER` | Default provider: `ollama`, `claude`, `gemini`, `codex` |
| `OLLAMA_CLI_CODING_PROVIDER` | Provider for coding tasks |
| `OLLAMA_CLI_AGENT_PROVIDER` | Provider for agent tasks |
| `OLLAMA_CLI_SUBAGENT_PROVIDER` | Provider for subagent tasks |
| `OLLAMA_CLI_CODING_MODEL` | Model for coding tasks |
| `OLLAMA_CLI_AGENT_MODEL` | Model for agent tasks |
| `OLLAMA_CLI_SUBAGENT_MODEL` | Model for subagent tasks |

### API Keys

| Variable | Provider |
|----------|----------|
| `ANTHROPIC_API_KEY` | Claude |
| `GEMINI_API_KEY` | Gemini |
| `OPENAI_API_KEY` | Codex/OpenAI |

### Feature Flags

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_COMPACT` | `true` | Enable automatic context compaction |
| `COMPACT_THRESHOLD` | `0.85` | Context usage ratio triggering compaction |
| `KEEP_LAST_N` | `4` | Messages to preserve during compaction |
| `HOOKS_ENABLED` | `true` | Enable the hook system |

### Context Compaction Configuration

When `AUTO_COMPACT` is enabled, the context is compacted when usage exceeds `COMPACT_THRESHOLD`:

```python
# Example: Compact at 90% usage instead of 85%
COMPACT_THRESHOLD=0.9
```

---

## Quick Reference

### API Endpoint Summary

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/chat` | POST | Native chat completions |
| `/api/generate` | POST | Native text generation |
| `/api/tags` | GET | List models |
| `/api/show` | POST | Show model details |
| `/api/create` | POST | Create model from modelfile |
| `/api/pull` | POST | Pull model from registry |
| `/api/delete` | DELETE | Delete local model |
| `/api/copy` | POST | Copy model |
| `/api/embed` | POST | Generate embeddings |
| `/api/ps` | GET | List running models |
| `/api/version` | GET | Get server version |
| `/v1/chat/completions` | POST | OpenAI-compatible chat |
| `/v1/models` | GET | OpenAI-compatible model list |
| `/v1/embeddings` | POST | OpenAI-compatible embeddings |

### Provider Command-Line Flags

```bash
# Use specific provider
cli-ollama --provider claude run "prompt"

# Use specific model
cli-ollama --provider ollama --model codestral:latest run "prompt"

# Switch default provider
export OLLAMA_CLI_PROVIDER=claude
```

---

*Last updated: 2024-01-15*
