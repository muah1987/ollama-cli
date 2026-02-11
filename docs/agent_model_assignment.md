# Agent Model Assignment Feature

## Overview

This feature allows users to assign specific AI models to individual agents or agent types, enabling fine-grained control over which models handle specific tasks or functions.

## Configuration Options

### Environment Variables

Users can configure agent model assignments through environment variables:

```bash
# Assign specific models to agent types
OLLAMA_CLI_AGENT_CODE_MODEL=mistralai/Mistral-7B-Instruct-v0.3
OLLAMA_CLI_AGENT_RESEARCH_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
OLLAMA_CLI_AGENT_WRITER_MODEL=gpt-4.1

# Provider assignments for agent types
OLLAMA_CLI_AGENT_CODE_PROVIDER=hf
OLLAMA_CLI_AGENT_RESEARCH_PROVIDER=claude
OLLAMA_CLI_AGENT_WRITER_PROVIDER=codex
```

### Configuration File

Users can also configure agent model assignments in `.ollama/settings.json`:

```json
{
  "agent_models": {
    "code": {
      "model": "mistralai/Mistral-7B-Instruct-v0.3",
      "provider": "hf"
    },
    "research": {
      "model": "meta-llama/Meta-Llama-3-8B-Instruct",
      "provider": "claude"
    },
    "writer": {
      "model": "gpt-4.1",
      "provider": "codex"
    }
  }
}
```

### Inline Assignment

Users can also specify agent model assignments directly in commands:

```bash
ollama-cli --agent-model code:mistralai/Mistral-7B-Instruct-v0.3 --agent-provider code:hf run "Write a Python function"
```

## Implementation Plan

### 1. Enhanced Provider Router

The `ProviderRouter` class needs to be extended to support agent-specific model assignments:

```python
# In api/provider_router.py
_AGENT_MODEL_MAP: dict[str, tuple[str, str]] = {
    # agent_type: (provider, model)
    "code": ("hf", "mistralai/Mistral-7B-Instruct-v0.3"),
    "research": ("claude", "claude-sonnet-4-20250514"),
    "writer": ("codex", "gpt-4.1"),
}
```

### 2. Configuration Loading

Add support for loading agent model assignments from environment variables and configuration files:

```python
def _load_agent_model_config() -> dict[str, tuple[str, str]]:
    """Load agent model assignments from environment and config."""
    config = {}

    # Load from environment variables
    for agent_type in ["code", "research", "writer"]:
        provider_var = f"OLLAMA_CLI_AGENT_{agent_type.upper()}_PROVIDER"
        model_var = f"OLLAMA_CLI_AGENT_{agent_type.upper()}_MODEL"

        provider = os.environ.get(provider_var)
        model = os.environ.get(model_var)

        if provider and model:
            config[agent_type] = (provider, model)

    # Load from config file
    config_file = Path(".ollama/settings.json")
    if config_file.exists():
        try:
            with open(config_file) as f:
                settings = json.load(f)
                agent_models = settings.get("agent_models", {})
                for agent_type, config_data in agent_models.items():
                    config[agent_type] = (
                        config_data.get("provider", "ollama"),
                        config_data.get("model", "llama3.2")
                    )
        except Exception:
            pass  # Ignore config errors

    return config
```

### 3. Enhanced Session Management

Extend the `Session` class to support agent-specific model assignments:

```python
class Session:
    def __init__(
        self,
        session_id: str | None = None,
        model: str = "llama3.2",
        provider: str = "ollama",
        agent_models: dict[str, tuple[str, str]] | None = None,
        # ... other parameters
    ) -> None:
        # ... existing initialization
        self.agent_models = agent_models or {}

    def get_agent_provider_and_model(self, agent_type: str) -> tuple[str, str]:
        """Get the provider and model for a specific agent type."""
        if agent_type in self.agent_models:
            return self.agent_models[agent_type]
        return self.provider, self.model
```

### 4. Command Line Interface

Add command line options for specifying agent model assignments:

```python
# In cmd/root.py or relevant command files
parser.add_argument(
    "--agent-model",
    action="append",
    help="Assign a model to an agent type (format: type:model)",
    metavar="TYPE:MODEL"
)

parser.add_argument(
    "--agent-provider",
    action="append",
    help="Assign a provider to an agent type (format: type:provider)",
    metavar="TYPE:PROVIDER"
)
```

## Usage Examples

### Setting Agent Models via Environment

```bash
export OLLAMA_CLI_AGENT_CODE_MODEL=mistralai/Mistral-7B-Instruct-v0.3
export OLLAMA_CLI_AGENT_CODE_PROVIDER=hf
export OLLAMA_CLI_AGENT_RESEARCH_MODEL=meta-llama/Meta-Llama-3-8B-Instruct
export OLLAMA_CLI_AGENT_RESEARCH_PROVIDER=claude

ollama-cli run "Write a Python function to calculate factorial"
```

### Setting Agent Models via Configuration File

Create `.ollama/settings.json`:

```json
{
  "agent_models": {
    "code": {
      "model": "mistralai/Mistral-7B-Instruct-v0.3",
      "provider": "hf"
    },
    "research": {
      "model": "meta-llama/Meta-Llama-3-8B-Instruct",
      "provider": "claude"
    }
  }
}
```

### Setting Agent Models Inline

```bash
ollama-cli --agent-model code:mistralai/Mistral-7B-Instruct-v0.3 --agent-provider code:hf run "Write a Python function"
```

## Benefits

1. **Specialization**: Different agents can use models optimized for their specific tasks
2. **Cost Optimization**: Use cheaper models for simple tasks and expensive models for complex ones
3. **Performance Tuning**: Assign faster models to latency-sensitive agents
4. **Flexibility**: Mix and match providers and models as needed

## Integration with Existing Features

This feature integrates with:
- Existing provider routing system
- Context management and sub-agent support
- Token tracking and cost estimation
- Session persistence
- Configuration system

## Backward Compatibility

The feature maintains full backward compatibility:
- Existing configurations continue to work unchanged
- Default behavior remains the same when no agent-specific assignments are configured
- All existing commands function identically without agent model assignments