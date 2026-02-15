"""Help screen -- command reference and keyboard shortcuts."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Footer, Header, Markdown

_HELP_TEXT = """\
# qarin Help

## Chat
Type a message and press **Enter** to send it to the AI.

Use `@agent_type` prefix to route to a specific agent:
- `@code` - Code generation
- `@review` - Code review
- `@test` - Test writing
- `@debug` - Debugging
- `@plan` - Planning
- `@docs` - Documentation
- `@orchestrator` - Multi-step orchestration

## Keyboard Shortcuts
| Key | Action |
|-----|--------|
| Ctrl+P | Command palette |
| Ctrl+B | Toggle sidebar |
| Ctrl+S | Save session |
| Ctrl+L | Clear chat |
| Ctrl+, | Settings |
| F1 | This help screen |
| Escape | Close / Cancel |
| Ctrl+Q | Quit |

## Slash Commands

### Session
- `/model` - List/switch models
- `/provider` - Switch provider
- `/status` - Show session status
- `/save` - Save session
- `/load` - Load session
- `/clear` - Clear history
- `/history` - Show history
- `/compact` - Force context compaction

### Agents & Tools
- `/tools` - List available tools
- `/tool <name>` - Invoke a tool
- `/agents` - List active agents
- `/intent` - Intent classifier control
- `/chain` - Multi-wave orchestration
- `/build` - Execute a plan

### Memory
- `/memory` - View/add project memory
- `/remember` - Store a memory entry
- `/recall` - Recall memories

### Other
- `/config` - View/set configuration
- `/help` - This help screen
- `/quit` - Exit
"""


class HelpScreen(Screen):
    """Full help screen with command reference."""

    BINDINGS = [("escape", "pop_screen", "Back"), ("f1", "pop_screen", "Back")]

    DEFAULT_CSS = """
    HelpScreen {
        background: #0d1117;
    }

    #help-content {
        padding: 2 4;
        height: 1fr;
    }

    #help-content Markdown {
        margin: 0 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollableContainer(id="help-content"):
            yield Markdown(_HELP_TEXT)
        yield Footer()

    def action_pop_screen(self) -> None:
        self.app.pop_screen()
