# Ollama CLI

**Get up and running with LLMs.**

Ollama CLI is a Python-based AI coding assistant powered by Ollama with multi-provider support. Seamlessly switch between local models and cloud providers like Claude, Gemini, and Codex.

---

## Installation

### Install with pip

```bash
pip install ollama-cli
```

### Install from source

```bash
git clone https://github.com/muah1987/ollama-cli.git
cd ollama-cli
pip install -e .
```

### Install with uv

```bash
uv pip install ollama-cli
```

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running

---

## Quick Start

```bash
# List available models
ollama-cli list

# Start an interactive chat
ollama-cli run llama3.2

# Run a one-shot prompt
ollama-cli run llama3.2 "explain recursion in Python"

# Check server status
ollama-cli serve

# Create a model from a Modelfile
ollama-cli create mymodel

# Pull a model
ollama-cli pull llama3.2

# Show model details
ollama-cli show llama3.2

# List running models
ollama-cli ps

# Stop a running model
ollama-cli stop llama3.2

# Copy a model
ollama-cli cp llama3.2 mycopy

# Delete a model
ollama-cli rm mymodel
```

---

## CLI Reference

| Command | Description |
|---------|-------------|
| `run` | Run a model interactively |
| `create` | Create a model from a Modelfile |
| `pull` | Pull a model from a registry |
| `show` | Show model details |
| `list` | List available local models |
| `ps` | List running models |
| `stop` | Stop a running model |
| `rm` | Delete a local model |
| `cp` | Copy a local model |
| `serve` | Check Ollama server status |
| `chat` | Start an interactive chat session |
| `config` | Show/set configuration |
| `status` | Show current session status |
| `version` | Show CLI version |

---

## Configuration

Ollama CLI can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Default model to use |
| `OLLAMA_CONTEXT_LENGTH` | `4096` | Context window size in tokens |
| `OLLAMA_CLI_PROVIDER` | `ollama` | Default provider (ollama, claude, gemini, codex) |
| `ANTHROPIC_API_KEY` | - | API key for Claude provider |
| `GEMINI_API_KEY` | - | API key for Gemini provider |
| `OPENAI_API_KEY` | - | API key for Codex/OpenAI provider |
| `AUTO_COMPACT` | `true` | Enable automatic context compaction |
| `COMPACT_THRESHOLD` | `0.85` | Context usage ratio that triggers compaction |
| `HOOKS_ENABLED` | `true` | Enable the hook system |

---

## Multi-Provider Setup

### Claude (Anthropic)

```bash
export ANTHROPIC_API_KEY="your-api-key"
ollama-cli --provider claude run "explain this code"
```

### Gemini (Google)

```bash
export GEMINI_API_KEY="your-api-key"
ollama-cli --provider gemini run "summarize this file"
```

### Codex (OpenAI)

```bash
export OPENAI_API_KEY="your-api-key"
ollama-cli --provider codex run "refactor this function"
```

---

## Examples

### Interactive Chat

```bash
ollama-cli run llama3.2
> Hello! How can I help you today?
> Write a Python function to calculate Fibonacci numbers.
```

### One-Shot Prompt

```bash
ollama-cli run llama3.2 "Write a Python function to sort a list"
```

### Streaming Output

```bash
ollama-cli run llama3.2 --stream "Explain quantum computing"
```

### Custom Context

```bash
OLLAMA_CONTEXT_LENGTH=8192 ollama-cli run llama3.2 "Summarize a long document"
```

### Different Provider

```bash
ollama-cli --provider claude run "Review this code for security issues"
```

---

## Model Library

Available models depend on your Ollama installation. See [Ollama's model library](https://ollama.ai/library) for popular models:

- `llama3.2` - Meta's latest Llama
- `codellama` - Code-specialized model
- `mistral` - Lightweight and efficient
- `gemma` - Google's open model
- And many more...

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License. See [LICENSE](LICENSE) for details.