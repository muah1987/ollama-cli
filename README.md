# Ollama CLI

An open-source AI coding assistant that runs in your terminal, powered by [Ollama](https://ollama.ai) with multi-provider support for Claude, Gemini, and OpenAI Codex.

<p align="center">
  <strong>Local-first</strong> · <strong>Multi-provider</strong> · <strong>Extensible hooks</strong> · <strong>Built-in tools</strong>
</p>

---

## Quick Start

### Install

```bash
curl -fsSL https://raw.githubusercontent.com/muah1987/ollama-cli/main/install.sh | bash
```

This installs `ollama-cli` to `~/.local/bin/`, sets up dependencies, and installs Ollama if needed.

### Start chatting

```bash
# Start interactive session (default)
ollama-cli

# Or with a direct prompt
ollama-cli "Explain this codebase to me"

# Non-interactive mode
ollama-cli -p "Write a Python function that reverses a string"

# Resume last session
ollama-cli --resume
```

### Pipe input

```bash
echo "Fix the bug in this code" | ollama-cli
cat error.log | ollama-cli -p "What went wrong?"
git diff | ollama-cli -p "Review these changes"
```

---

## Usage

```
Usage: ollama-cli [options] [command] [prompt]

Options:
  -v, --version                   Show version
  -p, --print                     Print response and exit (non-interactive)
  -r, --resume                    Resume the most recent conversation
  --model MODEL                   Override model (e.g. llama3.2, codellama)
  --provider {ollama,claude,gemini,codex}
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
| `/provider <name>` | Switch provider (ollama, claude, gemini, codex) |
| `/status` | Show session status, tokens, context, auto-compact state |
| `/compact` | Force context compaction to free space |
| `/clear` | Clear conversation history |
| `/save [name]` | Save session to file |
| `/load <name>` | Load session from file |
| `/history` | Show conversation history |
| `/memory [note]` | View or add to project memory (OLLAMA.md) |
| `/tools` | List available built-in tools |
| `/tool <name> ...` | Invoke a tool (file_read, shell_exec, grep_search, ...) |
| `/diff` | Show git diff of working directory |
| `/config [k] [v]` | View or set configuration |
| `/bug [desc]` | File a bug report with session context |
| `/team_planning <desc>` | Generate an implementation plan → `specs/` |
| `/build <plan>` | Execute a saved plan file |
| `/resume [id]` | List or resume previous tasks |
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
ollama-cli --provider ollama

# Use Claude
ollama-cli --provider claude

# Use Gemini
ollama-cli --provider gemini

# Use OpenAI Codex
ollama-cli --provider codex
```

Switch mid-session with `/provider claude` in the REPL.

### Auto-Compact Context Management

Ollama CLI automatically manages your context window. When token usage exceeds the configured threshold (default 85%), older messages are summarized and compacted to free space while preserving recent context.

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
  web_fetch                      Fetch URL content                     [medium]

>>> /tool file_read README.md
>>> /tool grep_search "def main" src/
>>> /tool shell_exec "python -m pytest tests/ -v"
```

**Tool permissions:** Use `--allowed-tools` to restrict which tools are available:

```bash
ollama-cli --allowed-tools file_read,grep_search
```

### Project Memory (OLLAMA.md)

Like Claude's `CLAUDE.md` and Gemini's `GEMINI.md`, ollama-cli reads `OLLAMA.md` from your project root to load persistent context:

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

### `.ollamaignore`

Create a `.ollamaignore` file to prevent tools from accessing sensitive files:

```
# .ollamaignore
.env
*.key
secrets/
```

### Hook System

7 lifecycle hooks for customization:

| Hook | When it fires |
|------|---------------|
| `SessionStart` | Session begins |
| `SessionEnd` | Session ends |
| `PreToolUse` | Before a tool executes (can deny/ask/allow) |
| `PostToolUse` | After a tool completes |
| `PreCompact` | Before context compaction |
| `Stop` | After plan generation (for validation) |
| `Notification` | On notable events |

Hooks are configured in `.ollama/settings.json` and run as shell commands.

### Session Persistence

Save and resume conversations across sessions:

```bash
# Save current session
>>> /save my-project

# Resume later
>>> /load my-project

# Or use the CLI flag
ollama-cli --resume
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
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Default model |
| `PROVIDER` | `ollama` | Default provider |
| `CONTEXT_LENGTH` | `4096` | Max context window (tokens) |
| `AUTO_COMPACT` | `true` | Enable auto-compaction |
| `COMPACT_THRESHOLD` | `0.85` | Context usage trigger (0.0–1.0) |
| `ANTHROPIC_API_KEY` | — | Claude API key |
| `GEMINI_API_KEY` | — | Gemini API key |
| `OPENAI_API_KEY` | — | OpenAI API key |

See [`.env.sample`](.env.sample) for the full template.

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
git clone https://github.com/muah1987/ollama-cli.git
cd ollama-cli

# Install dependencies
uv sync --dev

# Run tests
uv run pytest tests/ -v

# Lint
uv run ruff check .

# Format
uv run ruff format .
```

---

## Support

- **GitHub Issues:** [Report bugs or request features](https://github.com/muah1987/ollama-cli/issues)
- **Ollama:** [Official Ollama website](https://ollama.ai)

## License

MIT License — see [LICENSE](LICENSE) for details.
