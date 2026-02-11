# Copilot Instructions — Ollama CLI

## Project Overview

Ollama CLI is a full-featured AI coding assistant powered by Ollama with multi-provider support (Ollama, Claude, Gemini, Codex/OpenAI). It is a Python 3.11+ CLI tool built with `httpx`, `rich`, and `python-dotenv`, packaged via `hatchling`, and managed with `uv`.

## Repository Structure

```
ollama-cli/
├── cmd/           # CLI commands (root.py is the entry point)
├── api/           # API client, provider router, config
├── model/         # Model management and sessions
├── server/        # Server utilities (hook runner)
├── runner/        # Context manager and token counter
├── src/           # Alternative/wrapper modules
├── tests/         # Pytest test suite
├── docs/          # Documentation (development.md, api.md)
├── .ollama/       # Hooks, status lines, settings
│   ├── hooks/     # Pre/post-execution hooks
│   └── status_lines/  # Status display modules
├── production/    # Production build variant
├── pyproject.toml # Project config, dependencies, ruff, pytest, semantic-release
├── uv.lock        # Locked dependency versions
├── .env.sample    # Environment variable template
└── run_tests.py   # Standalone test runner
```

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
- **Test mode**: pytest with `--import-mode=importlib` (configured in pyproject.toml) to avoid `cmd` module collision with the stdlib.
- **Commit messages**: Follow [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`.
- **New CLI commands**: Add a file in `cmd/`, implement `cmd_<name>(args)`, register in `cmd/root.py` via `build_parser()` and `COMMAND_MAP`.

## Dependency Policy

- Use `uv` as the package manager. Add dependencies with `uv add <package>` (or `uv add --dev <package>` for dev-only).
- The `uv.lock` file must be committed for reproducibility.
- Only add new dependencies when strictly necessary. Prefer the standard library or existing deps (`httpx`, `rich`, `python-dotenv`).
- Build backend is `hatchling`; wheel packages are `cmd`, `api`, `model`, `server`, `runner`.

## Security Guardrails

- **No secrets in code.** API keys must come from environment variables (see `.env.sample`).
- **No hardcoded credentials.** Use `python-dotenv` and `os.environ`.
- **HTTPS only** for cloud provider connections.
- **Validate user input** before processing.
- Refer to `SECURITY.md` for the full security policy.

## PR Expectations

- Tests must pass (`uv run pytest tests/ -v`).
- Linting must pass (`uv run ruff check .`).
- Update documentation when adding or changing user-facing behavior.
- Keep diffs minimal and focused on the stated change.
- Follow conventional commit message format.
