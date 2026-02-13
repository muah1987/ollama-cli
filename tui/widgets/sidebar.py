"""Sidebar widget -- sessions, agents, tools panel."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Label, Static


class Sidebar(Widget):
    """Collapsible sidebar showing sessions, agents, and tools."""

    DEFAULT_CSS = """
    Sidebar {
        dock: left;
        width: 30;
        background: #1e2030;
        border-right: solid #24283b;
        padding: 1 0;
        display: block;
    }

    Sidebar.-hidden {
        display: none;
    }

    Sidebar .sidebar-header {
        text-style: bold;
        color: #7aa2f7;
        padding: 0 2;
        margin: 0 0 1 0;
    }

    Sidebar .sidebar-section {
        padding: 0 1;
        margin: 0 0 1 0;
    }

    Sidebar .section-title {
        color: #bb9af7;
        text-style: bold;
        padding: 0 1;
    }

    Sidebar .sidebar-item {
        color: #c0caf5;
        padding: 0 2;
    }

    Sidebar .sidebar-item-dim {
        color: #565f89;
        padding: 0 2;
    }
    """

    visible: reactive[bool] = reactive(True)

    def compose(self) -> ComposeResult:
        yield Label("ollama-cli", classes="sidebar-header")
        yield Static("\u2500" * 26)

        with Vertical(classes="sidebar-section"):
            yield Label("Agents", classes="section-title")
            for agent in [
                "code",
                "review",
                "test",
                "debug",
                "plan",
                "docs",
                "orchestrator",
            ]:
                yield Label(f"  \u25cf {agent}", classes="sidebar-item")

        with Vertical(classes="sidebar-section"):
            yield Label("Tools", classes="section-title")
            for tool in ["file_read", "file_write", "shell_exec", "web_fetch"]:
                yield Label(f"  \u25c6 {tool}", classes="sidebar-item-dim")

        with Vertical(classes="sidebar-section"):
            yield Label("Shortcuts", classes="section-title")
            yield Label("  Ctrl+P  Commands", classes="sidebar-item-dim")
            yield Label("  Ctrl+B  Sidebar", classes="sidebar-item-dim")
            yield Label("  Ctrl+S  Save", classes="sidebar-item-dim")
            yield Label("  F1      Help", classes="sidebar-item-dim")

    def toggle(self) -> None:
        """Toggle sidebar visibility."""
        self.visible = not self.visible
        self.toggle_class("-hidden")
