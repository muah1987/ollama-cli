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

> **Model auto-discovery:** At startup the CLI queries your local Ollama server
> and verifies that `OLLAMA_MODEL` is available. If it is not found, the CLI
> auto-selects the first available local model and prints a warning. Partial
> names work too — `llama3.2` resolves to `llama3.2:latest` when present.

### Provider Configuration

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | API key for Claude provider |
| `GEMINI_API_KEY` | API key for Gemini provider |
| `OPENAI_API_KEY` | API key for Codex/OpenAI provider |
| `HF_TOKEN` | API key for Hugging Face provider |
| `GH_TOKEN` | GitHub token (auto-enables GitHub MCP server) |
| `OLLAMA_CLI_PROVIDER` | Default provider (ollama, claude, gemini, codex, hf) |

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
HF_TOKEN=hf_...
GH_TOKEN=ghp_...
OLLAMA_CLI_PROVIDER=ollama
AUTO_COMPACT=true
COMPACT_THRESHOLD=0.85
HOOKS_ENABLED=true
```

### `.ollama/settings.json`

Configuration for the hook system and multi-model agent assignments:

```json
{
  "hooks": {
    "Setup": [...],
    "SessionStart": [...],
    "SessionEnd": [...],
    "UserPromptSubmit": [...],
    "PreToolUse": [...],
    "PostToolUse": [...],
    "PostToolUseFailure": [...],
    "PermissionRequest": [...],
    "SkillTrigger": [...],
    "PreCompact": [...],
    "Stop": [...],
    "SubagentStart": [...],
    "SubagentStop": [...],
    "Notification": [...]
  },
  "agent_models": {
    "code": {"provider": "ollama", "model": "codestral:latest"},
    "review": {"provider": "claude", "model": "claude-sonnet"},
    "test": {"provider": "gemini", "model": "gemini-flash"},
    "plan": {"provider": "ollama", "model": "llama3.2"},
    "docs": {"provider": "hf", "model": "mistral-7b"}
  }
}
```

### `.ollama/mcp.json`

MCP (Model Context Protocol) server configuration:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": ""},
      "enabled": false
    },
    "docker": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "mcp/docker"],
      "enabled": false
    }
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

The hook system allows customization at 13 lifecycle events:

| Hook | When It Fires |
|------|---------------|
| `Setup` | On init or maintenance |
| `SessionStart` | When a session begins |
| `SessionEnd` | When a session ends |
| `UserPromptSubmit` | Before processing user input |
| `PreToolUse` | Before tool execution |
| `PostToolUse` | After tool completes |
| `PostToolUseFailure` | When a tool fails |
| `PermissionRequest` | On permission dialog |
| `SkillTrigger` | When a skill triggers a hook |
| `PreCompact` | Before context compaction |
| `Stop` | When model finishes responding |
| `SubagentStart` | When a subagent spawns |
| `SubagentStop` | When a subagent finishes |
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
