# Ollama CLI

**A full-featured AI coding assistant powered by Ollama with multi-provider support.**

[![PyPI version](https://badge.fury.io/py/ollama-cli.svg)](https://badge.fury.io/py/ollama-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Ollama CLI is a local-first AI coding assistant that runs on your machine with Ollama, with optional cloud provider support for Claude, Gemini, and Codex.

---

## Prerequisites

- **Python 3.11+**
- **[Ollama](https://ollama.ai)** installed and running (`ollama serve`)
- **[uv](https://docs.astral.sh/uv/)** for dependency management

---

## Installation

### One-Line Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/muah1987/ollama-cli/main/install.sh | bash
```

This script will:
1. Install `uv` if not present
2. Clone or update ollama-cli from GitHub
3. Install Python dependencies
4. Detect Ollama and install it if missing

### Manual Install

```bash
# 1. Clone the repository
git clone https://github.com/muah1987/ollama-cli.git
cd ollama-cli

# 2. Install dependencies with uv
uv sync

# 3. Create your environment file
cp .env.sample .env

# 4. Edit .env with your settings
#    At minimum, ensure OLLAMA_HOST points to your Ollama instance
```

---

## Quick Start

```bash
# Start an interactive chat session
ollama-cli interactive

# Run a one-shot prompt
ollama-cli run "explain this code"

# List available local models
ollama-cli list

# Pull a model from registry
ollama-cli pull llama3.2

# Use a specific model
ollama-cli --model codellama run "write a fibonacci function"

# Use a cloud provider
ollama-cli --provider claude run "review this architecture"

# Show version
ollama-cli version
```

---

## Documentation

For detailed documentation on all features, configuration, and advanced usage, see the [docs](docs/) folder:

| Documentation | Description |
|--------------|-------------|
| [Getting Started](docs/getting_started.md) | Installation walkthrough and first steps |
| [Project Overview](docs/project_overview.md) | Features, architecture, hooks, status lines, and contributing |
| [CLI Reference](docs/cli_reference.md) | All available commands |
| [API Reference](docs/api_reference.md) | Ollama and provider APIs |
| [Configuration](docs/configuration.md) | Environment variables and settings |
| [Multi-Provider](docs/multi_provider.md) | Using Claude, Gemini, Codex, Hugging Face |
| [RDMA Support](docs/rdma.md) | High-performance networking |
| [Hooks System](docs/hooks.md) | Lifecycle hooks and customization |
| [Development](docs/development.md) | Contributing and building |

---

## Getting Help

- Check the [Documentation Index](docs/README.md)
- File an issue on [GitHub](https://github.com/muah1987/ollama-cli/issues)
- Visit the [Ollama documentation](https://ollama.ai/docs)

---

## License

MIT License. See [LICENSE](LICENSE) for details.