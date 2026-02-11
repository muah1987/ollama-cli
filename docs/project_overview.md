# Ollama CLI — Project Overview

**A full-featured AI coding assistant powered by Ollama with multi-provider support.**

Ollama CLI gives you a local-first AI coding assistant that runs on your machine with Ollama, while optionally routing to cloud providers like Claude, Gemini, and Codex when you need them. Built with the GOTCHA Framework and ATLAS Workflow for reliable, deterministic execution.

---

## Features

- **Multi-Provider Routing** -- Seamlessly switch between Ollama (local/cloud), Claude, Gemini, Codex, and Hugging Face with a single flag
- **Agent Model Assignment** -- Assign specific models to agent types for specialized tasks (@code, @research, etc.)
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

### Hugging Face

```bash
# In your .env file
HF_TOKEN=your-huggingface-token

# Use it
ollama-cli --provider hf run "answer this question"
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
    provider_router.py   -- Multi-provider routing (Ollama/Claude/Gemini/Codex/HuggingFace)
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

## Getting Help

- Check the [Documentation Index](README.md)
- File an issue on [GitHub](https://github.com/muah1987/ollama-cli/issues)
- Visit the [Ollama documentation](https://ollama.ai/docs)

---

## License

MIT License. See [LICENSE](../LICENSE) for details.
