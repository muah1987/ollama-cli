# Qarin CLI

An AI coding assistant for the terminal with multi-provider LLM support and Arabic-themed progress indicators.

Qarin connects to **Anthropic Claude**, **OpenAI GPT**, or **local Ollama** models and provides an interactive agentic coding experience with tool execution, session persistence, and culturally inspired themes.

## Features

- **Multi-provider support** -- Anthropic, OpenAI, and Ollama out of the box
- **Agentic tool-call loop** -- file read/write/edit, shell execution, grep search, web fetch
- **Intent classification** -- automatically detects Code, Review, Test, Debug, Plan, and more
- **Session persistence** -- save and resume conversations with full context
- **Sub-agent orchestration** -- 4-wave delegation (Diagnostic, Analysis, Solution, Validation)
- **Real-time token tracking** with cost estimation
- **Arabic-themed progress indicators** -- five built-in themes with bilingual messages
- **Hook system** -- lifecycle events for extensibility
- **Project context** -- reads `QARIN.md` at session start for project-specific guidelines

## Installation

```bash
npm install -g @muah1987/qarin-cli
```

### From source

```bash
git clone https://github.com/muah1987/qarin-cli.git
cd qarin-cli
npm install
```

## Usage

```bash
# Interactive mode
qarin

# Run a task directly
qarin "fix the authentication bug in auth.ts"

# Choose a provider and model
qarin -p openai -m gpt-4 "review this code"
qarin -p ollama -m llama2 "refactor this function"

# Pick a theme
qarin --theme caravan "write unit tests"

# Resume the last session
qarin --resume

# Non-interactive output
qarin --print "generate API docs"

# Custom system prompt
qarin --system-prompt "You are a Python expert" "optimize this code"

# JSON output
qarin --output-format json "analyze this"
```

### CLI Options

| Option | Description | Default |
|---|---|---|
| `-m, --model <model>` | AI model to use | `claude-sonnet-4-20250514` |
| `-p, --provider <provider>` | LLM provider: `anthropic`, `openai`, `ollama` | `anthropic` |
| `-t, --theme <theme>` | Progress theme | `shisha` |
| `--print` | Non-interactive output mode | -- |
| `--resume` | Resume the latest session | -- |
| `--system-prompt <prompt>` | Custom system prompt | -- |
| `--output-format <format>` | Output format: `text`, `json`, `markdown` | `text` |

### Interactive Commands

| Command | Description |
|---|---|
| `/quit` or `/exit` | End session and exit |
| `/theme` | Cycle through available themes |
| `/status` | Show session status |
| `/save` | Persist session to disk |

## Themes

Each theme maps operation phases to culturally-themed metaphors with emoji, English, and Arabic messages.

| Theme | Metaphor | Phases |
|---|---|---|
| **shisha** (default) | Hookah cafe session | preparing the hookah through to thick clouds |
| **caravan** | Desert journey | dawn departure through to starlit camp |
| **qahwa** | Arabic coffee ceremony | selecting beans through to the perfect cup |
| **scholarly** | Islamic manuscript study | opening the text through to wisdom gained |
| **base** | Generic fallback | standard progress phases |

## Built-in Tools

The agent can autonomously execute:

| Tool | Description |
|---|---|
| `file_read` | Read file contents |
| `file_write` | Write files (creates directories as needed) |
| `file_edit` | Edit specific line ranges |
| `shell_exec` | Execute shell commands |
| `grep_search` | Regex search across files |
| `web_fetch` | Fetch URL content |

## Configuration

### Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `QARIN_PROJECT_DIR` | Project root directory (defaults to cwd) |

### Project Context

Drop a `QARIN.md` file in your project root. Qarin loads it automatically at session start to understand your project conventions, architecture, and guidelines.

### Hooks

Configure lifecycle hooks in `.qarin/settings.json`. Supported events:

`SessionStart`, `SessionEnd`, `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PreCompact`, `UserPromptSubmit`, `SkillTrigger`, `SubagentStart`, `SubagentStop`, `Notification`, `PermissionRequest`, `Stop`

### Data Storage

| Path | Purpose |
|---|---|
| `.qarin/sessions/` | Persisted session files |
| `.qarin/memory/` | Long-term memory/context |
| `.qarin/settings.json` | Hook configuration |

## Development

```bash
npm run dev            # Run with --watch
npm run build          # Compile TypeScript
npm run build:binary   # Create standalone binary (requires Bun)
npm run lint           # Type check
npm run test           # Run tests
```

## Requirements

- Node.js >= 18.0.0

## License

[MIT](LICENSE)

## Author

Mohammed Uthmaan Al Hashimi
