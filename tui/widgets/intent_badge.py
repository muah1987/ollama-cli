"""Intent badge widget -- colorized label for auto-detected intent."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label

# Agent color map
_AGENT_BADGE_COLORS: dict[str, str] = {
    "code": "#a78bfa",
    "review": "#79c0ff",
    "test": "#e3b341",
    "plan": "#7c8aff",
    "docs": "#7ee787",
    "debug": "#ff7b72",
    "orchestrator": "#ffa657",
}


class IntentBadge(Widget):
    """Small badge showing auto-detected agent type and confidence."""

    DEFAULT_CSS = """
    IntentBadge {
        height: 1;
        width: auto;
        padding: 0 1;
        margin: 0 0 0 2;
    }

    IntentBadge Label {
        text-style: italic;
        color: #484f58;
    }
    """

    agent_type: reactive[str] = reactive("")
    confidence: reactive[float] = reactive(0.0)

    def compose(self) -> ComposeResult:
        yield Label("", id="badge-label")

    def watch_agent_type(self, value: str) -> None:
        self._update_badge()

    def watch_confidence(self, value: float) -> None:
        self._update_badge()

    def _update_badge(self) -> None:
        try:
            label = self.query_one("#badge-label", Label)
            if self.agent_type:
                color = _AGENT_BADGE_COLORS.get(self.agent_type, "#565f89")
                label.update(f"[{color}][auto: {self.agent_type} {self.confidence:.0%}][/]")
            else:
                label.update("")
        except Exception:
            pass

    def show(self, agent_type: str, confidence: float) -> None:
        """Show the badge with the given agent type and confidence."""
        self.agent_type = agent_type
        self.confidence = confidence
        self.display = True

    def hide(self) -> None:
        """Hide the badge."""
        self.agent_type = ""
        self.confidence = 0.0
        self.display = False
