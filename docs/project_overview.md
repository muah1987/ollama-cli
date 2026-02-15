# Qarin CLI — Project Overview

**A full-featured AI coding assistant powered by Ai Models with multi-provider support.**

Qarin CLI gives you a local-first AI coding assistant that runs on your machine with Ollama, while optionally routing to cloud providers like Claude, Gemini, and Codex when you need them. Built with the GOTCHA Framework and ATLAS Workflow for reliable, deterministic execution.

---

## Features

- **Multi-Provider Routing** -- Seamlessly switch between Ollama (local/cloud), Claude, Gemini, Codex, and Hugging Face with a single flag
- **Model Auto-Discovery** -- Automatically detects locally available Ollama models at startup and resolves the best available model
- **Multi-Model Agent Assignment** -- Assign 5+ models from mixed providers to agent types (@code, @review, @test, @plan, @docs)
- **Provider Fallback** -- Automatic fallback chain uses your session's selected model, not a hardcoded default
- **Auto-Compact Context** -- Automatically compacts conversation history at 85% context usage to keep sessions running smoothly
- **13 Lifecycle Hooks** -- Full hook system: Setup, SessionStart/End, UserPromptSubmit, PreToolUse, PostToolUse, PostToolUseFailure, PermissionRequest, SkillTrigger, PreCompact, Stop, SubagentStart/Stop, Notification
- **Skill→Hook→.py Pipeline** -- Skills trigger hooks, hooks trigger Python scripts for extensible automation
- **MCP Integration** -- Connect to GitHub MCP, Docker MCP, filesystem, and memory MCP servers
- **Chain Orchestration** -- Multi-wave subagent pipeline: analyze → plan/validate/optimize → execute → finalize
- **Status Lines** -- Real-time dashboards showing token usage, provider health, and session metrics with job status
- **Interactive REPL** -- Full chat mode with streaming responses and persistent bottom status bar
- **Token Tracking** -- Track token usage and cost estimation across all providers
- **Session Persistence** -- Save and resume conversations with automatic session management
- **RDMA Acceleration** -- High-performance networking with InfiniBand, RoCE, iWARP, USB/RDMA, and Thunderbolt support
- **Apple Silicon MLX** -- Metal Performance Shaders acceleration for macOS
- **EXO Distributed Execution** -- Multi-node distributed computing support
- **Dependabot** -- Automated dependency updates with auto-merge for patch/minor versions

---

## Multi-Provider Setup

Qarin CLI defaults to your local Ollama instance but can route requests to cloud providers when needed. Each provider requires its own API key.

### Claude (Anthropic)

```bash
# In your .env file
ANTHROPIC_API_KEY=sk-ant-...

# Use it
qarin-cli --provider claude run "explain this error"
```

### Gemini (Google)

```bash
# In your .env file
GEMINI_API_KEY=AI...

# Use it
qarin-cli --provider gemini run "summarize this file"
```

### Codex (OpenAI)

```bash
# In your .env file
OPENAI_API_KEY=sk-...

# Use it
qarin-cli --provider codex run "refactor this function"
```

### Hugging Face

```bash
# In your .env file
HF_TOKEN=your-huggingface-token

# Use it
qarin-cli --provider hf run "answer this question"
```

### Provider Selection

You can set a default provider in `.env` or override per-command:

```bash
# Set default in .env
QARIN_CLI_PROVIDER=claude

# Override per-command
qarin-cli --provider ollama run "quick local question"
```

---

## Hook System

Qarin CLI provides 14 lifecycle hooks that let you extend and customize behavior at every stage of execution. Hooks follow the **skill→hook→.py pipeline** and are configured in `.qarin/settings.json`.

| # | Hook | When It Fires | Use Case |
|---|------|---------------|----------|
| 1 | `Setup` | On init or periodic maintenance | Load git status, inject context, environment persistence |
| 2 | `SessionStart` | When a new session begins | Initialize state, load context, set up environment |
| 3 | `SessionEnd` | When a session ends | Save summaries, persist memory, clean up resources |
| 4 | `UserPromptSubmit` | Before processing user input | Validate input, security filtering, prompt logging |
| 5 | `PreToolUse` | Before a tool is executed | Validate inputs, enforce policies, gate dangerous operations |
| 6 | `PostToolUse` | After a tool completes | Log results, transform output, trigger follow-up actions |
| 7 | `PostToolUseFailure` | When a tool execution fails | Structured error logging with full context |
| 8 | `PermissionRequest` | On permission dialog | Permission auditing, auto-allow read-only ops |
| 9 | `SkillTrigger` | When a skill invokes a hook | Skill→hook routing, pre-processing, logging |
| 10 | `PreCompact` | Before context compaction | Extract key information before context is trimmed |
| 11 | `Stop` | When the model finishes responding | Final output processing, cleanup |
| 12 | `SubagentStart` | When a subagent spawns | Subagent spawn logging, resource tracking |
| 13 | `SubagentStop` | When a subagent finishes | Subagent completion logging, result aggregation |
| 14 | `Notification` | On notable events | Alerts, logging, external integrations |

---

## Status Lines

Three built-in status line scripts provide real-time visibility into your session:

| Status Line | Description |
|-------------|-------------|
| **Token Counter** | Displays current token usage (prompt + completion), cost estimate, and context utilization percentage |
| **Provider Health** | Shows connectivity status for each configured provider (local Ollama, cloud endpoints) |
| **Full Dashboard** | Combined view with token metrics, provider status, session duration, and message count |

Status line scripts are located in `.qarin/status_lines/` and can be customized.

---

## Architecture

### GOTCHA Framework

Qarin CLI is built on the GOTCHA Framework, a 6-layer architecture for agentic systems:

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
qarin-cli/
  qarin_cmd/
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
    install.py           -- Install Ollama automatically
    onboarding.py        -- First-time onboarding flow
    accelerate.py        -- Hardware acceleration management
    rdma.py              -- RDMA device management
  api/
    ollama_client.py     -- Ollama API client (native + OpenAI-compatible)
    provider_router.py   -- Multi-provider routing (Ollama/Claude/Gemini/Codex/HuggingFace)
    config.py            -- Configuration management
    mcp_client.py        -- MCP (Model Context Protocol) client
    rdma_client.py       -- RDMA networking client
  model/
    session.py           -- Session state management
  server/
    hook_runner.py       -- Hook execution engine
  runner/
    context_manager.py   -- Auto-compact context management
    token_counter.py     -- Token tracking with cost estimation
    intent_classifier.py -- Intent classification for agent routing
    chain_controller.py  -- Chain orchestration controller
    agent_comm.py        -- Agent communication layer
    memory_layer.py      -- Memory persistence layer
    rdma_manager.py      -- RDMA connection manager
  tui/
    app.py               -- Textual TUI application
    command_processor.py -- Slash-command dispatch and registry
    screens/             -- TUI screens (chat, help, settings)
    widgets/             -- TUI widgets (chat_message, input_area, status_panel, spinner, intent_badge, sidebar)
    styles/              -- TUI stylesheets (app.tcss, dark.tcss, light.tcss)
  skills/
    tools.py             -- Built-in tool definitions
    exo/                 -- EXO distributed execution skill
    mlx/                 -- Apple Silicon MLX acceleration skill
    rdma/                -- RDMA networking skill
  .qarin/
    settings.json        -- Hook config + agent_models + TUI settings
    hooks/               -- 14 lifecycle hook scripts (skill→hook→.py pipeline)
    status_lines/        -- 3 status line scripts + utilities
    mcp.json             -- MCP server configuration
    chain.json           -- Chain orchestration configuration
    memory.json          -- Persistent memory store
```

---

## Contributing

Contributions are welcome. Here is how to get started:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Run tests and linting (`uv run ruff check qarin_cmd/ api/ model/ server/ runner/`)
5. Commit your changes (`git commit -m "Add my feature"`)
6. Push to your branch (`git push origin feature/my-feature`)
7. Open a Pull Request

Please follow the existing code style and include tests for new functionality.

---

## Getting Help

- Check the [Documentation Index](README.md)
- File an issue on [GitHub](https://github.com/muah1987/qarin-cli/issues)
- Visit the [Ollama documentation](https://ollama.ai/docs)

---

## License

MIT License. See [LICENSE](../LICENSE) for details.
