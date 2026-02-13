"""Input area widget -- multi-line input with command awareness."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Label


class InputArea(Widget):
    """Chat input area with Enter-to-send and command completion.

    Emits InputArea.Submitted when the user presses Enter.
    """

    DEFAULT_CSS = """
    InputArea {
        dock: bottom;
        height: auto;
        max-height: 6;
        padding: 0 1;
        background: #1a1b26;
    }

    InputArea Horizontal {
        height: auto;
    }

    InputArea Input {
        width: 1fr;
        border: round #565f89;
        background: #24283b;
        color: #c0caf5;
    }

    InputArea Input:focus {
        border: round #7aa2f7;
    }

    InputArea .prompt-indicator {
        width: 4;
        height: 3;
        content-align: center middle;
        color: #7aa2f7;
        text-style: bold;
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
        with Horizontal():
            yield Label(">>>", classes="prompt-indicator")
            yield Input(placeholder="Type a message or /command...", id="chat-input")

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
