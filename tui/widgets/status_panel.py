"""Status panel widget -- BOTTOM zone with hints and model metrics.

The BOTTOM zone is persistent (never scrolls) and shows:
  Line 1: separator
  Line 2: hint / tip line
  Line 3: keyboard shortcuts
  Line 4: model | context% | remaining tokens
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static

# Agent type color map
_AGENT_COLORS: dict[str, str] = {
    "code": "#a78bfa",  # purple
    "review": "#79c0ff",  # blue
    "test": "#e3b341",  # yellow
    "plan": "#7c8aff",  # indigo
    "docs": "#7ee787",  # green
    "debug": "#ff7b72",  # red
    "orchestrator": "#ffa657",  # orange
    "default": "#e6edf3",  # white
}


class StatusPanel(Widget):
    """Persistent BOTTOM zone: separator + hints + shortcuts + model metrics."""

    DEFAULT_CSS = """
    StatusPanel {
        dock: bottom;
        height: auto;
        max-height: 5;
        background: #0d1117;
        color: #484f58;
        padding: 0 0;
    }

    StatusPanel #status-separator {
        color: #30363d;
        height: 1;
    }

    StatusPanel #status-hint {
        color: #e6edf3;
        padding: 0 1;
        height: 1;
    }

    StatusPanel #status-shortcuts {
        color: #484f58;
        padding: 0 1;
        height: 1;
    }

    StatusPanel #status-metrics {
        color: #484f58;
        padding: 0 1;
        height: 1;
    }
    """

    model_name: reactive[str] = reactive("llama3.2")
    provider_name: reactive[str] = reactive("ollama")
    context_pct: reactive[float] = reactive(0.0)
    token_count: reactive[int] = reactive(0)
    cost: reactive[float] = reactive(0.0)
    job_status: reactive[str] = reactive("idle")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("─" * 90, id="status-separator")
            yield Label(
                '› Try "ollama run ' + self.model_name + '"',
                id="status-hint",
            )
            yield Label(
                "» shift+tab to cycle  •  /model to switch  •  /settings to configure",
                id="status-shortcuts",
            )
            yield Label(
                self._build_metrics_text(),
                id="status-metrics",
            )

    def _build_metrics_text(self) -> str:
        """Build the metrics line: [model] | X.X% used | ~Nk left | ..."""
        pct = f"{self.context_pct:.1%}"
        remaining = max(0, 200_000 - self.token_count)
        if remaining >= 1000:
            remaining_str = f"~{remaining / 1000:.1f}k"
        else:
            remaining_str = f"~{remaining}"
        parts = [
            f"[{self.model_name}]",
            f"{pct} used",
            f"{remaining_str} left",
        ]
        if self.job_status and self.job_status != "idle":
            parts.append(f"● {self.job_status}")
        return " | ".join(parts)

    def watch_model_name(self, value: str) -> None:
        self._update_hint(value)
        self._update_metrics()

    def watch_provider_name(self, _value: str) -> None:
        self._update_metrics()

    def watch_context_pct(self, _value: float) -> None:
        self._update_metrics()

    def watch_token_count(self, _value: int) -> None:
        self._update_metrics()

    def watch_cost(self, _value: float) -> None:
        self._update_metrics()

    def watch_job_status(self, _value: str) -> None:
        self._update_metrics()

    def _update_hint(self, model: str) -> None:
        try:
            self.query_one("#status-hint", Label).update(
                f'› Try "ollama run {model}"'
            )
        except Exception:
            pass

    def _update_metrics(self) -> None:
        try:
            self.query_one("#status-metrics", Label).update(
                self._build_metrics_text()
            )
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
