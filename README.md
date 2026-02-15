# Qarin CLI

[![PyPI version](https://img.shields.io/pypi/v/qarin-cli.svg)](https://pypi.org/project/qarin-cli/)
[![Build & Test](https://github.com/muah1987/qarin-cli/actions/workflows/build-test.yml/badge.svg)](https://github.com/muah1987/qarin-cli/actions/workflows/build-test.yml)
[![codecov](https://codecov.io/gh/muah1987/qarin-cli/branch/main/graph/badge.svg)](https://codecov.io/gh/muah1987/qarin-cli)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

An open-source AI coding assistant with Textual TUI interface that runs in your terminal, powered by [Ollama](https://ollama.ai) with multi-provider support for Claude, Gemini, OpenAI Codex, and Hugging Face.

<p align="center">
  <strong>Local-first</strong> · <strong>Multi-provider</strong> · <strong>14 lifecycle hooks</strong> · <strong>MCP integration</strong> · <strong>Chain orchestration</strong> · <strong>Built-in tools</strong>
</p>

---

## Quick Start

### Install

**Via installer script (recommended):**

```bash
curl -fsSL https://raw.githubusercontent.com/muah1987/qarin-cli/main/install.sh | bash
```

This installs `qarin-cli` to `~/.local/bin/`, sets up dependencies, and installs Ollama if needed.

**Via PyPI:**

```bash
pip install qarin-cli
# or
pipx install qarin-cli
```

This installs the `qarin-cli` command globally.

### Start chatting

```bash
# Start interactive session (default)
qarin-cli

# Or with a direct prompt
qarin-cli "Explain this codebase to me"

# Non-interactive mode
qarin-cli -p "Write a Python function that reverses a string"

# Resume last session
qarin-cli --resume
```

### Pipe input

```bash
echo "Fix the bug in this code" | qarin-cli
cat error.log | qarin-cli -p "What went wrong?"
git diff | qarin-cli -p "Review these changes"
```

---

## Usage

```
Usage: qarin-cli [options] [command] [prompt]

Options:
  -v, --version                   Show version
  -p, --print                     Print response and exit (non-interactive)
  -r, --resume                    Resume the most recent conversation
  --model MODEL                   Override model (e.g. llama3.2, codellama)
  --provider {ollama,claude,gemini,codex,hf}
                                  Override provider
  --system-prompt PROMPT          Custom system prompt
  --output-format {text,json,markdown}
                                  Output format
  --allowed-tools TOOLS           Comma-separated tool whitelist
  --json                          JSON output mode
  --no-hooks                      Disable lifecycle hooks
  --verbose                       Verbose output

Commands:
  chat, interactive (i)           Start interactive REPL session
  run PROMPT                      Run a one-shot prompt
  list                            List available local models
  pull MODEL                      Pull a model from registry
  show MODEL                      Show model details
  serve                           Check Ollama server status
  config [get|set] [key] [value]  Show/set configuration
  status                          Show current session status
  version                         Show CLI version
  create, rm, cp, ps, stop        Ollama model management commands
```

---

## Interactive Commands

Inside the REPL, use slash commands:

| Command | Description |
|---------|-------------|
| `/model <name>` | Switch active model |
| `/provider <name>` | Switch provider (ollama, claude, gemini, codex, hf) |
| `/status` | Show session status, tokens, context, auto-compact state |
| `/compact` | Force context compaction to free space |
| `/clear` | Clear conversation history |
| `/save [name]` | Save session to file |
| `/load <name>` | Load session from file |
| `/history` | Show conversation history |
| `/memory [note]` | View or add to project memory (QARIN.md) |
| `/tools` | List available built-in tools |
| `/tool <name> ...` | Invoke a tool (file_read, shell_exec, grep_search, ...) |
| `/diff` | Show git diff of working directory |
| `/config [k] [v]` | View or set configuration |
| `/bug [desc]` | File a bug report with session context |
| `/team_planning <desc>` | Generate an implementation plan → `specs/` |
| `/build <plan>` | Execute a saved plan file |
| `/resume [id]` | List or resume previous tasks |
| `/set-agent-model <type:prov:model>` | Assign a model to an agent type |
| `/list-agent-models` | List agent model assignments |
| `/agents` | List active agents and communication stats |
| `/mcp [action]` | Manage MCP servers (enable, disable, tools, invoke) |
| `/chain <prompt>` | Run multi-wave chain orchestration |
| `/remember <k> <v>` | Store a memory entry |
| `/recall [query]` | Recall stored memories |
| `/update_status_line <k> <v>` | Update session status metadata |
| `/help` | Show all commands |
| `/quit` | Exit the session |

**Multi-line input:** End a line with `\` to continue on the next line.

---

## Features

### Multi-Provider Routing

Seamlessly switch between providers — your conversation context is preserved:

```bash
# Use Ollama (default, local)
qarin-cli --provider ollama

# Use Claude
qarin-cli --provider claude

# Use Gemini
qarin-cli --provider gemini

# Use OpenAI Codex
qarin-cli --provider codex

# Use Hugging Face
qarin-cli --provider hf
```

Switch mid-session with `/provider claude` in the REPL.

### Auto-Compact Context Management

Qarin CLI automatically manages your context window. When token usage exceeds the configured threshold (default 85%), older messages are summarized and compacted to free space while preserving recent context.

```bash
# Check context status
>>> /status
Context
  Used:       3,481 / 4,096 tokens
  Usage:      85.0%
  Auto-compact: on (threshold 85%, keep last 4)
  ⚠ Context above threshold — run /compact to free space

# Manually compact
>>> /compact
Context Compaction
  Before: 3,481 / 4,096 tokens (85.0%) — 12 messages
  Auto-compact: on | threshold: 85% | keep last: 4 messages
  After:  1,200 / 4,096 tokens (29.3%) — 5 messages
  Removed 7 messages, freed ~2,281 tokens
```

Configure via environment variables or `/config`:

```bash
export AUTO_COMPACT=true
export COMPACT_THRESHOLD=0.85

# Or in the REPL
>>> /config compact_threshold 0.9
>>> /config auto_compact true
```

### Built-in Tools

Tools are available via `/tool` in the REPL and integrate with the hook system for approval:

```bash
>>> /tools
Available tools:
  file_read                      Read file contents                    [low]
  file_write                     Write content to file                 [medium]
  file_edit                      Edit file with find/replace           [medium]
  grep_search                    Search files for patterns             [low]
  shell_exec                     Execute a shell command               [high]
  web_fetch                      Fetch URL content                     [low]

>>> /tool file_read README.md
>>> /tool grep_search "def main" src/
>>> /tool shell_exec "python -m pytest tests/ -v"
```

**Tool permissions:** Use `--allowed-tools` to restrict which tools are available:

```bash
qarin-cli --allowed-tools file_read,grep_search
```

### Project Memory (QARIN.md)

Like Claude's `CLAUDE.md` and Gemini's `GEMINI.md`, qarin-cli reads `QARIN.md` from your project root to load persistent context:

```bash
# View project memory
>>> /memory

# Add a note
>>> /memory Always use type hints in Python functions
```

### Planning & Orchestration

Generate structured implementation plans and execute them:

```bash
# Create a plan
>>> /team_planning Add user authentication with JWT tokens
✅ Implementation Plan Created
  File: specs/add-user-authentication-with-jwt-tokens.md
  To execute: /build specs/add-user-authentication-with-jwt-tokens.md

# Execute the plan
>>> /build specs/add-user-authentication-with-jwt-tokens.md

# Resume a previous task
>>> /resume
  add-user-auth       [planned   ] team_planning: Add user auth...
>>> /resume add-user-auth
```

### `.qarinignore`

Create a `.qarinignore` file to prevent tools from accessing sensitive files:

```
# .qarinignore
.env
*.key
secrets/
```

### Hook System

14 lifecycle hooks for full customization:

| Hook | When it fires |
|------|---------------|
| `Setup` | On init/maintenance (git status, context injection) |
| `SessionStart` | Session begins |
| `SessionEnd` | Session ends |
| `UserPromptSubmit` | Before processing user input (can deny) |
| `PreToolUse` | Before a tool executes (can deny/ask/allow) |
| `PostToolUse` | After a tool completes |
| `PostToolUseFailure` | When a tool execution fails |
| `PermissionRequest` | On permission dialog (auto-allows read-only ops) |
| `SkillTrigger` | Skill→hook→.py pipeline trigger |
| `PreCompact` | Before context compaction |
| `Stop` | When model finishes responding |
| `SubagentStart` | When a subagent spawns |
| `SubagentStop` | When a subagent finishes |
| `Notification` | On notable events |

Hooks are configured in `.qarin/settings.json` and run as shell commands via the skill→hook→.py pipeline.

### MCP Integration

Connect to MCP (Model Context Protocol) servers for extended capabilities:

```bash
# List MCP servers
>>> /mcp
  ● enabled  github   GitHub MCP server for repos, issues, PRs, actions
  ○ disabled docker   Docker MCP server for container management
  ○ disabled filesystem  Filesystem MCP server for file operations
  ○ disabled memory   Memory MCP server for persistent knowledge graph

# Enable a server
>>> /mcp enable docker

# Discover tools from a server
>>> /mcp tools github

# Invoke a tool
>>> /mcp invoke github list_repos '{"owner": "myorg"}'
```

GitHub MCP auto-enables when `GH_TOKEN` is set. Configure in `.qarin/mcp.json`.

### Chain Orchestration

Run multi-wave subagent pipelines for complex tasks:

```bash
>>> /chain Add JWT authentication with refresh tokens

🔗 Chain Orchestration
  Prompt: Add JWT authentication with refresh tokens

📊 Chain Complete (run: a1b2c3d4)
  Waves: 4 | Duration: 45.2s
  • analysis: 2 agents, 8.1s
  • plan_validate_optimize: 3 agents, 15.3s
  • execution: 2 agents, 12.5s
  • finalize: 3 agents, 9.3s

📝 Final Output
  ...
```

Configure wave pipeline in `.qarin/chain.json`.

### Session Persistence

Save and resume conversations across sessions:

```bash
# Save current session
>>> /save my-project

# Resume later
>>> /load my-project

# Or use the CLI flag
qarin-cli --resume
```

### Agent Model Assignment

Assign specific models to agent types:

```bash
>>> /set-agent-model coding:ollama:codellama
>>> /set-agent-model review:claude:claude-3-sonnet
>>> /list-agent-models
```

---

## Configuration

### Environment Variables

Create a `.env` file or set these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL (use `https://ollama.com` for cloud) |
| `OLLAMA_MODEL` | `llama3.2` | Default model |
| `OLLAMA_API_KEY` | — | API key for [Ollama Cloud](https://ollama.com) (Bearer auth) |
| `PROVIDER` | `ollama` | Default provider |
| `CONTEXT_LENGTH` | `4096` | Max context window (tokens) |
| `AUTO_COMPACT` | `true` | Enable auto-compaction |
| `COMPACT_THRESHOLD` | `0.85` | Context usage trigger (0.0–1.0) |
| `ANTHROPIC_API_KEY` | — | Claude API key |
| `GEMINI_API_KEY` | — | Gemini API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `HF_TOKEN` | — | Hugging Face API key |
| `GH_TOKEN` | — | GitHub token (auto-enables GitHub MCP) |

See [`.env.sample`](.env.sample) for the full template.

### Tested Ollama Cloud Models

The following [Ollama Cloud](https://ollama.com) models have been tested and verified to work with qarin-cli. Set `OLLAMA_HOST=https://ollama.com` and provide your `OLLAMA_API_KEY` to use them:

| Model | Tag |
|-------|-----|
| GLM-4 | `glm-4.7:cloud` |
| GLM-5 | `glm-5:cloud` |
| Qwen3 Coder Next | `qwen3-coder-next:cloud` |
| Qwen3 Next 80B | `qwen3-next:80b-cloud` |
| Qwen3 Coder 480B | `qwen3-coder:480b-cloud` |
| Qwen3 VL 235B | `qwen3-vl:235b-cloud` |
| Qwen3 VL 235B Instruct | `qwen3-vl:235b-instruct-cloud` |

---

## Documentation

| Document | Description |
|----------|-------------|
| [Getting Started](docs/getting_started.md) | Installation and first steps |
| [CLI Reference](docs/cli_reference.md) | All commands and flags |
| [API Reference](docs/api_reference.md) | Ollama and provider APIs |
| [Configuration](docs/configuration.md) | Environment variables and settings |
| [Multi-Provider](docs/multi_provider.md) | Using Claude, Gemini, Codex |
| [Agent Models](docs/agent_model_assignment.md) | Agent-specific model assignments |
| [Hooks System](docs/hooks.md) | Lifecycle hooks and customization |
| [RDMA Support](docs/rdma.md) | High-performance networking |
| [Development](docs/development.md) | Contributing and building |

---

## Development

```bash
# Clone
git clone https://github.com/muah1987/qarin-cli.git
cd qarin-cli

# Install dependencies
uv sync --dev

# Run tests
uv run pytest tests/ -v

# Run tests with coverage
uv run pytest tests/ --cov=./ --cov-report=term-missing

# Lint
uv run ruff check .

# Format
uv run ruff format .
```

---

## Support

- **GitHub Issues:** [Report bugs or request features](https://github.com/muah1987/qarin-cli/issues)
- **Ollama:** [Official Ollama website](https://ollama.ai)

## Migration Notice

The CLI frontend is planned to migrate from Python to
[Go](https://go.dev/) using the
[BubbleTea](https://github.com/charmbracelet/bubbletea) TUI framework.
The current Python version remains fully supported until the migration is
complete.  See the [ROADMAP](ROADMAP.md) for details.

## License

MIT License — see [LICENSE](LICENSE) for details.
