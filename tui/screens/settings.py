"""Settings screen -- interactive configuration."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static


class SettingsScreen(Screen):
    """Interactive settings configuration screen."""

    BINDINGS = [("escape", "pop_screen", "Back")]

    DEFAULT_CSS = """
    SettingsScreen {
        layout: vertical;
        background: #0d1117;
    }

    #settings-container {
        padding: 2 4;
        height: 1fr;
    }

    .setting-title {
        text-style: bold;
        color: #7c8aff;
        padding: 1 0;
    }

    .setting-row {
        height: 3;
        padding: 0 2;
    }

    .setting-label {
        width: 30;
        color: #e6edf3;
    }

    .setting-value {
        color: #7ee787;
    }

    #btn-back {
        margin: 2 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="settings-container"):
            yield Label("Settings", classes="setting-title")
            yield Static("\u2500" * 50)
            yield Static("")

            # Model
            yield Label("Model Configuration", classes="setting-title")
            yield Label(
                "  Current model and provider settings are configured via /model and /provider commands.",
                classes="setting-label",
            )
            yield Static("")

            # Intent Classifier
            yield Label("Intent Classifier", classes="setting-title")
            yield Label(
                "  Configure via /intent command: /intent on|off|threshold <val>",
                classes="setting-label",
            )
            yield Static("")

            # Theme
            yield Label("Theme", classes="setting-title")
            yield Label(
                "  Switch themes with /theme dark or /theme light",
                classes="setting-label",
            )
            yield Static("")

            yield Button("Back", id="btn-back", variant="primary")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-back":
            self.app.pop_screen()

    def action_pop_screen(self) -> None:
        self.app.pop_screen()
