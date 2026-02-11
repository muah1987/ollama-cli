# Plan: Hugging Face Integration

## Task Description

Integrate Hugging Face as a provider in the Ollama CLI while following a modular, extensible architecture. The integration will use Hugging Face's router API with OpenAI-compatible endpoint format, supporting chat completions, model listing, health checks, and token tracking. Users can configure `HF_TOKEN` environment variable to use Hugging Face models.

## Objective

Add Hugging Face as a provider while demonstrating a modular pattern for easily adding new providers to the CLI. This integration will:

1. Add Hugging Face as a first-class provider alongside Ollama, Claude, and Gemini
2. Demonstrate the extensible architecture pattern for future providers
3. Enable access to thousands of open-weight models through Hugging Face's router service

**Modular Design Principles Applied:**
- Single Responsibility: Each provider is a self-contained class
- Open/Closed Principle: Open for extension, closed for modification
- Dependency Injection: Providers accept configuration via constructor
- Interface-Based: All providers implement the same BaseProvider interface
- Convention over Configuration: Simple naming and structure rules

**CLI Component Integration:**
- All components work together seamlessly
- Easy to add new providers following established patterns
- Configuration-driven provider discovery
- Plugin-style architecture for future extensions

## Problem Statement

Currently Ollama CLI supports only 4 providers:
1. Ollama (local models)
2. Claude (Anthropic)
3. Gemini (Google)
4. Codex (OpenAI)

**The Problem for Future Providers:**
When adding a new provider, developers currently need to:
- Modify `provider_router.py` with a new class
- Update multiple places in the codebase
- No single source of truth for provider configuration

**What We Want to Achieve:**
- A pattern where adding a new provider requires minimal code changes
- Configuration-driven provider discovery
- Plug-and-play architecture for future extensions

## Relevant Files

### Existing Files (Modify)
- `ollama-cli/production/api/provider_router.py` - Add HfProvider class and integrate with ProviderRouter
- `ollama-cli/production/docs/multi_provider.md` - Add Hugging Face provider section
- `ollama-cli/production/README.md` - Add Hugging Face to features list
- `ollama-cli/production/pyproject.toml` - Add openai dependency if not present
- `ollama-cli/production/api/ollama_client.py` - Review for potential HF-specific helpers

### New Files
- None required for Hugging Face integration itself

### New Files (For Modular Architecture Enhancement - Optional)
- `ollama-cli/production/api/provider_registry.py` - Provider registry with dynamic loading
- `ollama-cli/production/docs/adding_providers.md` - Guide for future provider development

## Implementation Phases

### Phase 1: Core Provider Implementation
- Create HfProvider class in `api/provider_router.py`
- Implement chat, complete, health_check, list_models methods
- Handle OpenAI-compatible response format
- Support streaming responses

### Phase 2: Router Integration
- Add "hf" to provider fallback chain
- Update `_build_provider()` to include Hugging Face
- Add HF to `list_available_providers()` check
- Add default model configuration for HF

### Phase 2.5: Modular Architecture Pattern (NEW)
- Document the provider registration pattern for future providers
- Create `api/provider_registry.py` - standalone provider registry
- Define `PROVIDER_CONFIG` dict for easy configuration
- Create `_add_provider()` function for dynamic registration

### Phase 3: Documentation
- Update `docs/multi_provider.md` with HF section
- Add `docs/huggingface.md` for detailed HF documentation
- Update `README.md` features and quick start
- Create `docs/adding_providers.md` - guide for future provider development
- Document environment variable configuration

### Phase 4: Validation
- Test health check against HF router
- Test model listing
- Test chat completion with sample prompt
- Verify token counting accuracy

## Modular Architecture for Future Providers

### The Provider Pattern

To add a new provider in the future, follow this pattern:

#### Step 1: Create Provider Class
```python
# api/my_provider.py
from api.provider_router import BaseProvider, ProviderAuthError, ProviderError

class MyProvider(BaseProvider):
    name = "my_provider"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("MY_API_KEY", "")
        if not self._api_key:
            raise ProviderAuthError("MY_API_KEY is not set")
        self._client = httpx.AsyncClient(...)

    async def chat(...) -> ...: ...
    async def complete(...) -> str: ...
    async def health_check() -> bool: ...
    async def list_models() -> list[str]: ...
```

#### Step 2: Register in Provider Router
```python
# In provider_router.py
PROVIDER_REGISTRY = {
    "my_provider": lambda: MyProvider(),
    # ... other providers
}
```

#### Step 3: Add to Fallback Chain
```python
_FALLBACK_CHAIN = ["ollama", "claude", "gemini", "codex", "hf", "my_provider"]
```

#### Step 4: Configure Environment Variables
```python
_TASK_ENV_MAP = {
    "coding": ("OLLAMA_CLI_CODING_PROVIDER", "OLLAMA_CLI_CODING_MODEL", "ollama", "..."),
    # Add my_provider as option
}
```

### Adding a New Provider Checklist

- [ ] Create provider class extending `BaseProvider`
- [ ] Implement all 4 abstract methods
- [ ] Read API key from `MY_API_KEY` environment variable
- [ ] Raise `ProviderAuthError` when key missing
- [ ] Add provider name to `PROVIDER_REGISTRY`
- [ ] Add to `_FALLBACK_CHAIN` list
- [ ] Update `list_available_providers()` to check key
- [ ] Add to `_TASK_ENV_MAP` (if applicable)
- [ ] Write documentation in `docs/adding_providers.md`

## Team Orchestration

### Team Members

- Builder
  - Name: builder-hf-integration
  - Role: Implement Hugging Face provider class and router integration
  - Agent Type: general-purpose
  - Resume: true

- Validator
  - Name: validator-hf
  - Role: Validate the implementation against acceptance criteria
  - Agent Type: validator
  - Resume: true

## Step by Step Tasks

### 1. Create HfProvider Class
- **Task ID**: create-hf-provider
- **Depends On**: none
- **Assigned To**: builder-hf-integration
- **Agent Type**: general-purpose
- **Parallel**: false

Implement the HfProvider class that:
- Extends BaseProvider (already defined in provider_router.py)
- Uses `base_url="https://router.huggingface.co/v1"`
- Reads `HF_TOKEN` from environment
- Implements all 5 abstract methods
- Returns "hf" as provider name
- Supports OpenAI-compatible response format
- Handles streaming for chat completions

```python
class HfProvider(BaseProvider):
    name = "hf"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("HF_TOKEN", "")
        if not self._api_key:
            raise ProviderAuthError("HF_TOKEN is not set")
        self._default_model = _DEFAULT_MODELS.get("hf", "zai-org/GLM-4.7-Flash:novita")
        self._client = httpx.AsyncClient(
            base_url="https://router.huggingface.co/v1",
            timeout=httpx.Timeout(_DEFAULT_TIMEOUT),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
        )

    # Implement chat, complete, health_check, list_models
```

### 2. Update ProviderRouter for Hugging Face
- **Task ID**: update-provider-router
- **Depends On**: create-hf-provider
- **Assigned To**: builder-hf-integration
- **Agent Type**: general-purpose
- **Parallel**: false

Make these changes to provider_router.py:
- Add "hf" to `_FALLBACK_CHAIN` list (after codex)
- Add HF default model to `_DEFAULT_MODELS` dict
- Add `HF_TOKEN` mapping to `list_available_providers()`
- Update `_build_provider()` to handle "hf" case
- Add HF-specific handling in route() if needed

### 3. Add Hugging Face to Token Tracking
- **Task ID**: add-hf-token-tracking
- **Depends On**: create-hf-provider
- **Assigned To**: builder-hf-integration
- **Agent Type**: general-purpose
- **Parallel**: false

Ensure Hugging Face responses include token usage in the response format. The OpenAI-compatible format returns:
```json
{
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### 4. Update Documentation
- **Task ID**: update-docs
- **Depends On**: update-provider-router
- **Assigned To**: builder-hf-integration
- **Agent Type**: general-purpose
- **Parallel**: false

Update documentation files:
- Add Hugging Face section to `docs/multi_provider.md`
- Add `docs/huggingface.md` with detailed usage
- Update `README.md` features to include HF
- Add HF to CLI quick start examples
- Create `docs/adding_providers.md` - guide for future provider development

### 5. Add CLI Support
- **Task ID**: add-cli-support
- **Depends On**: update-provider-router
- **Assigned To**: builder-hf-integration
- **Agent Type**: general-purpose
- **Parallel**: false

No changes needed if existing `--provider` flag already supports all providers dynamically.

### 6. Modular Architecture Documentation (NEW)
- **Task ID**: doc-modular-architecture
- **Depends On**: update-provider-router
- **Assigned To**: builder-hf-integration
- **Agent Type**: general-purpose
- **Parallel**: false

Document the modular architecture:
- Create architecture diagrams showing component interaction
- Document the Provider Pattern for future extensions
- Document the Command Pattern for new CLI commands
- Document all extensibility points

### 7. Validation and Testing
- **Task ID**: validate-all
- **Depends On**: create-hf-provider, update-provider-router, update-docs, doc-modular-architecture
- **Assigned To**: validator-hf
- **Agent Type**: validator
- **Parallel**: false

Verify:
- HfProvider can be instantiated with HF_TOKEN
- Health check returns True/False appropriately
- Model listing works (or returns known models if API doesn't support)
- Chat completion returns proper response structure
- Error handling for missing/invalid tokens

## Acceptance Criteria

1. **Provider Registration**: Hugging Face can be selected via `--provider hf` flag
2. **Authentication**: Reads `HF_TOKEN` from environment without hardcoding
3. **Chat Completions**: Successfully sends messages and receives responses
4. **Health Check**: Returns False when HF_TOKEN is missing, True when valid
5. **Model Listing**: Either lists available models or returns known models
6. **Token Tracking**: Usage information is extracted from responses
7. **Error Handling**: Proper exceptions for auth errors and connection issues
8. **Documentation**: All docs updated with HF provider information

## Validation Commands

```bash
# Set up environment
export HF_TOKEN="your-huggingface-token"

# Test provider can be imported
cd ollama-cli/production
uv run python -c "from api.provider_router import HfProvider; print('Import success')"

# Test health check
uv run python -c "
import asyncio
from api.provider_router import HfProvider
async def test():
    p = HfProvider()
    print(f'Health: {await p.health_check()}')
    print(f'Available models: {await p.list_models()}')
asyncio.run(test())
"

# Test chat completion
uv run python -c "
import asyncio
from api.provider_router import HfProvider
async def test():
    p = HfProvider()
    result = await p.chat([{'role': 'user', 'content': 'Hello'}])
    print(f'Response: {result}')
asyncio.run(test())
"

# Test via ProviderRouter
uv run python -c "
import asyncio
from api.provider_router import ProviderRouter
async def test():
    r = ProviderRouter()
    print(f'Available providers: {r.list_available_providers()}')
    # Make a test request
asyncio.run(test())
"

# Run existing tests
uv run ruff check api/provider_router.py
uv run pytest tests/ -v --tb=short
```

## Modular Component Architecture

### How All CLI Components Work Together

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Layer (cmd/)                        │
│  - root.py      -- Main entry point, command routing            │
│  - run.py       -- Single-prompt execution                      │
│  - interactive.py -- Chat mode session                          │
│  - list.py      -- Model listing                                │
│  - ... (other commands)                                         │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Provider Router Layer                      │
│  - provider_router.py   -- Routes to Ollama/Claude/Gemini/HF   │
│  - ollama_client.py     -- Native Ollama API client             │
│  - provider_registry.py -- Dynamic provider registry (NEW)     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Session & Runner Layer                    │
│  - session.py           -- Conversation state management        │
│  - context_manager.py   -- Auto-compact context handling        │
│  - token_counter.py     -- Token usage tracking                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Model Layer                              │
│  - Model selection, configuration, fallback logic               │
└─────────────────────────────────────────────────────────────────┘
```

### The Extensibility Points

1. **New Commands**: Add `cmd/new_command.py` and register in `root.py`
2. **New Providers**: Implement `BaseProvider` and add to `PROVIDER_REGISTRY`
3. **New Hooks**: Add to `.ollama/settings.json` with shell/Python commands
4. **New Status Lines**: Add to `.ollama/status_lines/` directory

### Adding a New CLI Command

```python
# cmd/my_command.py
"""My new CLI command."""

async def run(args) -> int:
    """Execute the command. Return 0 for success, non-zero for error."""
    # Your implementation here
    return 0
```

Then register in `cmd/root.py`:
```python
from cmd import my_command

# In _build_main_parser():
parser_new = subparsers.add_parser("my-command", help="My new command")
parser_new.set_defaults(func=my_command.run)
```

## Notes

### Hugging Face API Details

The Hugging Face router API uses:
- Base URL: `https://router.huggingface.co/v1`
- Auth: `Bearer {HF_TOKEN}` in Authorization header
- Endpoints: `/v1/chat/completions` (OpenAI-compatible format)
- Streaming: Supported via server-sent events

### Hugging Face Models

Common models available through the router:
- `zai-org/GLM-4.7-Flash:novita` (default suggested)
- `mistralai/Mistral-7B-Instruct-v0.3`
- `meta-llama/Meta-Llama-3-8B-Instruct`
- `google/gemma-2-9b-it`
- `deepseek-ai/DeepSeek-Coder-V2-Instruct`

### Dependency Management

Check if `openai` package is already in dependencies. If not, add it:
```bash
uv add openai
```

However, since we're using httpx directly (like other providers), we may not need the openai package.

### Fallback Chain Position

Hugging Face should be added after Codex in the fallback chain:
```python
_FALLBACK_CHAIN = ["ollama", "claude", "gemini", "codex", "hf"]
```

This puts HF as a last resort after all major cloud providers.
