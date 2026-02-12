# Copilot Instructions — Ollama CLI

## Project Overview

Ollama CLI is a full-featured AI coding assistant powered by Ollama with multi-provider support (Ollama, Claude, Gemini, Codex/OpenAI, Hugging Face). It is a Python 3.11+ CLI tool built with `httpx`, `rich`, and `python-dotenv`, packaged via `hatchling`, and managed with `uv`.

## Repository Structure

```
ollama-cli/
├── ollama_cmd/    # CLI commands (root.py is the entry point)
├── api/           # API client, provider router, RDMA client, MCP client, config
├── model/         # Model management and sessions
├── server/        # Server utilities (hook runner)
├── runner/        # Context manager, token counter, RDMA manager
├── skills/        # Skill modules (EXO, MLX, RDMA) with hook trigger pipeline
├── specs/         # Integration specifications
├── tests/         # Pytest test suite
├── docs/          # Documentation (API, CLI, hooks, MCP, RDMA, providers, etc.)
├── .ollama/       # Hooks, status lines, settings, MCP config
│   ├── hooks/     # 13 lifecycle hook scripts (skill→hook→.py pipeline)
│   ├── status_lines/  # Status display modules
│   ├── settings.json  # Hook config + agent_models
│   └── mcp.json       # MCP server configuration
├── pyproject.toml # Project config, dependencies, ruff, pytest, semantic-release
├── uv.lock        # Locked dependency versions
├── .env.sample    # Environment variable template
└── install.sh     # One-line installer script
```

## Hook Lifecycle (13 Events)

The hook system follows the skill→hook→.py pipeline:

1. **Setup** — On init/maintenance (loads git status, injects context)
2. **SessionStart** — When a session begins
3. **SessionEnd** — When a session ends
4. **UserPromptSubmit** — Before processing user input (can deny)
5. **PreToolUse** — Before tool execution (can deny/ask/allow)
6. **PostToolUse** — After tool completion
7. **PostToolUseFailure** — When a tool execution fails
8. **PermissionRequest** — On permission dialog (auto-allow read-only ops)
9. **SkillTrigger** — When a skill invokes a hook (skill→hook→.py)
10. **PreCompact** — Before context compaction
11. **Stop** — When the model finishes responding
12. **SubagentStart** — When a subagent spawns
13. **SubagentStop** — When a subagent finishes
14. **Notification** — On notable events

## Multi-Model Agent Configuration

Up to 10+ agent types can be assigned specific providers and models:

```json
// .ollama/settings.json
{
  "agent_models": {
    "code": {"provider": "ollama", "model": "codestral:latest"},
    "review": {"provider": "claude", "model": "claude-sonnet"},
    "test": {"provider": "gemini", "model": "gemini-flash"},
    "plan": {"provider": "ollama", "model": "llama3.2"},
    "docs": {"provider": "hf", "model": "mistral-7b"}
  }
}
```

Or via environment variables: `OLLAMA_CLI_AGENT_CODE_PROVIDER=ollama`, `OLLAMA_CLI_AGENT_CODE_MODEL=codestral:latest`.

## MCP Integration

MCP (Model Context Protocol) servers are configured in `.ollama/mcp.json`:
- **GitHub MCP** — Auto-enabled when `GH_TOKEN` is set
- **Docker MCP** — Container management
- **Filesystem MCP** — File operations
- **Memory MCP** — Persistent knowledge graph

Use `/mcp` in the REPL to manage servers.

## How to Run Locally

```bash
# Install dependencies (including dev tools)
uv sync --dev

# Run the CLI
uv run ollama --help

# Activate the virtual environment (optional)
source .venv/bin/activate
```

## How to Validate Changes

```bash
# Run tests
uv run pytest tests/ -v

# Run linter
uv run ruff check .

# Check import sorting
uv run ruff check --select I .

# Auto-fix lint issues
uv run ruff check --fix .

# Format code
uv run ruff format .
```

A change is "green" when all three pass: `pytest` exits 0, `ruff check .` exits 0, and `ruff check --select I .` exits 0.

## Coding Standards

- **Python version**: 3.11+ required.
- **Line length**: 120 characters max (enforced by ruff).
- **Type hints**: All functions must include type hints.
- **Linter/formatter**: ruff (`ruff check .` and `ruff format .`).
- **Test mode**: pytest with `--import-mode=importlib` (configured in pyproject.toml).
- **Commit messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`.
- **New CLI commands**: Add a file in `ollama_cmd/`, implement `cmd_<name>(args)`, register in `ollama_cmd/root.py` via `build_parser()` and `COMMAND_MAP`.

## Dependency Policy

- Use `uv` as the package manager. Add dependencies with `uv add <package>` (or `uv add --dev <package>` for dev-only).
- The `uv.lock` file must be committed for reproducibility.
- Only add new dependencies when strictly necessary. Prefer the standard library or existing deps (`httpx`, `rich`, `python-dotenv`).
- Build backend is `hatchling`; wheel packages are `ollama_cmd`, `api`, `model`, `server`, `runner`.

## Security Guardrails

- **No secrets in code.** API keys must come from environment variables (see `.env.sample`).
- **No hardcoded credentials.** Use `python-dotenv` and `os.environ`.
- **HTTPS only** for cloud provider connections.
- **Validate user input** before processing (UserPromptSubmit hook).
- **PermissionRequest hook** auto-allows read-only ops, asks for risky operations.
- Refer to `SECURITY.md` for the full security policy.

## PR Expectations

- Tests must pass (`uv run pytest tests/ -v`).
- Linting must pass (`uv run ruff check .`).
- Update documentation when adding or changing user-facing behavior.
- Keep diffs minimal and focused on the stated change.
- Follow conventional commit message format.
