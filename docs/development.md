# Development

## Project Structure

Ollama CLI follows the directory structure of the [official Ollama project](https://github.com/ollama/ollama):

```
ollama-cli/
├── ollama_cmd/       # CLI entry points per command
│   ├── root.py       # Main entry point and argument parser
│   ├── run.py        # Run model interactively
│   ├── create.py     # Create from Modelfile
│   ├── pull.py       # Pull from registry
│   ├── show.py       # Show model details
│   ├── list.py       # List available models
│   ├── ps.py         # List running models
│   ├── stop.py       # Stop running model
│   ├── rm.py         # Delete model
│   ├── cp.py         # Copy model
│   ├── serve.py      # Check server status
│   ├── interactive.py# Interactive REPL mode
│   └── ...
├── api/              # API client and utilities
│   ├── ollama_client.py  # Ollama API client
│   ├── provider_router.py  # Multi-provider routing
│   └── config.py      # Configuration management
├── model/            # Model management
│   └── session.py     # Session state management
├── server/           # Server utilities
│   └── hook_runner.py  # Hook execution engine
├── runner/           # Model execution
│   ├── context_manager.py  # Auto-compact context
│   └── token_counter.py   # Token tracking
├── docs/             # Documentation
├── tests/            # Test files
└── pyproject.toml    # Project configuration
```

---

## How to Add Commands

### Command Pattern

Each command in `ollama_cmd/` follows this pattern:

1. Import necessary modules
2. Define a function with signature `(args: argparse.Namespace) -> None`
3. Add the command to `root.py` in both `build_parser()` and `COMMAND_MAP`

### Example

Create `ollama_cmd/mycommand.py`:

```python
#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys

from rich.console import Console

console = Console()

def cmd_mycommand(args: argparse.Namespace) -> None:
    """Description of what this command does."""
    console.print("Running my command!")
```

Add to `ollama_cmd/root.py`:

```python
def build_parser() -> argparse.ArgumentParser:
    # ... existing code ...
    subparsers.add_parser("mycommand", help="My command description")
    # ... existing code ...

COMMAND_MAP = {
    # ... existing commands ...
    "mycommand": cmd_mycommand,
}
```

---

## Hook System

Ollama CLI provides hooks that execute at specific points in the lifecycle:

### Available Hooks

| Hook | When It Fires |
|------|---------------|
| `PreToolUse` | Before tool execution |
| `PostToolUse` | After tool execution |
| `SessionStart` | When session begins |
| `SessionEnd` | When session ends |
| `PreCompact` | Before context compaction |
| `Stop` | When assistant stops |
| `Notification` | On notable events |

### Configuration

Hooks are configured in `.ollama/settings.json`:

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

### Hook Interface

Each hook command receives JSON on stdin:

```json
{
  "hook": "SessionStart",
  "timestamp": "2024-01-01T00:00:00",
  "data": {
    "model": "llama3.2",
    "provider": "ollama"
  }
}
```

---

## Status Lines

Status line scripts provide real-time visibility:

### Built-in Status Lines

- `token_counter.py` - Token usage and cost estimate
- `provider_health.py` - Provider connectivity status
- `full_dashboard.py` - Combined dashboard

### Location

Status lines are in `.ollama/status_lines/` and can be customized.

---

## Got in Touch

- GitHub: [https://github.com/muah1987/ollama-cli](https://github.com/muah1987/ollama-cli)
- Issues: [https://github.com/muah1987/ollama-cli/issues](https://github.com/muah1987/ollama-cli/issues)

---

## Contribution Workflow

See [CONTRIBUTING.md](../CONTRIBUTING.md) for full contribution guidelines.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Run linting: `ruff check .`
6. Commit with conventional commit message
7. Open a Pull Request