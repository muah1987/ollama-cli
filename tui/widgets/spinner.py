"""Llama spinner widget -- animated thinking indicator."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label

_LLAMA_SPINNER_FRAMES = [
    "🦙 Thinking...",
    "🦙 Chewing on that...",
    "🦙 Ruminating...",
    "🦙 Spitting ideas...",
    "🦙 Grazing for answers...",
    "🦙 Trotting through context...",
    "🦙 Llama-nating...",
    "🦙 Herding tokens...",
]


class LlamaSpinner(Widget):
    """Animated llama-themed spinner for thinking state."""

    DEFAULT_CSS = """
    LlamaSpinner {
        height: 1;
        width: 100%;
        padding: 0 2;
        color: #e0af68;
        text-style: italic;
    }
    """

    frame_index: reactive[int] = reactive(0)
    spinning: reactive[bool] = reactive(False)

    def compose(self) -> ComposeResult:
        yield Label("", id="spinner-label")

    def start(self) -> None:
        """Start the spinner animation."""
        self.spinning = True
        self.frame_index = 0
        self.display = True
        self._advance()
        self.set_interval(0.8, self._advance, name="spinner-timer")

    def stop(self) -> None:
        """Stop the spinner animation."""
        self.spinning = False
        self.display = False
        # Remove the timer by name
        try:
            for timer in list(self._timers):
                if timer.name == "spinner-timer":
                    timer.stop()
        except Exception:
            pass

    def _advance(self) -> None:
        """Advance to the next spinner frame."""
        if not self.spinning:
            return
        try:
            label = self.query_one("#spinner-label", Label)
            label.update(
                _LLAMA_SPINNER_FRAMES[
                    self.frame_index % len(_LLAMA_SPINNER_FRAMES)
                ]
            )
            self.frame_index += 1
        except Exception:
            pass
