# CLI Reference

All available commands in Ollama CLI.

---

## Main Commands

| Command | Description | Example |
|---------|-------------|---------|
| `interactive` | Start interactive chat session | `cli-ollama interactive` |
| `run` | Run a one-shot prompt | `cli-ollama run "Hello!"` |
| `list` | List available local models | `cli-ollama list` |
| `serve` | Check Ollama server status | `cli-ollama serve` |
| `version` | Show CLI version | `cli-ollama version` |

---

## Advanced Commands

| Command | Description | Example |
|---------|-------------|---------|
| `install` | Install Ollama automatically | `cli-ollama install` |
| `check` | Check Ollama installation | `cli-ollama check` |
| `rdma` | RDMA device management | `cli-ollama rdma detect` |
| `accelerate` | Hardware acceleration | `cli-ollama accelerate check` |

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
| `--model <name>` | Override the default model for this session |
| `--provider <name>` | Override provider (ollama, claude, gemini, codex, hf) |
| `--api <url>` | Override the Ollama API host URL (e.g. `http://localhost:11434`) |
| `--json` | Output in JSON format |
| `--verbose` | Enable verbose output |
| `--no-hooks` | Disable hooks |
| `--system-prompt <text>` | Set a custom system prompt |
| `--allowed-tools <list>` | Comma-separated list of allowed tool names |
| `-p, --print` | Print response and exit (non-interactive mode) |
| `-r, --resume` | Resume the most recent conversation |
| `--planning` | Enable planning mode for research-focused tasks |
| `--work` | Enable work mode for execution-focused tasks |
| `--bypass` | Bypass permissions and skip interactive prompts |
| `--tui` | Launch the Textual TUI (default for interactive mode) |

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

The orchestrator automatically allocates optimal models to each agent role based on
configured agent model assignments. Roles map to agent types as follows:

| Agent Role | Agent Type | Purpose |
|------------|------------|---------|
| `analyzer_a`, `analyzer_b` | `analysis` | Problem analysis |
| `planner` | `plan` | Solution planning |
| `validator`, `monitor` | `review` | Validation and quality |
| `optimizer` | `debug` | Optimization and edge cases |
| `executor_1`, `executor_2` | `code` | Code generation |
| `reporter`, `cleaner` | `docs` | Documentation and formatting |

Use `/set-agent-model` or environment variables to assign specific models per type.
Unassigned types fall back to the session's current `--model`.

---

## Interactive Commands (Slash Commands)

Type `/` in the REPL to see the full command menu. Key commands:

### Session & Model

| Command | Description |
|---------|-------------|
| `/model` | List available models and current status |
| `/model <name>` | Switch to a new model |
| `/model provider` | List available providers with status |
| `/model provider <name>` | Switch to a new provider |
| `/provider <name>` | Switch provider (shortcut) |
| `/pull <model>` | Pull/download a model from the registry |
| `/pull --force <model>` | Force re-download a model |
| `/status` | Show session status |
| `/clear` | Clear conversation history |
| `/save [name]` | Save session |
| `/load <name>` | Load session |

### Tools

| Command | Description |
|---------|-------------|
| `/tools` | List available built-in tools |
| `/tool <name> [args]` | Invoke a tool (file\_read, shell\_exec, grep\_search, web\_fetch, model\_pull) |
| `/diff` | Show git diff |

### Memory & Context

| Command | Description |
|---------|-------------|
| `/memory [note]` | View or add to project memory |
| `/remember <key> <value>` | Store a memory entry |
| `/recall [query]` | Recall stored memories |
| `/compact` | Force context compaction |

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
cli-ollama --model codellama interactive
```

### Run with cloud provider
```bash
cli-ollama --provider claude run "Review my code"
```

### Use a custom API host
```bash
cli-ollama --api http://myserver:11434 --model llama3.2 interactive
```

### Combine model, provider, and API
```bash
cli-ollama --model glm-5:cloud --provider hf --api http://remote:8080 interactive
```

### JSON output
```bash
cli-ollama --provider gemini list --json
```

### Check RDMA
```bash
cli-ollama rdma detect
```

### Enable MLX acceleration
```bash
cli-ollama accelerate enable mlx
```
