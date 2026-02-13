"""Command processor -- shared slash command logic for Textual TUI.

Provides a UI-agnostic interface for dispatching slash commands.  The
Textual TUI delegates command handling here.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class CommandResult:
    """Result of executing a slash command."""

    should_exit: bool = False
    output: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Output callback protocol
# ---------------------------------------------------------------------------


class OutputHandler(Protocol):
    """Protocol for UI output -- implemented by TUI."""

    def system(self, text: str) -> None: ...

    def error(self, text: str) -> None: ...

    def info(self, text: str) -> None: ...

    def response(self, text: str, agent_type: str | None = None) -> None: ...


# ---------------------------------------------------------------------------
# Command registry
# ---------------------------------------------------------------------------

# Maps command name -> (handler_method_name, description, category)
COMMAND_REGISTRY: dict[str, tuple[str, str, str]] = {
    "/help": ("_cmd_help", "Full help message", "Other"),
    "/quit": ("_cmd_quit", "Exit the session", "Other"),
    "/exit": ("_cmd_quit", "Exit the session", "Other"),
    "/status": ("_cmd_status", "Show session status", "Session"),
    "/clear": ("_cmd_clear", "Clear history", "Session"),
    "/model": ("_cmd_model", "List/switch models", "Session"),
    "/provider": ("_cmd_provider", "Switch provider", "Session"),
    "/save": ("_cmd_save", "Save session", "Session"),
    "/load": ("_cmd_load", "Load session", "Session"),
    "/history": ("_cmd_history", "Show conversation history", "Session"),
    "/compact": ("_cmd_compact", "Force context compaction", "Memory"),
    "/memory": ("_cmd_memory", "View/add project memory", "Memory"),
    "/remember": ("_cmd_remember", "Store a memory entry", "Memory"),
    "/recall": ("_cmd_recall", "Recall stored memories", "Memory"),
    "/tools": ("_cmd_tools", "List available tools", "Tools"),
    "/tool": ("_cmd_tool", "Invoke a tool", "Tools"),
    "/pull": ("_cmd_pull", "Pull/download a model", "Tools"),
    "/diff": ("_cmd_diff", "Show git diff", "Tools"),
    "/mcp": ("_cmd_mcp", "Manage MCP servers", "Tools"),
    "/agents": ("_cmd_agents", "List active agents", "Agents"),
    "/set-agent-model": (
        "_cmd_set_agent_model",
        "Assign model to agent type",
        "Agents",
    ),
    "/list-agent-models": (
        "_cmd_list_agent_models",
        "List agent model assignments",
        "Agents",
    ),
    "/chain": ("_cmd_chain", "Multi-wave chain orchestration", "Agents"),
    "/team_planning": (
        "_cmd_team_planning",
        "Generate implementation plan",
        "Agents",
    ),
    "/build": ("_cmd_build", "Execute a saved plan", "Agents"),
    "/resume": ("_cmd_resume", "List/resume previous tasks", "Agents"),
    "/intent": ("_cmd_intent", "Intent classifier control", "Agents"),
    "/init": ("_cmd_init", "Initialize project", "Project"),
    "/config": ("_cmd_config", "View/set configuration", "Project"),
    "/bug": ("_cmd_bug", "File a bug report", "Project"),
    "/update_status_line": (
        "_cmd_update_status_line",
        "Update status line",
        "Other",
    ),
}


# ---------------------------------------------------------------------------
# CommandProcessor
# ---------------------------------------------------------------------------


class CommandProcessor:
    """Slash command processor for Textual TUI.

    Routes commands to handler methods and provides a clean interface
    for the Textual TUI.

    Parameters
    ----------
    session:
        The active Session object.
    output:
        Output handler implementing the :class:`OutputHandler` protocol.
    fire_hook:
        Callback to fire lifecycle hooks (optional).
    """

    def __init__(
        self,
        session: Any,
        output: OutputHandler,
        fire_hook: Callable[..., Any] | None = None,
    ) -> None:
        self.session = session
        self.output = output
        self._fire_hook = fire_hook or (lambda *a, **kw: [])

    # -- dispatch ------------------------------------------------------------

    async def dispatch(self, line: str) -> CommandResult:
        """Parse and dispatch a slash command.

        Parameters
        ----------
        line:
            The raw input line starting with ``/``.

        Returns
        -------
        :class:`CommandResult` with ``should_exit`` flag and any output/errors.
        """
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        # Bare "/" shows the command menu
        if cmd == "/":
            return self._show_menu()

        entry = COMMAND_REGISTRY.get(cmd)
        if entry is None:
            return CommandResult(
                errors=[
                    f"Unknown command: {cmd}. Type /help to see available commands."
                ]
            )

        handler_name = entry[0]
        handler = getattr(self, handler_name, None)
        if handler is None:
            return CommandResult(
                errors=[
                    f"Command {cmd} is not yet implemented in CommandProcessor."
                ]
            )

        result = handler(arg)
        if asyncio.iscoroutine(result):
            result = await result

        if isinstance(result, CommandResult):
            return result

        # Legacy bool return: True = exit, False = continue
        return CommandResult(
            should_exit=bool(result) if result is not None else False
        )

    # -- menu ----------------------------------------------------------------

    def _show_menu(self) -> CommandResult:
        """Show available commands grouped by category."""
        categories: dict[str, list[tuple[str, str]]] = {}
        for cmd, (_, desc, cat) in COMMAND_REGISTRY.items():
            if cmd == "/exit":  # Skip alias
                continue
            categories.setdefault(cat, []).append((cmd, desc))

        lines: list[str] = ["Available Commands:", "\u2500" * 50]
        for cat, cmds in categories.items():
            lines.append(f"\n  {cat}")
            for cmd_str, desc in cmds:
                lines.append(f"    {cmd_str:30s} {desc}")

        return CommandResult(output=lines)

    # -- simple commands implemented directly ---------------------------------

    def _cmd_quit(self, arg: str) -> CommandResult:
        """Signal the session to exit."""
        return CommandResult(should_exit=True)

    def _cmd_help(self, arg: str) -> CommandResult:
        """Display the full help message."""
        lines: list[str] = [
            "ollama-cli Help",
            "\u2550" * 50,
            "",
            "Usage:",
            "  Type a message to chat with the AI",
            "  Use @agent_type to route to a specific agent (e.g., @code, @review)",
            "  Use /command to run a slash command",
            "",
        ]
        for cmd, (_, desc, _cat) in COMMAND_REGISTRY.items():
            if cmd == "/exit":
                continue
            lines.append(f"  {cmd:30s} {desc}")

        lines.extend(
            [
                "",
                "Keyboard shortcuts (TUI mode):",
                "  Ctrl+P     Command palette",
                "  Ctrl+B     Toggle sidebar",
                "  Ctrl+S     Save session",
                "  Ctrl+L     Clear chat",
                "  Ctrl+,     Settings",
                "  F1         Help",
                "  Escape     Cancel / close",
            ]
        )
        return CommandResult(output=lines)

    def _cmd_status(self, arg: str) -> CommandResult:
        """Show session status."""
        lines: list[str] = []

        # Use get_status() when available (the full Session object has it).
        if hasattr(self.session, "get_status"):
            status = self.session.get_status()
            token_info: dict[str, Any] = status.get("token_metrics", {})
            context_info: dict[str, Any] = status.get("context_usage", {})

            lines.append("Session")
            lines.append(f"  ID:         {status.get('session_id', 'n/a')}")
            lines.append(f"  Model:      {status.get('model', 'n/a')}")
            lines.append(f"  Provider:   {status.get('provider', 'n/a')}")
            lines.append(f"  Uptime:     {status.get('uptime_str', 'n/a')}")
            lines.append(f"  Messages:   {status.get('messages', 0)}")
            hooks = status.get("hooks_enabled")
            if hooks is not None:
                lines.append(
                    f"  Hooks:      {'enabled' if hooks else 'disabled'}"
                )

            lines.append("Tokens")
            lines.append(
                f"  Prompt:     {token_info.get('prompt_tokens', 0):,}"
            )
            lines.append(
                f"  Completion: {token_info.get('completion_tokens', 0):,}"
            )
            lines.append(
                f"  Total:      {token_info.get('total_tokens', 0):,}"
            )
            lines.append(
                f"  Speed:      {token_info.get('tokens_per_second', 0):.1f} tok/s"
            )
            lines.append(
                f"  Cost:       ${token_info.get('cost_estimate', 0):.4f}"
            )

            lines.append("Context")
            lines.append(
                f"  Used:       {context_info.get('used', 0):,}"
                f" / {context_info.get('max', 0):,} tokens"
            )
            lines.append(
                f"  Usage:      {context_info.get('percentage', 0)}%"
            )
            lines.append(
                f"  Remaining:  {context_info.get('remaining', 0):,}"
            )

            # Auto-compact info
            if hasattr(self.session, "context_manager"):
                cm = self.session.context_manager
                compact_label = "on" if cm.auto_compact else "off"
                lines.append(
                    f"  Auto-compact: {compact_label}"
                    f" (threshold {int(cm.compact_threshold * 100)}%,"
                    f" keep last {cm.keep_last_n})"
                )
                if cm.should_compact():
                    lines.append(
                        "  Warning: Context above threshold"
                        " -- run /compact to free space"
                    )

            # Agent Communication
            if hasattr(self.session, "agent_comm"):
                comm_stats = self.session.agent_comm.get_token_savings()
                lines.append("Agent Communication")
                lines.append(
                    f"  Messages:     {comm_stats['total_messages']}"
                )
                lines.append(
                    f"  Token savings: ~{comm_stats['context_tokens_saved']:,}"
                )

            # Memory Layer
            if hasattr(self.session, "memory_layer"):
                mem_stats = self.session.memory_layer.get_token_savings()
                lines.append("Memory")
                lines.append(
                    f"  Entries:      {mem_stats['total_entries']}"
                )
                lines.append(
                    f"  Raw tokens:   {mem_stats['total_raw_tokens']:,}"
                )
                lines.append(
                    f"  Context used: {mem_stats['context_tokens_used']:,}"
                )
                lines.append(
                    f"  Saved:        ~{mem_stats['tokens_saved']:,}"
                )
        else:
            # Minimal fallback for lightweight session objects
            lines.append(f"  Model: {getattr(self.session, 'model', 'n/a')}")
            lines.append(
                f"  Provider: {getattr(self.session, 'provider', 'n/a')}"
            )
            lines.append(
                f"  Session ID: {getattr(self.session, 'session_id', 'n/a')}"
            )

        return CommandResult(output=lines)

    def _cmd_clear(self, arg: str) -> CommandResult:
        """Clear conversation history."""
        if hasattr(self.session, "context_manager"):
            self.session.context_manager.clear()
        if hasattr(self.session, "_message_count"):
            self.session._message_count = 0
        return CommandResult(output=["Conversation history cleared."])

    def _cmd_intent(self, arg: str) -> CommandResult:
        """Inspect or configure the intent classifier.

        Subcommands: on, off, show, threshold <val>, test <prompt>.
        """
        from api.config import get_config

        cfg = get_config()

        if not arg:
            status = "enabled" if cfg.intent_enabled else "disabled"
            lines = [
                f"  Intent classifier: {status}",
                f"  Confidence threshold: {cfg.intent_confidence_threshold:.2f}",
                f"  Show detection: {cfg.intent_show_detection}",
                f"  LLM fallback: {cfg.intent_llm_fallback}",
            ]
            if cfg.intent_default_agent_type:
                lines.append(
                    f"  Default agent type: {cfg.intent_default_agent_type}"
                )
            return CommandResult(output=lines)

        parts = arg.split(maxsplit=1)
        sub = parts[0].lower()

        if sub == "on":
            cfg.intent_enabled = True
            return CommandResult(output=["Intent classifier enabled."])

        if sub == "off":
            cfg.intent_enabled = False
            return CommandResult(output=["Intent classifier disabled."])

        if sub == "show":
            cfg.intent_show_detection = not cfg.intent_show_detection
            state = "on" if cfg.intent_show_detection else "off"
            return CommandResult(output=[f"Intent display toggled {state}."])

        if sub == "threshold":
            val_str = parts[1].strip() if len(parts) > 1 else ""
            if not val_str:
                return CommandResult(
                    output=[
                        f"  Current threshold: {cfg.intent_confidence_threshold:.2f}",
                        "Usage: /intent threshold <0.0-1.0>",
                    ]
                )
            try:
                val = float(val_str)
                if not 0.0 <= val <= 1.0:
                    return CommandResult(
                        errors=["Threshold must be between 0.0 and 1.0."]
                    )
                cfg.intent_confidence_threshold = val
                return CommandResult(
                    output=[f"Confidence threshold set to {val:.2f}"]
                )
            except ValueError:
                return CommandResult(errors=[f"Invalid number: {val_str}"])

        if sub == "test":
            test_prompt = parts[1].strip() if len(parts) > 1 else ""
            if not test_prompt:
                return CommandResult(
                    errors=["Usage: /intent test <prompt>"]
                )
            from runner.intent_classifier import classify_intent

            result = classify_intent(
                test_prompt, threshold=cfg.intent_confidence_threshold
            )
            lines: list[str] = []
            if result.agent_type:
                lines.append(
                    f"  Intent: {result.agent_type}"
                    f" (confidence: {result.confidence:.0%})"
                )
            else:
                lines.append(
                    f"  Intent: none"
                    f" (confidence: {result.confidence:.0%})"
                )
            lines.append(f"  Reasoning: {result.reasoning}")
            if result.matched_patterns:
                lines.append(
                    f"  Patterns: {', '.join(result.matched_patterns)}"
                )
            return CommandResult(output=lines)

        return CommandResult(
            errors=[
                f"Unknown /intent subcommand: {sub}",
                "Usage: /intent [on|off|show|threshold <val>|test <prompt>]",
            ]
        )

    # -- static helpers for UI consumers -------------------------------------

    @staticmethod
    def get_command_names() -> list[str]:
        """Return all registered command names for tab completion."""
        return list(COMMAND_REGISTRY.keys())

    @staticmethod
    def get_commands_by_category() -> dict[str, list[tuple[str, str]]]:
        """Return commands grouped by category for UI display."""
        categories: dict[str, list[tuple[str, str]]] = {}
        for cmd, (_, desc, cat) in COMMAND_REGISTRY.items():
            if cmd == "/exit":
                continue
            categories.setdefault(cat, []).append((cmd, desc))
        return categories
