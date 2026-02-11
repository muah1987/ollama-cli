# Configuration Guide

Configure Ollama CLI to suit your needs.

---

## Environment Variables

### Ollama Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Default model to use |
| `OLLAMA_CONTEXT_LENGTH` | `4096` | Context window size in tokens |

### Provider Configuration

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key for Claude provider |
| `GEMINI_API_KEY` | API key for Gemini provider |
| `OPENAI_API_KEY` | API key for Codex/OpenAI provider |
| `OLLAMA_CLI_PROVIDER` | Default provider (ollama, claude, gemini, codex) |

### Context Compaction

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTO_COMPACT` | `true` | Enable automatic context compaction |
| `COMPACT_THRESHOLD` | `0.85` | Context usage ratio triggering compaction |
| `KEEP_LAST_N` | `4` | Number of messages to preserve during compaction |

### Hooks Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOOKS_ENABLED` | `true` | Enable the hook system |
| `OLLAMA_PROJECT_DIR` | Current directory | Project directory for hooks |

---

## Configuration Files

### `.env` File

Create a `.env` file in your project directory:

```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AI...
OPENAI_API_KEY=sk-...
OLLAMA_CLI_PROVIDER=ollama
AUTO_COMPACT=true
COMPACT_THRESHOLD=0.85
HOOKS_ENABLED=true
```

### `.ollama/settings.json`

Configuration for the hook system:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python .ollama/hooks/session_start.py"
          }
        ]
      }
    ]
  }
}
```

---

## Provider Settings

### Setting Default Provider

Via environment variable:
```bash
export OLLAMA_CLI_PROVIDER=claude
```

Via code:
```python
from api.config import get_config
cfg = get_config()
cfg.provider = "claude"
```

### Switching Providers

```bash
# Use Claude for one command
ollama-cli --provider claude run "Explain this"

# Use Gemini for one command
ollama-cli --provider gemini run "Summarize this"
```

---

## Advanced Configuration

### Custom Context Length

```bash
# Set custom context length
export OLLAMA_CONTEXT_LENGTH=8192

# Or use a specific model with longer context
ollama-cli --model llama3.2-8b interactive
```

### Disabling Auto-Compact

```bash
export AUTO_COMPACT=false
```

---

## Hook Configuration

The hook system allows customization at 7 lifecycle events:

| Hook | When It Fires |
|------|---------------|
| `SessionStart` | When a session begins |
| `SessionEnd` | When a session ends |
| `PreToolUse` | Before tool execution |
| `PostToolUse` | After tool completes |
| `PreCompact` | Before context compaction |
| `Stop` | When the assistant stops |
| `Notification` | On notable events |

See [Hooks System](hooks.md) for detailed configuration.

---

## Status Lines

Three built-in status line scripts:

| Status Line | Description |
|-------------|-------------|
| `status_line_token_counter` | Token usage and cost |
| `status_line_provider_health` | Provider availability |
| `status_line_full_dashboard` | Combined metrics |

---

## Environment Examples

### Cloud-Only Setup

```bash
# Disable local Ollama, use only cloud providers
OLLAMA_CLI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-...
OLLAMA_HOST=disabled
```

### Hybrid Setup

```bash
# Use local Ollama with Claude as fallback
OLLAMA_CLI_PROVIDER=ollama
ANTHROPIC_API_KEY=sk-ant-...
```

### Development Setup

```bash
# Enable verbose logging
OLLAMA_CLI_LOG_LEVEL=debug

# Disable hooks for debugging
HOOKS_ENABLED=false
```
