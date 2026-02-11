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

## Command Options

### Global Options

| Option | Description |
|--------|-------------|
| `--model <name>` | Override default model |
| `--provider <name>` | Override provider (ollama, claude, gemini, codex) |
| `--json` | Output in JSON format |
| `--verbose` | Enable verbose output |
| `--no-hooks` | Disable hooks |

---

## Provider Options

| Provider | Provider Flag | API Key Env Var |
|----------|---------------|-----------------|
| Ollama (default) | `--provider ollama` | None |
| Claude | `--provider claude` | `ANTHROPIC_API_KEY` |
| Gemini | `--provider gemini` | `GEMINI_API_KEY` |
| Codex | `--provider codex` | `OPENAI_API_KEY` |

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
