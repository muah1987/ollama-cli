"""Input area widget -- bordered input box with › prompt indicator.

Part of the MIDDLE zone in the 3-zone layout.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static


class InputArea(Widget):
    """Chat input area with bordered box, › prompt, and Enter-to-send.

    Emits InputArea.Submitted when the user presses Enter.
    """

    DEFAULT_CSS = """
    InputArea {
        height: auto;
        max-height: 8;
        padding: 0 1;
        background: #0d1117;
    }

    InputArea #input-box {
        border: round #30363d;
        background: #161b22;
        padding: 0 1;
        height: auto;
    }

    InputArea #input-hint {
        color: #484f58;
        padding: 0 0;
        height: 1;
    }

    InputArea Input {
        width: 1fr;
        border: none;
        background: #161b22;
        color: #e6edf3;
    }

    InputArea Input:focus {
        border: none;
    }

    InputArea .prompt-indicator {
        color: #484f58;
        height: 1;
        padding: 0 0;
    }
    """

    class Submitted(Message):
        """Posted when the user submits input."""

        def __init__(self, value: str) -> None:
            self.value = value
            super().__init__()

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._history: list[str] = []
        self._history_index: int = -1

    def compose(self) -> ComposeResult:
        with Vertical(id="input-box"):
            yield Static("› Type your message or @path/to/file", id="input-hint")
            yield Input(placeholder="> ", id="chat-input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter key in the input field."""
        value = event.value.strip()
        if value:
            self._history.append(value)
            self._history_index = -1
            self.post_message(self.Submitted(value))
        event.input.value = ""

    def focus_input(self) -> None:
        """Focus the text input."""
        try:
            self.query_one("#chat-input", Input).focus()
        except Exception:
            pass
