"""Chat message widget -- Claude Code-style flat message rendering."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Markdown, Static


class ChatMessage(Widget):
    """A single chat message in Claude Code style.

    Parameters
    ----------
    content: The message text content.
    role: Either "user" or "assistant".
    agent_type: Optional agent type (e.g., "code", "debug").
    timestamp: Optional timestamp string.
    """

    DEFAULT_CSS = """
    ChatMessage {
        width: 100%;
        padding: 0 1;
        margin: 0 0;
    }

    ChatMessage .user-message {
        background: transparent;
        color: #e6edf3;
        padding: 0 1;
        margin: 0 0;
    }

    ChatMessage .assistant-message {
        background: transparent;
        color: #e6edf3;
        padding: 0 1;
        margin: 0 0;
        border-left: tall #7c8aff;
    }

    ChatMessage .message-header {
        color: #484f58;
        text-style: dim;
        padding: 0 0 0 0;
    }

    ChatMessage .agent-badge {
        color: #7c8aff;
        text-style: bold;
    }
    """

    content: reactive[str] = reactive("")
    role: reactive[str] = reactive("user")

    def __init__(
        self,
        content: str,
        role: str = "user",
        agent_type: str | None = None,
        timestamp: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.content = content
        self.role = role
        self.agent_type = agent_type
        self.timestamp = timestamp

    def compose(self) -> ComposeResult:
        header_parts = []
        if self.role == "user":
            header_parts.append("❯")
        else:
            header_parts.append("⏎")
            if self.agent_type:
                header_parts.append(f"[{self.agent_type}]")
        if self.timestamp:
            header_parts.append(f"  {self.timestamp}")

        header_text = " ".join(header_parts)
        css_class = "user-message" if self.role == "user" else "assistant-message"

        with Vertical(classes=css_class):
            yield Label(header_text, classes="message-header")
            if self.role == "assistant":
                yield Markdown(self.content)
            else:
                yield Static(self.content)

    def update_content(self, new_content: str) -> None:
        """Update the message content (for streaming responses)."""
        self.content = new_content
        # Find and update the Markdown/Static widget
        try:
            if self.role == "assistant":
                md = self.query_one(Markdown)
                md.update(new_content)
            else:
                st = self.query_one(Static)
                st.update(new_content)
        except Exception:
            pass
