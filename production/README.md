# Ollama CLI

**A full-featured AI coding assistant powered by Ollama with multi-provider support.**

[![PyPI version](https://badge.fury.io/py/ollama-cli.svg)](https://badge.fury.io/py/ollama-cli)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Ollama CLI gives you a local-first AI coding assistant that runs on your machine with Ollama, while optionally routing to cloud providers like Claude, Gemini, and Codex when you need them. Built with the GOTCHA Framework and ATLAS Workflow for reliable, deterministic execution.

---

## Features

- **Multi-Provider Routing** -- Seamlessly switch between Ollama (local/cloud), Claude, Gemini, and Codex with a single flag
- **Auto-Compact Context** -- Automatically compacts conversation history at 85% context usage to keep sessions running smoothly
- **Hook System** -- 7 lifecycle hooks let you extend behavior at every stage of execution
- **Status Lines** -- Real-time dashboards showing token usage, provider health, and session metrics
- **Interactive REPL** -- Full chat mode with streaming responses and rich terminal output
- **Token Tracking** -- Track token usage and cost estimation across all providers
- **Session Persistence** -- Save and resume conversations with automatic session management
- **RDMA Acceleration** -- High-performance networking with InfiniBand, RoCE, iWARP, USB/RDMA, and Thunderbolt support
- **Apple Silicon MLX** -- Metal Performance Shaders acceleration for macOS
- **EXO Distributed Execution** -- Multi-node distributed computing support

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
cd ollama-cli/production

# 2. Install dependencies with uv
uv sync

# 3. Create your environment file
cp .env.sample .env

# 4. Edit .env with your settings
#    At minimum, ensure OLLAMA_HOST points to your Ollama instance
```

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai) installed and running (`ollama serve`)
- [uv](https://docs.astral.sh/uv/) for dependency management

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

# Show model details
ollama-cli show llama3.2

# Check Ollama server status
ollama-cli serve

# Show current configuration
ollama-cli config

# Show session status
ollama-cli status

# Use a specific model
ollama-cli --model codellama run "write a fibonacci function"

# Use a cloud provider
ollama-cli --provider claude run "review this architecture"

# Show version
ollama-cli version

# Enable RDMA acceleration
ollama-cli accelerate enable rdma

# Check RDMA devices
ollama-cli rdma detect
```

---

## Documentation

| Documentation | Description |
|--------------|-------------|
| [Getting Started](docs/README.md) | Installation and first steps |
| [CLI Reference](docs/cli_reference.md) | All available commands |
| [API Reference](docs/api_reference.md) | Ollama and provider APIs |
| [Configuration](docs/configuration.md) | Environment variables and settings |
| [Multi-Provider](docs/multi_provider.md) | Using Claude, Gemini, Codex |
| [RDMA Support](docs/rdma.md) | High-performance networking |
| [Hooks System](docs/hooks.md) | Lifecycle hooks and customization |
| [Development](docs/development.md) | Contributing and building |

---

## Multi-Provider Setup

Ollama CLI defaults to your local Ollama instance but can route requests to cloud providers when needed. Each provider requires its own API key.

### Claude (Anthropic)

```bash
# In your .env file
ANTHROPIC_API_KEY=sk-ant-...

# Use it
ollama-cli --provider claude run "explain this error"
```

### Gemini (Google)

```bash
# In your .env file
GEMINI_API_KEY=AI...

# Use it
ollama-cli --provider gemini run "summarize this file"
```

### Codex (OpenAI)

```bash
# In your .env file
OPENAI_API_KEY=sk-...

# Use it
ollama-cli --provider codex run "refactor this function"
```

### Provider Selection

You can set a default provider in `.env` or override per-command:

```bash
# Set default in .env
OLLAMA_CLI_PROVIDER=claude

# Override per-command
ollama-cli --provider ollama run "quick local question"
```

---

## Hook System

Ollama CLI provides 7 lifecycle hooks that let you extend and customize behavior at every stage of execution. Hooks are configured in `.ollama/settings.json` and execute shell commands with JSON payloads on stdin.

| Hook | When It Fires | Use Case |
|------|---------------|----------|
| `PreToolUse` | Before a tool is executed | Validate inputs, enforce policies, gate dangerous operations |
| `PostToolUse` | After a tool completes | Log results, transform output, trigger follow-up actions |
| `SessionStart` | When a new session begins | Initialize state, load context, set up environment |
| `SessionEnd` | When a session ends | Save summaries, persist memory, clean up resources |
| `PreCompact` | Before context compaction | Extract key information before context is trimmed |
| `Stop` | When the assistant stops | Final output processing, cleanup |
| `Notification` | On notable events | Alerts, logging, external integrations |

---

## Status Lines

Three built-in status line scripts provide real-time visibility into your session:

| Status Line | Description |
|-------------|-------------|
| **Token Counter** | Displays current token usage (prompt + completion), cost estimate, and context utilization percentage |
| **Provider Health** | Shows connectivity status for each configured provider (local Ollama, cloud endpoints) |
| **Full Dashboard** | Combined view with token metrics, provider status, session duration, and message count |

Status line scripts are located in `.ollama/status_lines/` and can be customized.

---

## Architecture

### GOTCHA Framework

Ollama CLI is built on the GOTCHA Framework, a 6-layer architecture for agentic systems:

| Layer | Directory | Purpose |
|-------|-----------|---------|
| **Goals** | `goals/` | Process definitions -- what needs to happen |
| **Orchestration** | -- | The AI manager that coordinates execution |
| **Tools** | `tools/` | Deterministic scripts that do the actual work |
| **Context** | `context/` | Reference material and domain knowledge |
| **Hard Prompts** | `hardprompts/` | Reusable instruction templates |
| **Args** | `args/` | Behavior settings that shape how the system acts |

### ATLAS Workflow

Development follows the ATLAS Workflow:

1. **Architect** -- Design the structure and interfaces
2. **Trace** -- Map dependencies and data flow
3. **Link** -- Connect components and wire integrations
4. **Assemble** -- Build and integrate the full system
5. **Stress-test** -- Validate under real conditions

### Source Structure

```
ollama-cli/
  cmd/
    root.py              -- Main CLI entry point
    run.py               -- Run model with streaming
    list.py              -- List local models
    pull.py              -- Pull model from registry
    show.py              -- Show model details
    serve.py             -- Check Ollama server status
    config.py            -- Show/set configuration
    status.py            -- Show session status
    version.py           -- Show CLI version
    interactive.py       -- Interactive REPL mode
    create.py            -- Create model from Modelfile
    rm.py                -- Delete local model
    cp.py                -- Copy model
    ps.py                -- List running models
    stop.py              -- Stop running model
  api/
    ollama_client.py     -- Ollama API client (native + OpenAI-compatible)
    provider_router.py   -- Multi-provider routing (Ollama/Claude/Gemini/Codex)
    config.py            -- Configuration management
  model/
    session.py           -- Session state management
  server/
    hook_runner.py       -- Hook execution engine
  runner/
    context_manager.py   -- Auto-compact context management
    token_counter.py     -- Token tracking with cost estimation
  .ollama/
    settings.json        -- Hook configuration
    hooks/               -- 7 lifecycle hook scripts
    status_lines/        -- 3 status line scripts + utilities
```

---

## Contributing

Contributions are welcome. Here is how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests and linting (`uv run ruff check cmd/ api/ model/ server/ runner/`)
5. Commit your changes (`git commit -m "Add my feature"`)
6. Push to your branch (`git push origin feature/my-feature`)
7. Open a Pull Request

Please follow the existing code style and include tests for new functionality.

### Getting Help

- Check the [Documentation Index](docs/README.md)
- File an issue on [GitHub](https://github.com/muah1987/ollama-cli/issues)
- Visit the [Ollama documentation](https://ollama.ai/docs)

---

## License

MIT License. See [LICENSE](LICENSE) for details.