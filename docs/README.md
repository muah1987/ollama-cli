# Qarin CLI

**A full-featured AI coding assistant powered by Ai Models with multi-provider support.**

[![PyPI version](https://badge.fury.io/py/qarin-cli.svg)](https://badge.fury.io/py/qarin-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Qarin CLI is a local-first AI coding assistant that runs on your machine with Ollama, with optional cloud provider support for Claude, Gemini, Codex, and Hugging Face.

---

## Prerequisites

- **Python 3.11+**
- **[Ollama](https://ollama.ai)** installed and running (`ollama serve`)
- **[uv](https://docs.astral.sh/uv/)** for dependency management

---

## Installation

### One-Line Install (Recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/muah1987/qarin-cli/main/install.sh | bash
```

This script will:
1. Install `uv` if not present
2. Clone or update qarin-cli from GitHub
3. Install Python dependencies
4. Detect Ollama and install it if missing

### Manual Install

```bash
# 1. Clone the repository
git clone https://github.com/muah1987/qarin-cli.git
cd qarin-cli

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
qarin-cli interactive

# Run a one-shot prompt
qarin-cli run "explain this code"

# List available local models
qarin-cli list

# Pull a model from registry
qarin-cli pull llama3.2

# Use a specific model
qarin-cli --model codellama run "write a fibonacci function"

# Use a cloud provider
qarin-cli --provider claude run "review this architecture"

# Show version
qarin-cli version
```

---

## Documentation

For detailed documentation on all features, configuration, and advanced usage, see the [docs](docs/) folder:

| Documentation | Description |
|--------------|-------------|
| [Getting Started](getting_started.md) | Installation walkthrough and first steps |
| [Project Overview](project_overview.md) | Features, architecture, hooks, status lines, and contributing |
| [CLI Reference](cli_reference.md) | All available commands |
| [API Reference](api_reference.md) | Ollama and provider APIs |
| [Configuration](configuration.md) | Environment variables and settings |
| [Multi-Provider](multi_provider.md) | Using Claude, Gemini, Codex, Hugging Face |
| [Agent Models](agent_model_assignment.md) | Multi-model agent assignment |
| [RDMA Support](rdma.md) | High-performance networking |
| [Hooks System](hooks.md) | 14 lifecycle hooks and customization |
| [MCP Integration](mcp.md) | GitHub, Docker, and other MCP servers |
| [Development](development.md) | Contributing and building |
| [Testing](testing_coverage.md) | Testing procedures and code coverage |

---

## Getting Help

- Check the [Documentation Index](README.md)
- File an issue on [GitHub](https://github.com/muah1987/qarin-cli/issues)
- Visit the [Ollama documentation](https://ollama.ai/docs)

---

## License

MIT License. See [LICENSE](LICENSE) for details.
