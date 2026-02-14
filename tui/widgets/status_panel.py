"""Status panel widget -- BOTTOM zone with hints and model metrics.

The BOTTOM zone is persistent (never scrolls) and shows:
  Line 1: separator
  Line 2: hint / tip line
  Line 3: keyboard shortcuts
  Line 4: model | context% | progress bar | remaining tokens | uuid | cwd
"""

from __future__ import annotations

import os

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
        height: auto;
        max-height: 5;
        background: #0d1117;
        color: #484f58;
        padding: 0 0;
    }

    StatusPanel #status-separator {
        color: #b2a266;
        height: 1;
        border-top: solid #b2a266;
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

    # Default context window size (tokens) -- overridden by session data
    _DEFAULT_CONTEXT_SIZE = 200_000
    # Display length for truncated session ID in the status bar (8 hex + dash + 4 hex)
    _SESSION_ID_DISPLAY_LEN = 13

    model_name: reactive[str] = reactive("llama3.2")
    provider_name: reactive[str] = reactive("ollama")
    context_pct: reactive[float] = reactive(0.0)
    token_count: reactive[int] = reactive(0)
    cost: reactive[float] = reactive(0.0)
    job_status: reactive[str] = reactive("idle")
    context_max: reactive[int] = reactive(_DEFAULT_CONTEXT_SIZE)
    session_id: reactive[str] = reactive("")

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static("", id="status-separator")
            yield Label(
                '› Try "ollama run ' + self.model_name + '"',
                id="status-hint",
            )
            yield Label(
                "» shift+tab to cycle  •  /settings to configure",
                id="status-shortcuts",
            )
            yield Label(
                self._build_metrics_text(),
                id="status-metrics",
            )

    def _build_metrics_text(self) -> str:
        """Build the metrics line with progress bar, per the reference layout.

        Format: [model] | X.X% used |##------%| ~Nk left | uuid | cwd: path
        """
        pct = self.context_pct
        pct_str = f"{pct:.1%}"

        # Progress bar: 16 display chars (N filled '#' + M empty '-' + '%')
        bar_total = 16
        filled = min(int(pct * (bar_total - 1)), bar_total - 1)
        bar = "#" * filled + "-" * (bar_total - 1 - filled) + "%"
        progress = f"|{bar}|"

        remaining = max(0, self.context_max - self.token_count)
        if remaining >= 1000:
            remaining_str = f"~{remaining / 1000:.1f}k"
        else:
            remaining_str = f"~{remaining}"

        cwd_short = os.path.basename(os.getcwd()) or "~"

        # Build the line: [model] | X.X% used |bar| ~Nk left | uuid | cwd: path
        # The progress bar already has pipe delimiters, so assemble manually
        line = f"[{self.model_name}] | {pct_str} used {progress} {remaining_str} left"
        if self.session_id:
            line += f" | {self.session_id[: self._SESSION_ID_DISPLAY_LEN]}"
        line += f" | cwd: {cwd_short}"
        if self.job_status and self.job_status != "idle":
            line += f" | \u25cf {self.job_status}"
        return line

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

    def watch_context_max(self, _value: int) -> None:
        self._update_metrics()

    def watch_session_id(self, _value: str) -> None:
        self._update_metrics()

    def _update_hint(self, model: str) -> None:
        try:
            self.query_one("#status-hint", Label).update(f'› Try "ollama run {model}"')
        except Exception:
            pass

    def _update_metrics(self) -> None:
        try:
            self.query_one("#status-metrics", Label).update(self._build_metrics_text())
        except Exception:
            pass

    def update_from_session(self, session) -> None:
        """Bulk update from a Session object."""
        self.model_name = getattr(session, "model", "unknown")
        self.provider_name = getattr(session, "provider", "unknown")
        self.session_id = getattr(session, "session_id", "")

        if hasattr(session, "context_manager"):
            cm = session.context_manager
            if hasattr(cm, "usage_ratio"):
                self.context_pct = cm.usage_ratio
            if hasattr(cm, "max_tokens"):
                self.context_max = cm.max_tokens

        if hasattr(session, "token_counter"):
            tc = session.token_counter
            if hasattr(tc, "total_tokens"):
                self.token_count = tc.total_tokens
            if hasattr(tc, "estimated_cost"):
                self.cost = tc.estimated_cost
