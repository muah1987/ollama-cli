# Development

## Project Structure

Qarin CLI follows the directory structure of the [official Ollama project](https://github.com/ollama/ollama):

```
qarin-cli/
├── qarin_cmd/       # CLI entry points per command
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
│   ├── install.py    # Install Ollama automatically
│   ├── onboarding.py # First-time onboarding flow
│   ├── accelerate.py # Hardware acceleration management
│   ├── rdma.py       # RDMA device management
│   └── ...
├── api/              # API client and utilities
│   ├── ollama_client.py     # Ollama API client
│   ├── provider_router.py   # Multi-provider routing
│   ├── config.py            # Configuration management
│   ├── mcp_client.py        # MCP (Model Context Protocol) client
│   └── rdma_client.py       # RDMA networking client
├── model/            # Model management
│   └── session.py     # Session state management
├── server/           # Server utilities
│   └── hook_runner.py  # Hook execution engine
├── runner/           # Model execution
│   ├── context_manager.py   # Auto-compact context
│   ├── token_counter.py     # Token tracking
│   ├── intent_classifier.py # Intent classification for agent routing
│   ├── chain_controller.py  # Chain orchestration controller
│   ├── agent_comm.py        # Agent communication layer
│   ├── memory_layer.py      # Memory persistence layer
│   └── rdma_manager.py      # RDMA connection manager
├── tui/              # Textual TUI application
│   ├── app.py               # Main TUI app
│   ├── command_processor.py # Slash-command dispatch and registry
│   ├── screens/             # TUI screens (chat, help, settings)
│   ├── widgets/             # TUI widgets (chat_message, input_area, status_panel, etc.)
│   └── styles/              # TUI stylesheets (app.tcss, dark.tcss, light.tcss)
├── skills/           # Skill modules (EXO, MLX, RDMA) with hook trigger pipeline
│   ├── tools.py             # Built-in tool definitions
│   ├── exo/                 # EXO distributed execution skill
│   ├── mlx/                 # Apple Silicon MLX acceleration skill
│   └── rdma/                # RDMA networking skill
├── docs/             # Documentation
├── tests/            # Test files
├── .qarin/          # Hooks, settings, MCP config, chain config
│   ├── hooks/        # 14 lifecycle hook scripts
│   ├── status_lines/ # Status line scripts + utilities
│   ├── settings.json # Hook config + agent_models + TUI settings
│   ├── mcp.json      # MCP server configuration
│   ├── chain.json    # Chain orchestration configuration
│   └── memory.json   # Persistent memory store
└── pyproject.toml    # Project configuration
```

---

## How to Add Commands

### Command Pattern

Each command in `qarin_cmd/` follows this pattern:

1. Import necessary modules
2. Define a function with signature `(args: argparse.Namespace) -> None`
3. Add the command to `root.py` in both `build_parser()` and `COMMAND_MAP`

### Example

Create `qarin_cmd/mycommand.py`:

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

Add to `qarin_cmd/root.py`:

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

Qarin CLI provides 14 lifecycle hooks that execute at specific points:

### Available Hooks

| # | Hook | When It Fires |
|---|------|---------------|
| 1 | `Setup` | On init or periodic maintenance |
| 2 | `SessionStart` | When session begins |
| 3 | `SessionEnd` | When session ends |
| 4 | `UserPromptSubmit` | Before processing user input |
| 5 | `PreToolUse` | Before tool execution |
| 6 | `PostToolUse` | After tool execution |
| 7 | `PostToolUseFailure` | When a tool execution fails |
| 8 | `PermissionRequest` | On permission dialog |
| 9 | `SkillTrigger` | When a skill invokes a hook |
| 10 | `PreCompact` | Before context compaction |
| 11 | `Stop` | When assistant stops |
| 12 | `SubagentStart` | When a subagent spawns |
| 13 | `SubagentStop` | When a subagent finishes |
| 14 | `Notification` | On notable events |

### Configuration

Hooks are configured in `.qarin/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python .qarin/hooks/session_start.py"
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

Status lines are in `.qarin/status_lines/` and can be customized.

---

## Got in Touch

- GitHub: [https://github.com/muah1987/qarin-cli](https://github.com/muah1987/qarin-cli)
- Issues: [https://github.com/muah1987/qarin-cli/issues](https://github.com/muah1987/qarin-cli/issues)

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