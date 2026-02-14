# Getting Started with Ollama CLI

A complete guide to get up and running with Ollama CLI.

---

## Prerequisites

- **Python 3.11+** - Required for Ollama CLI
- **Ollama** - The local LLM server (automatic installation included)

---

## Installation

### Option 1: One-Line Install (Recommended)

This script automatically installs Ollama if missing:

```bash
curl -fsSL https://raw.githubusercontent.com/muah1987/ollama-cli/main/install.sh | bash
```

### Option 2: PyPI Installation

```bash
# Install from PyPI
pip install ollama_cli

# Or with pipx for isolated installation
pipx install ollama_cli
```

This installs the `ollama-cli` command globally.

### Option 3: Manual Installation from Source

```bash
# Clone the repository
git clone https://github.com/muah1987/ollama-cli.git
cd ollama-cli

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

---

## Quick Start

### 1. Start Ollama Server

If you haven't installed Ollama yet, the install script will do it automatically. Otherwise:

```bash
ollama serve
```

### 2. List Available Models

```bash
ollama-cli list
```

### 3. Start an Interactive Session

```bash
ollama-cli interactive
# or
ollama-cli i
```

### 4. Run a One-Shot Prompt

```bash
ollama-cli run "Explain quantum computing in simple terms"
```

---

## First-Time Setup

### 1. Check Installation

```bash
ollama-cli version
# Should output: ollama-cli v0.1.0
```

### 2. Verify Ollama Server

```bash
ollama-cli serve
# Should show: Ollama is running at http://localhost:11434
```

### 3. Select a Model

```bash
# If no models are installed, pull one:
ollama pull llama3.2
```

> **Auto-discovery:** When you start the CLI, it automatically queries your
> local Ollama server for available models. If the configured model is not
> found locally, the CLI will auto-select the first available model and warn
> you. This means you can start using the CLI immediately after pulling any
> model — no manual configuration needed.

---

## Basic Commands

| Command | Description |
|---------|-------------|
| `ollama-cli interactive` | Start interactive chat session |
| `ollama-cli run "prompt"` | Run a one-shot prompt |
| `ollama-cli list` | List available models |
| `ollama-cli serve` | Check Ollama server status |
| `ollama-cli version` | Show CLI version |

---

## Using Different Models

```bash
# Use a specific model for one command
ollama-cli --model codellama run "Write a Python function"

# Pull a model from registry
ollama pull llama3.2
ollama pull codellama
ollama pull mistral
```

---

## Next Steps

- **Learn about providers**: [Multi-Provider Guide](multi_provider.md)
- **Configure settings**: [Configuration Guide](configuration.md)
- **Explore hooks**: [Hooks System](hooks.md)
- **RDMA Support**: [High-Performance Networking](rdma.md)

---

## Troubleshooting

### Ollama server not starting?

```bash
# Check if Ollama is installed
ollama --version

# If not, install it
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama manually
ollama serve
```

### Connection refused?

```bash
# Make sure Ollama is running
ollama serve &

# Check if port is accessible
curl http://localhost:11434/api/tags
```

### No models available?

```bash
# Pull a model
ollama pull llama3.2

# List installed models
ollama list
```

---

## Getting Help

- Check the [Documentation Index](README.md)
- File an issue on [GitHub](https://github.com/muah1987/ollama-cli/issues)
- Visit the [Ollama documentation](https://ollama.ai/docs)
