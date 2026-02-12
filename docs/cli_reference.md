# CLI Reference

All available commands in Ollama CLI.

---

## Main Commands

| Command | Description | Example |
|---------|-------------|---------|
| `interactive` | Start interactive chat session | `ollama-cli interactive` |
| `run` | Run a one-shot prompt | `ollama-cli run "Hello!"` |
| `list` | List available local models | `ollama-cli list` |
| `serve` | Check Ollama server status | `ollama-cli serve` |
| `version` | Show CLI version | `ollama-cli version` |

---

## Advanced Commands

| Command | Description | Example |
|---------|-------------|---------|
| `install` | Install Ollama automatically | `ollama-cli install` |
| `check` | Check Ollama installation | `ollama-cli check` |
| `rdma` | RDMA device management | `ollama-cli rdma detect` |
| `accelerate` | Hardware acceleration | `ollama-cli accelerate check` |

---
## Agent Commands

In interactive mode, you can use these features to assign specific models to agents:

| Feature | Description | Example |
|--------|-------------|---------|
| `@agent_type` | Prefix any message with @agent_type to use that agent's model | `@code write a Python function` |
| `/set-agent-model` | Assign a provider and model to an agent type | `/set-agent-model code:hf:mistralai/Mistral-7B-Instruct-v0.3` |
| `/list-agent-models` | Show all agent model assignments | `/list-agent-models` |

Examples:
- `@code Write a function to calculate Fibonacci numbers`
- `@research Find papers about transformer architectures`
- `@writer Compose a professional email to a client`

Setting agent models for subsequent sessions:
```bash
export OLLAMA_CLI_AGENT_CODE_PROVIDER=hf
export OLLAMA_CLI_AGENT_CODE_MODEL=mistralai/Mistral-7B-Instruct-v0.3
export OLLAMA_CLI_AGENT_RESEARCH_PROVIDER=claude
export OLLAMA_CLI_AGENT_RESEARCH_MODEL=claude-sonnet-4-20250514
```

Or in `.ollama/settings.json`:
```json
{
  "agent_models": {
    "code": {
      "model": "mistralai/Mistral-7B-Instruct-v0.3",
      "provider": "hf"
    },
    "research": {
      "model": "claude-sonnet-4-20250514",
      "provider": "claude"
    }
  }
}
```

---

## Command Options

### Global Options

| Option | Description |
|--------|-------------|
| `--model <name>` | Override default model |
| `--provider <name>` | Override provider (ollama, claude, gemini, codex, hf) |
| `--json` | Output in JSON format |
| `--verbose` | Enable verbose output |
| `--no-hooks` | Disable hooks |

---

## Provider Options

| Provider | Provider Flag | API Key Env Var |
|----------|---------------|-----------------|
| Ollama (default) | `--provider ollama` | None (or `OLLAMA_API_KEY`) |
| Claude | `--provider claude` | `ANTHROPIC_API_KEY` |
| Gemini | `--provider gemini` | `GEMINI_API_KEY` |
| Codex | `--provider codex` | `OPENAI_API_KEY` |
| Hugging Face | `--provider hf` | `HF_TOKEN` |

---

## MCP Commands

In interactive mode:

| Command | Description |
|---------|-------------|
| `/mcp` | List configured MCP servers |
| `/mcp enable <name>` | Enable an MCP server |
| `/mcp disable <name>` | Disable an MCP server |
| `/mcp tools [name]` | List tools from an MCP server |
| `/mcp invoke <server> <tool> [json]` | Invoke an MCP tool |

## Chain Orchestration

| Command | Description |
|---------|-------------|
| `/chain <prompt>` | Run multi-wave chain orchestration (analyze → plan → execute → finalize) |

---

## RDMA Commands

| Command | Description |
|---------|-------------|
| `rdma detect` | Detect all RDMA devices |
| `rdma status` | Show RDMA status |
| `rdma connect <device>` | Connect to RDMA device |

---

## Accelerate Commands

| Command | Description |
|---------|-------------|
| `accelerate check` | Check available acceleration |
| `accelerate enable <method>` | Enable acceleration |
| `accelerate disable <method>` | Disable acceleration |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error |
| 2 | Connection error |
| 3 | Model not found |

---

## Examples

### Chat with a specific model
```bash
ollama-cli --model codellama interactive
```

### Run with cloud provider
```bash
ollama-cli --provider claude run "Review my code"
```

### JSON output
```bash
ollama-cli --provider gemini list --json
```

### Check RDMA
```bash
ollama-cli rdma detect
```

### Enable MLX acceleration
```bash
ollama-cli accelerate enable mlx
```
