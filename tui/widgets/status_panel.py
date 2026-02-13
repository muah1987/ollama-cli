"""Status panel widget -- real-time session status display."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label


# Agent type color map (matching interactive.py)
_AGENT_COLORS: dict[str, str] = {
    "code": "#bb9af7",  # magenta/purple
    "review": "#7dcfff",  # cyan
    "test": "#e0af68",  # yellow
    "plan": "#7aa2f7",  # blue
    "docs": "#9ece6a",  # green
    "debug": "#f7768e",  # red
    "orchestrator": "#ff9e64",  # orange
    "default": "#c0caf5",  # white/gray
}


class StatusPanel(Widget):
    """Persistent status bar showing model, provider, context, tokens, cost."""

    DEFAULT_CSS = """
    StatusPanel {
        dock: bottom;
        height: 1;
        background: #24283b;
        color: #565f89;
        padding: 0 1;
    }

    StatusPanel Horizontal {
        height: 1;
        width: 100%;
    }

    StatusPanel .status-item {
        width: auto;
        padding: 0 1;
    }

    StatusPanel .status-model {
        color: #7aa2f7;
        text-style: bold;
    }

    StatusPanel .status-provider {
        color: #bb9af7;
    }

    StatusPanel .status-context {
        color: #9ece6a;
    }

    StatusPanel .status-tokens {
        color: #e0af68;
    }

    StatusPanel .status-cost {
        color: #7dcfff;
    }

    StatusPanel .status-job {
        color: #f7768e;
        text-style: bold;
    }
    """

    model_name: reactive[str] = reactive("llama3.2")
    provider_name: reactive[str] = reactive("ollama")
    context_pct: reactive[float] = reactive(0.0)
    token_count: reactive[int] = reactive(0)
    cost: reactive[float] = reactive(0.0)
    job_status: reactive[str] = reactive("idle")

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Label(
                f"Model: {self.model_name}",
                classes="status-item status-model",
                id="st-model",
            )
            yield Label(
                f"Provider: {self.provider_name}",
                classes="status-item status-provider",
                id="st-provider",
            )
            yield Label(
                f"Context: {self.context_pct:.0%}",
                classes="status-item status-context",
                id="st-context",
            )
            yield Label(
                f"Tokens: {self.token_count}",
                classes="status-item status-tokens",
                id="st-tokens",
            )
            yield Label(
                f"Cost: ${self.cost:.4f}",
                classes="status-item status-cost",
                id="st-cost",
            )
            yield Label("", classes="status-item status-job", id="st-job")

    def watch_model_name(self, value: str) -> None:
        try:
            self.query_one("#st-model", Label).update(f"Model: {value}")
        except Exception:
            pass

    def watch_provider_name(self, value: str) -> None:
        try:
            self.query_one("#st-provider", Label).update(f"Provider: {value}")
        except Exception:
            pass

    def watch_context_pct(self, value: float) -> None:
        try:
            label = self.query_one("#st-context", Label)
            label.update(f"Context: {value:.0%}")
            # Color-code: green <50%, yellow <75%, red >=75%
            if value < 0.5:
                label.styles.color = "#9ece6a"
            elif value < 0.75:
                label.styles.color = "#e0af68"
            else:
                label.styles.color = "#f7768e"
        except Exception:
            pass

    def watch_token_count(self, value: int) -> None:
        try:
            self.query_one("#st-tokens", Label).update(f"Tokens: {value:,}")
        except Exception:
            pass

    def watch_cost(self, value: float) -> None:
        try:
            self.query_one("#st-cost", Label).update(f"Cost: ${value:.4f}")
        except Exception:
            pass

    def watch_job_status(self, value: str) -> None:
        try:
            label = self.query_one("#st-job", Label)
            if value and value != "idle":
                label.update(f"[{value}]")
            else:
                label.update("")
        except Exception:
            pass

    def update_from_session(self, session) -> None:
        """Bulk update from a Session object."""
        self.model_name = getattr(session, "model", "unknown")
        self.provider_name = getattr(session, "provider", "unknown")

        if hasattr(session, "context_manager"):
            cm = session.context_manager
            if hasattr(cm, "usage_ratio"):
                self.context_pct = cm.usage_ratio

        if hasattr(session, "token_counter"):
            tc = session.token_counter
            if hasattr(tc, "total_tokens"):
                self.token_count = tc.total_tokens
            if hasattr(tc, "estimated_cost"):
                self.cost = tc.estimated_cost
