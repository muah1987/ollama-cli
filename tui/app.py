"""ollama-cli TUI application powered by Textual."""

from __future__ import annotations

from textual.app import App
from textual.binding import Binding


class ChatApp(App):
    """Ollama CLI -- beautiful TUI powered by Textual."""

    TITLE = "ollama-cli"
    SUB_TITLE = "AI Coding Assistant"
    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+p", "command_palette", "Commands"),
        Binding("ctrl+b", "toggle_sidebar", "Sidebar"),
        Binding("f1", "help", "Help"),
    ]

    def __init__(self, session=None, **kwargs):
        super().__init__(**kwargs)
        self.session = session

    def on_mount(self) -> None:
        """Push the chat screen on startup."""
        from tui.screens.chat import ChatScreen

        self.push_screen(ChatScreen(session=self.session))

    def action_command_palette(self) -> None:
        """Open command palette."""
        pass  # Will be implemented later

    def action_toggle_sidebar(self) -> None:
        """Toggle sidebar visibility."""
        try:
            from tui.widgets.sidebar import Sidebar

            sidebar = self.query_one(Sidebar)
            sidebar.toggle()
        except Exception:
            pass

    def action_help(self) -> None:
        """Show help screen."""
        from tui.screens.help import HelpScreen

        self.push_screen(HelpScreen())
