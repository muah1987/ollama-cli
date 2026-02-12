# Contributing to Ollama CLI

Thank you for your interest in contributing to Ollama CLI!

---

## How to Contribute

### Reporting Issues

If you find a bug or have a feature request:

1. Check existing [issues](https://github.com/muah1987/ollama-cli/issues) first
2. Create a new issue with a clear title and description
3. Include steps to reproduce for bugs

### Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests and linting
5. Commit with a clear message
6. Push to your branch: `git push origin feature/my-feature`
7. Open a Pull Request

---

## Code Style

### Type Hints

All functions should include type hints:

```python
def example_function(param: str) -> int:
    """Return the length of the parameter."""
    return len(param)
```

### Linting

We use [ruff](https://github.com/astral-sh/ruff) for linting:

```bash
# Check all files
ruff check .

# Auto-fix issues
ruff check --fix .
```

### Format

All code is formatted with ruff:

```bash
ruff format .
```

### Line Length

Maximum line length is 120 characters.

---

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ollama_cmd --cov=api --cov=model --cov=server --cov=runner

# Run specific test file
pytest tests/test_api.py
```

---

## Development Setup

```bash
# Clone the repository
git clone https://github.com/muah1987/ollama-cli.git
cd ollama-cli

# Install development dependencies
uv sync --dev

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Run tests
pytest

# Run linting
ruff check .
```

---

## Adding Commands

Follow the existing command structure in `ollama_cmd/`:

1. Create a new command file in `ollama_cmd/`
2. Import necessary modules from `api/`, `model/`, etc.
3. Add a function following the pattern:
```python
def cmd_mycommand(args: argparse.Namespace) -> None:
    """Description of the command."""
    pass
```
4. Add the command to `ollama_cmd/root.py` in the `build_parser()` function and `COMMAND_MAP`

---

## Project Structure

```
ollama-cli/
├── ollama_cmd/       # CLI entry points per command
├── api/              # API client, provider router, MCP client, config
├── model/            # Model management and sessions
├── server/           # Server utilities (hook runner)
├── runner/           # Context manager, token counter, chain controller
├── skills/           # Skill modules (EXO, MLX, RDMA) with hook trigger pipeline
├── docs/             # Documentation
├── tests/            # Test files
├── .ollama/          # Hooks, settings, MCP config, chain config
│   ├── hooks/        # 13 lifecycle hook scripts
│   ├── mcp.json      # MCP server configuration
│   ├── chain.json    # Chain orchestration config
│   └── settings.json # Hook config + agent_models
└── pyproject.toml    # Project configuration
```

---

## Commit Messages

Follow conventional commits:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Test changes
- `chore:` - Maintenance tasks

Example:
```
feat: add streaming support for run command
```

---

## Migration Notice

The CLI frontend is planned to migrate to
[BubbleTea](https://github.com/charmbracelet/bubbletea) (Go).  Contributions
to the current Python codebase are still welcome — all features and fixes will
be carried forward during the migration.  See the [ROADMAP](ROADMAP.md) for
the full plan.