# Ollama CLI

**A full-featured AI coding assistant powered by Ollama with multi-provider support.**

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

---

## Installation

### One-Line Install

```bash
curl -fsSL https://raw.githubusercontent.com/muah1987/ollama-cli/main/install.sh | bash
```

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

# Create model from Modelfile
ollama-cli create mymodel -f Modelfile

# Delete local model
ollama-cli rm mymodel

# Copy model
ollama-cli cp mymodel mymodel-copy

# List running models
ollama-cli ps

# Stop running model
ollama-cli stop llama3.2
```

---

## Configuration

All configuration is done through environment variables in your `.env` file.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Default model to use |
| `OLLAMA_CONTEXT_LENGTH` | `4096` | Context window size in tokens |
| `OLLAMA_CLI_PROVIDER` | `ollama` | Default provider (`ollama`, `claude`, `gemini`, `codex`) |
| `ANTHROPIC_API_KEY` | -- | API key for Claude provider |
| `GEMINI_API_KEY` | -- | API key for Gemini provider |
| `OPENAI_API_KEY` | -- | API key for Codex/OpenAI provider |
| `AUTO_COMPACT` | `true` | Enable automatic context compaction |
| `COMPACT_THRESHOLD` | `0.85` | Context usage ratio that triggers compaction |
| `HOOKS_ENABLED` | `true` | Enable the hook system |

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
|---|---|---|
| `PreToolUse` | Before a tool is executed | Validate inputs, enforce policies, gate dangerous operations |
| `PostToolUse` | After a tool completes | Log results, transform output, trigger follow-up actions |
| `SessionStart` | When a new session begins | Initialize state, load context, set up environment |
| `SessionEnd` | When a session ends | Save summaries, persist memory, clean up resources |
| `PreCompact` | Before context compaction | Extract key information before context is trimmed |
| `Stop` | When the assistant stops | Final output processing, cleanup |
| `Notification` | On notable events | Alerts, logging, external integrations |

### Hook Configuration

Hooks are defined in `.ollama/settings.json`:

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

Each hook command receives a JSON payload on stdin and can return JSON on stdout to influence execution (e.g., permission decisions, additional context, or updated inputs).

---

## Status Lines

Three built-in status line scripts provide real-time visibility into your session:

| Status Line | Description |
|---|---|
| **Token Counter** | Displays current token usage (prompt + completion), cost estimate, and context utilization percentage |
| **Provider Health** | Shows connectivity status for each configured provider (local Ollama, cloud endpoints) |
| **Full Dashboard** | Combined view with token metrics, provider status, session duration, and message count |

Status line scripts are located in `.ollama/status_lines/` and can be customized or extended.

---

## Architecture

### GOTCHA Framework

Ollama CLI is built on the GOTCHA Framework, a 6-layer architecture for agentic systems:

| Layer | Directory | Purpose |
|---|---|---|
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

---

## License

MIT License. See [LICENSE](LICENSE) for details.
