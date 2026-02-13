"""Chat screen -- primary view for the ollama-cli TUI."""

from __future__ import annotations

import datetime
import logging

from textual.app import ComposeResult
from textual.containers import ScrollableContainer
from textual.screen import Screen
from textual.widgets import Static

from tui.command_processor import CommandProcessor, CommandResult
from tui.widgets.chat_message import ChatMessage
from tui.widgets.input_area import InputArea
from tui.widgets.intent_badge import IntentBadge
from tui.widgets.sidebar import Sidebar
from tui.widgets.spinner import LlamaSpinner
from tui.widgets.status_panel import StatusPanel

logger = logging.getLogger(__name__)


class ChatScreen(Screen):
    """Main chat screen with message area, input, and status panel."""

    DEFAULT_CSS = """
    ChatScreen {
        layout: vertical;
    }

    #message-area {
        height: 1fr;
        padding: 1 2;
        background: #1a1b26;
    }

    #welcome-message {
        color: #565f89;
        text-style: italic;
        padding: 1 2;
        text-align: center;
    }
    """

    def __init__(self, session=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self._session = session
        self._processor: CommandProcessor | None = None
        self._message_count = 0

    def compose(self) -> ComposeResult:
        yield Sidebar()
        yield ScrollableContainer(
            Static(
                "Welcome to ollama-cli!\n\n"
                "Type a message to chat with the AI.\n"
                "Use /command for slash commands or @agent for agent routing.\n"
                "Press Ctrl+P for the command palette.",
                id="welcome-message",
            ),
            id="message-area",
        )
        yield IntentBadge()
        yield LlamaSpinner()
        yield InputArea()
        yield StatusPanel()

    def on_mount(self) -> None:
        """Initialize the screen after mounting."""
        # Hide spinner initially
        spinner = self.query_one(LlamaSpinner)
        spinner.display = False

        # Hide intent badge initially
        badge = self.query_one(IntentBadge)
        badge.display = False

        # Set up command processor if we have a session
        if self._session is not None:
            self._setup_processor()
            # Update status panel
            status = self.query_one(StatusPanel)
            status.update_from_session(self._session)

        # Focus the input
        self.query_one(InputArea).focus_input()

    def _setup_processor(self) -> None:
        """Initialize the CommandProcessor with output callbacks."""

        class _Output:
            def __init__(self, screen: ChatScreen) -> None:
                self._screen = screen

            def system(self, text: str) -> None:
                self._screen._add_system_message(text)

            def error(self, text: str) -> None:
                self._screen._add_system_message(f"Error: {text}")

            def info(self, text: str) -> None:
                self._screen._add_system_message(text)

            def response(self, text: str, agent_type: str | None = None) -> None:
                self._screen._add_assistant_message(text, agent_type)

        self._processor = CommandProcessor(
            session=self._session,
            output=_Output(self),
        )

    @staticmethod
    def _fire_hook(event_name: str, payload: dict) -> list:
        """Fire lifecycle hooks (same pattern as InteractiveMode)."""
        try:
            from server.hook_runner import HookRunner

            runner = HookRunner()
            if runner.is_enabled():
                return runner.run_hook(event_name, payload)
        except Exception:  # noqa: BLE001
            logger.debug("Hook %s failed", event_name, exc_info=True)
        return []

    async def on_input_area_submitted(self, event: InputArea.Submitted) -> None:
        """Handle user input submission."""
        text = event.value.strip()
        if not text:
            return

        # Slash command
        if text.startswith("/"):
            await self._handle_command(text)
            return

        # Agent-specific prefix
        agent_type: str | None = None
        prompt = text
        if text.startswith("@"):
            parts = text.split(" ", 1)
            if len(parts) > 1:
                agent_type = parts[0][1:]
                prompt = parts[1]
            else:
                prompt = text

        # Fire UserPromptSubmit hook before processing
        prompt_results = self._fire_hook(
            "UserPromptSubmit",
            {
                "prompt": prompt,
                "session_id": self._session.session_id if self._session else "",
                "model": self._session.model if self._session else "",
                "timestamp": datetime.datetime.now(
                    tz=datetime.timezone.utc
                ).isoformat(),
            },
        )
        # Check if denied by hook
        for pr in prompt_results:
            if (
                hasattr(pr, "permission_decision")
                and pr.permission_decision == "deny"
            ):
                self._add_system_message("Prompt blocked by UserPromptSubmit hook.")
                return

        # Intent classification (if no explicit agent type)
        if agent_type is None:
            try:
                from api.config import get_config

                cfg = get_config()
                if cfg.intent_enabled:
                    from runner.intent_classifier import classify_intent

                    result = classify_intent(
                        prompt, threshold=cfg.intent_confidence_threshold
                    )
                    if result.agent_type is not None:
                        agent_type = result.agent_type
                        if cfg.intent_show_detection:
                            badge = self.query_one(IntentBadge)
                            badge.show(agent_type, result.confidence)
            except Exception:
                logger.debug("Intent classification failed", exc_info=True)

        # Add user message to chat
        self._add_user_message(prompt)

        # Send to LLM
        await self._send_message(prompt, agent_type)

    async def _handle_command(self, line: str) -> None:
        """Dispatch a slash command."""
        if self._processor is None:
            self._add_system_message("No active session. Commands unavailable.")
            return

        result: CommandResult = await self._processor.dispatch(line)

        if result.output:
            for line_text in result.output:
                self._add_system_message(line_text)

        if result.errors:
            for err in result.errors:
                self._add_system_message(f"Error: {err}")

        if result.should_exit:
            self.app.exit()

    async def _send_message(self, prompt: str, agent_type: str | None = None) -> None:
        """Send a message to the LLM and display the response."""
        if self._session is None:
            self._add_system_message("No active session.")
            return

        # Show spinner
        spinner = self.query_one(LlamaSpinner)
        spinner.start()

        # Update status
        status = self.query_one(StatusPanel)
        status.job_status = "thinking"

        # Fire SubagentStart hook if agent routing is active
        if agent_type:
            self._fire_hook(
                "SubagentStart",
                {
                    "agent_id": f"{agent_type}-{self._session.session_id[:8]}",
                    "agent_type": agent_type,
                    "session_id": self._session.session_id,
                    "model": self._session.model,
                    "prompt_preview": prompt[:100],
                },
            )

        try:
            result = await self._session.send(prompt, agent_type=agent_type)
            content = (
                result.get("content", "") if isinstance(result, dict) else str(result)
            )
            self._add_assistant_message(content, agent_type)

            # Fire Stop hook after successful response
            self._fire_hook(
                "Stop",
                {
                    "session_id": self._session.session_id,
                    "model": self._session.model,
                    "stop_hook_active": True,
                },
            )

            # Fire SubagentStop hook if agent routing was active
            if agent_type:
                self._fire_hook(
                    "SubagentStop",
                    {
                        "agent_id": f"{agent_type}-{self._session.session_id[:8]}",
                        "agent_type": agent_type,
                        "session_id": self._session.session_id,
                    },
                )
        except ConnectionError as exc:
            self._add_system_message(
                f"Connection error: {exc}. Check if the model server is running."
            )
        except TimeoutError:
            self._add_system_message(
                "Request timed out. Try again or switch to a different model"
                " with /model."
            )
        except Exception as exc:
            self._add_system_message(f"Error: {exc}")
            logger.exception("Failed to send message")
        finally:
            spinner.stop()
            status.job_status = "idle"
            # Update status panel
            if self._session is not None:
                status.update_from_session(self._session)
            # Hide intent badge
            badge = self.query_one(IntentBadge)
            badge.hide()

    def _add_user_message(self, content: str) -> None:
        """Add a user message to the chat area."""
        self._message_count += 1
        timestamp = datetime.datetime.now().strftime("%H:%M")
        msg = ChatMessage(content=content, role="user", timestamp=timestamp)
        container = self.query_one("#message-area", ScrollableContainer)

        # Remove welcome message on first real message
        try:
            welcome = self.query_one("#welcome-message")
            welcome.remove()
        except Exception:
            pass

        container.mount(msg)
        container.scroll_end(animate=False)

    def _add_assistant_message(
        self, content: str, agent_type: str | None = None
    ) -> None:
        """Add an assistant message to the chat area."""
        self._message_count += 1
        timestamp = datetime.datetime.now().strftime("%H:%M")
        msg = ChatMessage(
            content=content,
            role="assistant",
            agent_type=agent_type,
            timestamp=timestamp,
        )
        container = self.query_one("#message-area", ScrollableContainer)
        container.mount(msg)
        container.scroll_end(animate=False)

    def _add_system_message(self, text: str) -> None:
        """Add a system/info message to the chat area."""
        container = self.query_one("#message-area", ScrollableContainer)
        msg = Static(text, classes="system-message")
        container.mount(msg)
        container.scroll_end(animate=False)
