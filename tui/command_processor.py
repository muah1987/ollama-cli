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
    "/settings": ("_cmd_config", "View/set configuration (alias)", "Project"),
    "/bug": ("_cmd_bug", "File a bug report", "Project"),
    "/plan": (
        "_cmd_team_planning",
        "Generate implementation plan (alias)",
        "Agents",
    ),
    "/complete_w_team": (
        "_cmd_complete_w_team",
        "Team plan-then-build completion loop",
        "Agents",
    ),
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

    # -- model/provider commands ---------------------------------------------

    def _cmd_model(self, arg: str) -> CommandResult:
        """List or switch the active model."""
        if not arg:
            lines: list[str] = []
            lines.append(f"  Current model: {getattr(self.session, 'model', 'n/a')}")
            lines.append(f"  Current provider: {getattr(self.session, 'provider', 'n/a')}")
            lines.append("")
            lines.append("  Use /model <name> to switch model.")
            return CommandResult(output=lines)

        old_model = getattr(self.session, "model", "unknown")
        self.session.model = arg
        return CommandResult(
            output=[f"Model switched: {old_model} → {arg}"]
        )

    def _cmd_provider(self, arg: str) -> CommandResult:
        """Switch the active provider."""
        valid = ("ollama", "claude", "gemini", "codex", "hf")
        if not arg:
            lines = [
                f"  Current provider: {getattr(self.session, 'provider', 'n/a')}",
                f"  Available: {', '.join(valid)}",
                "",
                "Usage: /provider <name>",
            ]
            return CommandResult(output=lines)

        name = arg.lower()
        if name not in valid:
            return CommandResult(
                errors=[
                    f"Unknown provider: {arg}",
                    f"  Available: {', '.join(valid)}",
                ]
            )

        old = getattr(self.session, "provider", "unknown")
        self.session.provider = name
        if hasattr(self.session, "token_counter"):
            self.session.token_counter.provider = name
        return CommandResult(output=[f"Provider switched: {old} → {name}"])

    # -- session commands ----------------------------------------------------

    def _cmd_save(self, arg: str) -> CommandResult:
        """Save the current session."""
        if hasattr(self.session, "save"):
            path = self.session.save(arg or None)
            return CommandResult(output=[f"Session saved to: {path}"])
        return CommandResult(errors=["Session save not available."])

    def _cmd_load(self, arg: str) -> CommandResult:
        """Load a session from file."""
        if not arg:
            return CommandResult(errors=["Usage: /load <name>"])

        try:
            from model.session import Session

            loaded = Session.load(arg)

            # Replace the current session state
            self.session.session_id = loaded.session_id
            self.session.model = loaded.model
            self.session.provider = loaded.provider
            if hasattr(loaded, "context_manager"):
                self.session.context_manager = loaded.context_manager
            if hasattr(loaded, "token_counter"):
                self.session.token_counter = loaded.token_counter
            if hasattr(loaded, "hooks_enabled"):
                self.session.hooks_enabled = loaded.hooks_enabled
            if hasattr(loaded, "start_time"):
                self.session.start_time = loaded.start_time
            if hasattr(loaded, "_message_count"):
                self.session._message_count = loaded._message_count

            msg_count = getattr(loaded, "_message_count", 0)
            return CommandResult(
                output=[
                    f"Session loaded: {loaded.session_id}"
                    f" ({msg_count} messages, model={loaded.model})"
                ]
            )
        except FileNotFoundError as exc:
            return CommandResult(errors=[str(exc)])
        except ImportError:
            return CommandResult(errors=["Session module not available."])
        except Exception as exc:
            return CommandResult(errors=[f"Failed to load session: {exc}"])

    def _cmd_history(self, arg: str) -> CommandResult:
        """Show conversation history."""
        if hasattr(self.session, "context_manager"):
            messages = self.session.context_manager.messages
            if not messages:
                return CommandResult(output=["No conversation history."])

            lines: list[str] = []
            for i, msg in enumerate(messages, start=1):
                if isinstance(msg, dict):
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                else:
                    role = "message"
                    content = str(msg)
                display = content if len(content) <= 200 else content[:200] + "..."
                lines.append(f"[{i}] {role}: {display}")
            return CommandResult(output=lines)

        return CommandResult(output=["No conversation history available."])

    # -- memory commands -----------------------------------------------------

    async def _cmd_compact(self, arg: str) -> CommandResult:
        """Force context compaction with hook support."""
        if not hasattr(self.session, "context_manager"):
            return CommandResult(output=["Context compaction not available."])

        cm = self.session.context_manager
        usage_before = cm.get_context_usage() if hasattr(cm, "get_context_usage") else {}
        msg_count = len(cm.messages) if hasattr(cm, "messages") else 0

        lines: list[str] = ["Context Compaction"]
        if usage_before:
            lines.append(
                f"  Before: {usage_before.get('used', 0):,} / {usage_before.get('max', 0):,} tokens "
                f"({usage_before.get('percentage', 0)}%) — {msg_count} messages"
            )

        keep_last = getattr(cm, "keep_last_n", 4)
        if msg_count <= keep_last:
            lines.append("  Nothing to compact (message count ≤ keep_last_n).")
            return CommandResult(output=lines)

        # Fire PreCompact hook
        self._fire_hook(
            "PreCompact",
            {
                "session_id": getattr(self.session, "session_id", ""),
                "context_used": usage_before.get("used", 0),
                "context_max": usage_before.get("max", 0),
                "context_percentage": usage_before.get("percentage", 0),
                "message_count": msg_count,
                "trigger": "manual",
            },
        )

        try:
            if hasattr(self.session, "compact"):
                result = await self.session.compact()
            elif hasattr(cm, "compact"):
                result = cm.compact()
                if asyncio.iscoroutine(result):
                    result = await result
            else:
                return CommandResult(output=["Context compaction not available."])
        except Exception as exc:
            return CommandResult(errors=[f"Compaction failed: {exc}"])

        usage_after = cm.get_context_usage() if hasattr(cm, "get_context_usage") else {}
        if isinstance(result, dict):
            removed = result.get("messages_removed", 0)
            saved = result.get("before_tokens", 0) - result.get("after_tokens", 0)
        else:
            removed = 0
            saved = 0

        if usage_after:
            msg_after = len(cm.messages) if hasattr(cm, "messages") else 0
            lines.append(
                f"  After:  {usage_after.get('used', 0):,} / {usage_after.get('max', 0):,} tokens "
                f"({usage_after.get('percentage', 0)}%) — {msg_after} messages"
            )
        lines.append(f"  Removed {removed} messages, freed ~{saved:,} tokens")
        return CommandResult(output=lines)

    def _cmd_memory(self, arg: str) -> CommandResult:
        """View or add to project memory (OLLAMA.md)."""
        from pathlib import Path

        memory_file = Path("OLLAMA.md")

        if not arg:
            if memory_file.is_file():
                try:
                    content = memory_file.read_text(encoding="utf-8")
                    lines = ["--- Project Memory (OLLAMA.md) ---"]
                    display = content[:2000]
                    lines.append(display)
                    if len(content) > 2000:
                        lines.append("...")
                    return CommandResult(output=lines)
                except OSError as exc:
                    return CommandResult(errors=[f"Cannot read OLLAMA.md: {exc}"])
            return CommandResult(
                output=["No OLLAMA.md found. Use /memory <note> to create one, or /init to set up."]
            )

        try:
            with open(memory_file, "a", encoding="utf-8") as f:
                f.write(f"\n- {arg}\n")
            return CommandResult(output=[f"Added to OLLAMA.md: {arg}"])
        except OSError as exc:
            return CommandResult(errors=[f"Cannot write to OLLAMA.md: {exc}"])

    def _cmd_remember(self, arg: str) -> CommandResult:
        """Store a memory entry."""
        if not arg or " " not in arg:
            return CommandResult(errors=["Usage: /remember <key> <content>"])

        if hasattr(self.session, "memory_layer"):
            key, content = arg.split(" ", 1)
            self.session.memory_layer.store(key, content)
            return CommandResult(output=[f"Remembered '{key}': {content}"])

        return CommandResult(errors=["Memory layer not available."])

    def _cmd_recall(self, arg: str) -> CommandResult:
        """Recall stored memories."""
        if not hasattr(self.session, "memory_layer"):
            return CommandResult(errors=["Memory layer not available."])

        if not arg:
            stats = self.session.memory_layer.get_token_savings()
            if stats["total_entries"] == 0:
                return CommandResult(
                    output=["No memories stored. Use /remember <key> <content> to add."]
                )
            lines = [f"Stored Memories ({stats['total_entries']} entries):"]
            for entry in self.session.memory_layer.get_all_entries():
                lines.append(f"  [{entry.category}] {entry.key}: {entry.content}")
            return CommandResult(output=lines)

        results = self.session.memory_layer.recall_relevant(arg)
        if not results:
            return CommandResult(output=[f"No memories matching '{arg}'."])

        lines = [f"Memories matching '{arg}':"]
        for entry in results:
            lines.append(f"  [{entry.category}] {entry.key}: {entry.content}")
        return CommandResult(output=lines)

    # -- tools commands ------------------------------------------------------

    def _cmd_tools(self, arg: str) -> CommandResult:
        """List available tools."""
        try:
            from skills.tools import list_tools

            tools = list_tools()
            lines = ["Available tools:"]
            for t in tools:
                lines.append(f"  {t['name']:30s} {t['description']:35s} [{t['risk']}]")
            lines.append("")
            lines.append("Use /tool <name> [args...] to invoke a tool.")
            return CommandResult(output=lines)
        except ImportError:
            return CommandResult(errors=["Tools module not available."])

    def _cmd_tool(self, arg: str) -> CommandResult:
        """Invoke a tool by name with hook integration."""
        if not arg:
            return CommandResult(
                errors=["Usage: /tool <name> [args...]", "  Example: /tool file_read README.md"]
            )

        try:
            from skills.tools import get_tool

            parts = arg.split(maxsplit=1)
            tool_name = parts[0]
            tool_arg = parts[1] if len(parts) > 1 else ""

            entry = get_tool(tool_name)
            if entry is None:
                return CommandResult(errors=[f"Unknown tool: {tool_name}"])

            # Check allowed-tools filter
            from api.config import get_config as _get_cfg

            cfg = _get_cfg()
            allowed = getattr(cfg, "allowed_tools", None)
            if allowed and tool_name not in allowed:
                return CommandResult(
                    errors=[f"Tool '{tool_name}' is not in --allowed-tools list."]
                )

            # Fire PreToolUse hook for approval
            hook_payload = {
                "tool_name": tool_name,
                "arguments": tool_arg,
                "risk": entry.get("risk", "unknown"),
            }
            try:
                results = self._fire_hook("PreToolUse", hook_payload)
                if results:
                    for r in results:
                        decision = getattr(r, "permission_decision", None)
                        if decision == "deny":
                            return CommandResult(
                                errors=[f"Tool '{tool_name}' blocked by PreToolUse hook."]
                            )
            except Exception:
                logger.debug("PreToolUse hook check failed, proceeding", exc_info=True)

            # Execute the tool
            fn = entry.get("function")
            if fn is None:
                return CommandResult(errors=[f"Tool '{tool_name}' has no callable function."])

            try:
                if tool_name == "file_read":
                    result = fn(tool_arg)
                elif tool_name == "file_write":
                    write_parts = tool_arg.split(maxsplit=1)
                    if len(write_parts) < 2:
                        return CommandResult(
                            errors=["Usage: /tool file_write <path> <content>"]
                        )
                    result = fn(write_parts[0], write_parts[1])
                elif tool_name == "file_edit":
                    edit_parts = tool_arg.split("|||")
                    if len(edit_parts) != 3:
                        return CommandResult(
                            errors=["Usage: /tool file_edit <path>|||<old_text>|||<new_text>"]
                        )
                    result = fn(edit_parts[0].strip(), edit_parts[1], edit_parts[2])
                elif tool_name == "grep_search":
                    search_parts = tool_arg.split(maxsplit=1)
                    pattern = search_parts[0] if search_parts else ""
                    path = search_parts[1] if len(search_parts) > 1 else "."
                    result = fn(pattern, path)
                elif tool_name == "shell_exec":
                    result = fn(tool_arg)
                elif tool_name == "web_fetch":
                    result = fn(tool_arg)
                elif tool_name == "model_pull":
                    force = "--force" in tool_arg
                    name = tool_arg.replace("--force", "").strip()
                    result = fn(name, force=force)
                else:
                    result = fn(tool_arg) if tool_arg else fn()
            except Exception as exc:
                result = {"error": str(exc)}

            # Fire PostToolUse hook
            try:
                post_payload = {"tool_name": tool_name, "result": str(result)[:500]}
                self._fire_hook("PostToolUse", post_payload)
            except Exception:
                logger.debug("PostToolUse hook failed", exc_info=True)

            # Handle result
            if isinstance(result, dict) and "error" in result:
                # Fire PostToolUseFailure hook
                self._fire_hook(
                    "PostToolUseFailure",
                    {
                        "tool_name": tool_name,
                        "tool_input": tool_arg,
                        "error": result["error"],
                        "session_id": getattr(self.session, "session_id", ""),
                    },
                )
                return CommandResult(errors=[f"Error: {result['error']}"])

            import json as _json

            if isinstance(result, dict):
                output_text = _json.dumps(result, indent=2, default=str)
            else:
                output_text = str(result) if result is not None else "(no output)"

            lines = [f"[{tool_name}] result:"]
            if len(output_text) > 3000:
                lines.append(output_text[:3000])
                lines.append(f"... ({len(output_text) - 3000} more characters)")
            else:
                lines.append(output_text)
            return CommandResult(output=lines)
        except ImportError:
            return CommandResult(errors=["Tools module not available."])

    def _cmd_pull(self, arg: str) -> CommandResult:
        """Pull/download a model from the registry."""
        if not arg:
            return CommandResult(
                errors=[
                    "Usage: /pull <model_name> [--force]",
                    "  Example: /pull llama3.2",
                    "  Force:   /pull --force llama3.2",
                ]
            )

        try:
            from skills.tools import tool_model_pull

            force = "--force" in arg
            model_name = arg.replace("--force", "").strip()
            if not model_name:
                return CommandResult(errors=["No model name provided."])

            action = "Force-pulling" if force else "Pulling"
            result = tool_model_pull(model_name, force=force)

            lines: list[str] = [f"{action} model: {model_name}"]

            if "error" in result:
                return CommandResult(
                    output=lines,
                    errors=[f"Pull failed: {result['error']}"],
                )

            status = result.get("status", "unknown")
            messages = result.get("messages", [])
            if status == "success":
                lines.append(f"✅ Successfully pulled {model_name}")
            else:
                lines.append(f"Pull completed with status: {status}")
            if messages:
                for msg in messages[-5:]:
                    lines.append(f"  {msg}")
            lines.append(f"  Use /model {model_name} to switch to this model.")
            return CommandResult(output=lines)
        except ImportError:
            return CommandResult(errors=["Model pull tool not available."])

    def _cmd_diff(self, arg: str) -> CommandResult:
        """Show git diff of the working directory."""
        import subprocess

        try:
            proc = subprocess.run(
                ["git", "diff", "--stat"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode != 0:
                return CommandResult(errors=["Not a git repository or git not available."])
            stat_output = proc.stdout.strip()
            if not stat_output:
                return CommandResult(output=["No uncommitted changes."])

            lines = ["--- Git Diff (stat) ---", stat_output]
            proc2 = subprocess.run(
                ["git", "diff", "--no-color"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            diff_text = proc2.stdout.strip()
            if diff_text:
                if len(diff_text) > 3000:
                    lines.append(diff_text[:3000])
                    lines.append(f"... ({len(diff_text) - 3000} more characters)")
                else:
                    lines.append(diff_text)
            return CommandResult(output=lines)
        except FileNotFoundError:
            return CommandResult(errors=["git is not installed."])
        except subprocess.TimeoutExpired:
            return CommandResult(errors=["git diff timed out."])

    def _cmd_mcp(self, arg: str) -> CommandResult:
        """Manage MCP servers with full subcommand support."""
        try:
            import json as _json

            from api.mcp_client import get_mcp_client

            client = get_mcp_client()

            if not arg:
                servers = client.list_servers()
                lines = ["MCP Servers:"]
                if not servers:
                    lines.append("  No MCP servers configured.")
                    lines.append("  Edit .ollama/mcp.json to add servers.")
                else:
                    for s in servers:
                        name = s.get("name", "unknown")
                        enabled = s.get("enabled", False)
                        has_cred = s.get("has_credentials", False)
                        desc = s.get("description", "")
                        status = "● enabled" if enabled else "○ disabled"
                        cred = "✓" if has_cred else "✗"
                        lines.append(f"  {status} {name:20s} {desc}  [cred: {cred}]")
                lines.append("")
                lines.append("Commands: /mcp enable|disable|tools|invoke <name>")
                return CommandResult(output=lines)

            parts = arg.split(maxsplit=2)
            action = parts[0].lower()

            if action == "enable" and len(parts) >= 2:
                name = parts[1]
                if client.enable_server(name):
                    return CommandResult(output=[f"MCP server '{name}' enabled."])
                return CommandResult(errors=[f"Unknown MCP server: {name}"])

            if action == "disable" and len(parts) >= 2:
                name = parts[1]
                if client.disable_server(name):
                    return CommandResult(output=[f"MCP server '{name}' disabled."])
                return CommandResult(errors=[f"Unknown MCP server: {name}"])

            if action == "tools":
                name = parts[1] if len(parts) >= 2 else None
                if name:
                    tools = client.discover_tools(name)
                    if tools:
                        lines = [f"Tools from {name}:"]
                        for t in tools:
                            lines.append(f"  {t.name:30s} {t.description}")
                        return CommandResult(output=lines)
                    return CommandResult(
                        output=[f"No tools discovered from {name} (is it enabled and accessible?)."]
                    )
                all_tools = client.list_discovered_tools()
                if all_tools:
                    lines = ["Discovered MCP tools:"]
                    for t in all_tools:
                        lines.append(f"  {t['name']:40s} {t['description']}")
                    return CommandResult(output=lines)
                return CommandResult(
                    output=["No MCP tools discovered yet. Use /mcp tools <server> to discover."]
                )

            if action == "invoke" and len(parts) >= 2:
                invoke_parts = parts[1].split(maxsplit=1)
                server_name = invoke_parts[0]
                if len(invoke_parts) >= 2:
                    rest = invoke_parts[1]
                elif len(parts) >= 3:
                    rest = parts[2]
                else:
                    return CommandResult(
                        errors=["Usage: /mcp invoke <server> <tool> [args_json]"]
                    )
                tool_parts = rest.split(maxsplit=1)
                tool_name = tool_parts[0]
                args_json = tool_parts[1] if len(tool_parts) > 1 else "{}"
                try:
                    arguments = _json.loads(args_json)
                except _json.JSONDecodeError:
                    return CommandResult(errors=[f"Invalid JSON arguments: {args_json}"])
                result = client.invoke_tool(server_name, tool_name, arguments)
                if "error" in result:
                    return CommandResult(errors=[f"MCP error: {result['error']}"])
                output_text = _json.dumps(result, indent=2, default=str)[:3000]
                return CommandResult(
                    output=[f"[mcp:{server_name}:{tool_name}] result:", output_text]
                )

            return CommandResult(
                errors=["Usage: /mcp [enable|disable|tools|invoke] <name>"]
            )
        except ImportError:
            return CommandResult(errors=["MCP client not available."])

    # -- agent commands ------------------------------------------------------

    def _cmd_agents(self, arg: str) -> CommandResult:
        """List active agents."""
        lines: list[str] = []
        if hasattr(self.session, "context_manager"):
            cm = self.session.context_manager
            sub_contexts = getattr(cm, "_sub_contexts", {})
            if sub_contexts:
                lines.append("Active Sub-Agents:")
                for cid, sub in sub_contexts.items():
                    usage = sub.get_context_usage()
                    lines.append(
                        f"  ● {cid}: {usage['used']:,}/{usage['max']:,} tokens ({usage['percentage']}%)"
                    )
            else:
                lines.append("No active sub-agents.")
        else:
            lines.append("No active sub-agents.")

        if hasattr(self.session, "agent_comm"):
            comm_stats = self.session.agent_comm.get_token_savings()
            lines.append("")
            lines.append("Agent Communication:")
            lines.append(f"  Messages:     {comm_stats['total_messages']}")
            lines.append(f"  Tokens saved: ~{comm_stats['context_tokens_saved']:,}")

        return CommandResult(output=lines)

    def _cmd_set_agent_model(self, arg: str) -> CommandResult:
        """Assign a model to an agent type."""
        if not arg:
            return CommandResult(
                errors=[
                    "Usage: /set-agent-model <type:provider:model>",
                    "  Example: /set-agent-model code:ollama:codestral:latest",
                ]
            )

        parts = arg.split(":", maxsplit=2)
        if len(parts) < 3:
            return CommandResult(errors=["Invalid format. Use: type:provider:model"])

        agent_type, provider, model = parts
        if hasattr(self.session, "provider_router"):
            self.session.provider_router.set_agent_model(agent_type, provider, model)
        return CommandResult(
            output=[f"Agent '{agent_type}' assigned to {provider}:{model}"]
        )

    def _cmd_list_agent_models(self, arg: str) -> CommandResult:
        """List agent model assignments."""
        try:
            from api.provider_router import _AGENT_MODEL_MAP

            if not _AGENT_MODEL_MAP:
                return CommandResult(output=["No agent model assignments configured."])

            lines = ["Agent Model Assignments:"]
            for agent_type, (provider, model) in _AGENT_MODEL_MAP.items():
                lines.append(f"  {agent_type}: {provider}:{model}")
            return CommandResult(output=lines)
        except ImportError:
            return CommandResult(errors=["Provider router not available."])

    async def _cmd_chain(self, arg: str) -> CommandResult:
        """Run multi-wave chain orchestration pipeline."""
        if not arg:
            return CommandResult(
                errors=[
                    "Usage: /chain <prompt>",
                    "  Runs a multi-wave chain: analyze → plan → execute → finalize",
                ]
            )

        try:
            from runner.chain_controller import ChainController

            controller = ChainController(self.session)
            result = await controller.run_chain(arg)

            run_id = result.get("run_id", "???")
            total_duration = result.get("total_duration", 0)
            wave_count = result.get("wave_count", 0)

            lines = [
                "🔗 Chain Orchestration",
                f"  Prompt: {arg[:100]}{'...' if len(arg) > 100 else ''}",
                "",
                f"📊 Chain Complete (run: {run_id})",
                f"  Waves: {wave_count} | Duration: {total_duration:.1f}s",
            ]

            for wr in result.get("wave_results", []):
                lines.append(
                    f"  • {wr.get('wave', '?')}: "
                    f"{wr.get('agents', 0)} agents, {wr.get('duration', 0):.1f}s"
                )

            final_output = result.get("final_output", "")
            if final_output:
                lines.append("")
                lines.append("📝 Final Output")
                lines.append(final_output[:3000])
                if len(final_output) > 3000:
                    lines.append(f"... ({len(final_output) - 3000} more characters)")

            if hasattr(self.session, "agent_comm"):
                comm_stats = self.session.agent_comm.get_token_savings()
                lines.append(
                    f"  agent messages: {comm_stats['total_messages']}"
                    f" • token savings: {comm_stats['context_tokens_saved']:,}"
                )

            return CommandResult(output=lines)
        except ImportError:
            return CommandResult(errors=["Chain controller not available."])
        except Exception as exc:
            logger.exception("Chain orchestration failed")
            return CommandResult(errors=[f"Chain failed: {exc}"])

    async def _cmd_team_planning(self, arg: str) -> CommandResult:
        """Generate an implementation plan with hook and agent support."""
        import json as _json
        import re
        from datetime import datetime, timezone
        from pathlib import Path

        if not arg:
            return CommandResult(
                errors=[
                    "Usage: /team_planning <description>",
                    "  (also available as /plan)",
                    "  Generates an engineering plan and saves it to specs/.",
                ]
            )

        specs_dir = Path("specs")
        specs_dir.mkdir(parents=True, exist_ok=True)

        slug = re.sub(r"[^a-z0-9]+", "-", arg.lower()).strip("-")[:60]
        plan_file = specs_dir / f"{slug}.md"

        planning_prompt = (
            "Create a detailed engineering implementation plan for the following requirement.\n\n"
            f"Requirement: {arg}\n\n"
            "The plan MUST include ALL of the following sections:\n"
            "## Task Description\n## Objective\n## Relevant Files\n"
            "## Step by Step Tasks\n## Acceptance Criteria\n## Team Orchestration\n"
            "### Team Members\n\n"
            "For each step include: Task ID, Depends On, Assigned To, Parallel flag, "
            "and specific actions.\n\n"
            f"Format as Markdown starting with: # Plan: {arg[:80]}\n"
        )

        # Create sub-context if session supports it
        planner_ctx_id = f"plan-{slug}"
        if hasattr(self.session, "create_sub_context"):
            self.session.create_sub_context(planner_ctx_id)

        # Inject memories if available
        if hasattr(self.session, "memory_layer"):
            memory_block = self.session.memory_layer.get_context_block(max_tokens=300)
            if memory_block:
                planning_prompt += f"\n\n## Recalled project context\n{memory_block}\n"

        # Announce via agent comm bus
        if hasattr(self.session, "agent_comm"):
            self.session.agent_comm.send(
                sender_id="orchestrator",
                recipient_id="planner",
                content=f"Planning task: {arg[:120]}",
                message_type="task",
            )

        # Send to model
        try:
            if hasattr(self.session, "send"):
                result = await self.session.send(
                    planning_prompt,
                    agent_type="plan",
                    context_id=planner_ctx_id,
                )
                plan_content = result.get("content", "")
            else:
                return CommandResult(
                    errors=["Session does not support send(). Cannot generate plan."]
                )
        except Exception as exc:
            return CommandResult(errors=[f"Failed to generate plan: {exc}"])

        if not plan_content or plan_content.startswith("[placeholder]"):
            return CommandResult(errors=["Model returned an empty or placeholder plan."])

        # Store plan in memory
        if hasattr(self.session, "memory_layer"):
            self.session.memory_layer.store(
                key=f"plan:{slug}",
                content=f"Plan for: {arg[:200]}",
                category="fact",
                importance=5,
            )

        # Notify via comm bus
        if hasattr(self.session, "agent_comm"):
            self.session.agent_comm.send(
                sender_id="planner",
                recipient_id="orchestrator",
                content=f"Plan complete: {slug} ({len(plan_content)} chars)",
                message_type="result",
            )

        # Write the plan file
        try:
            plan_file.write_text(plan_content, encoding="utf-8")
        except OSError as exc:
            return CommandResult(errors=[f"Cannot write plan: {exc}"])

        # Fire Stop hook so validators can check
        hook_payload = {
            "event": "team_planning",
            "plan_file": str(plan_file),
            "directory": "specs",
            "extension": ".md",
        }
        try:
            self._fire_hook("Stop", hook_payload)
        except Exception:
            logger.debug("Stop hook failed after team_planning", exc_info=True)

        # Save task record
        task_record = {
            "id": slug,
            "type": "team_planning",
            "description": arg,
            "plan_file": str(plan_file),
            "session_id": getattr(self.session, "session_id", ""),
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "status": "planned",
        }
        tasks_dir = Path(".ollama/tasks")
        tasks_dir.mkdir(parents=True, exist_ok=True)
        task_file = tasks_dir / f"{slug}.json"
        try:
            task_file.write_text(_json.dumps(task_record, indent=2), encoding="utf-8")
        except OSError:
            logger.debug("Failed to save task record", exc_info=True)

        lines = [
            "✅ Implementation Plan Created",
            f"  File: {plan_file}",
            f"  Topic: {arg[:100]}",
        ]
        if hasattr(self.session, "agent_comm"):
            comm_stats = self.session.agent_comm.get_token_savings()
            lines.append(
                f"  Agent messages: {comm_stats['total_messages']}"
                f" • Token savings: {comm_stats['context_tokens_saved']:,}"
            )
        lines.append(f"To execute this plan, run: /build {plan_file}")
        return CommandResult(output=lines)

    async def _cmd_build(self, arg: str) -> CommandResult:
        """Execute a saved plan with full agent support."""
        import json as _json
        from pathlib import Path

        if not arg:
            return CommandResult(
                errors=["Usage: /build <plan_file>", "  Example: /build specs/plan_20240101.md"]
            )

        plan_path = Path(arg.strip())
        if not plan_path.is_file():
            return CommandResult(errors=[f"Plan file not found: {plan_path}"])

        try:
            plan_content = plan_path.read_text(encoding="utf-8")
        except OSError as exc:
            return CommandResult(errors=[f"Cannot read plan: {exc}"])

        task_id = plan_path.stem

        # Create sub-context for builder agent
        builder_ctx_id = f"build-{task_id}"
        if hasattr(self.session, "create_sub_context"):
            self.session.create_sub_context(builder_ctx_id)

        # Update task status
        task_file = Path(".ollama/tasks") / f"{task_id}.json"
        if task_file.is_file():
            try:
                task_data = _json.loads(task_file.read_text(encoding="utf-8"))
                task_data["status"] = "in_progress"
                task_file.write_text(_json.dumps(task_data, indent=2), encoding="utf-8")
            except Exception:
                logger.debug("Failed to update task status", exc_info=True)

        # Recall memories
        memory_block = ""
        if hasattr(self.session, "memory_layer"):
            memory_block = self.session.memory_layer.get_context_block(max_tokens=300)

        # Announce via comm bus
        planner_context = ""
        if hasattr(self.session, "agent_comm"):
            self.session.agent_comm.send(
                sender_id="orchestrator",
                recipient_id="builder",
                content=f"Building plan: {task_id} ({len(plan_content)} chars)",
                message_type="task",
            )
            planner_messages = self.session.agent_comm.receive("builder")
            if planner_messages:
                planner_context = "\n\n## Messages from other agents\n"
                for msg in planner_messages[-3:]:
                    planner_context += f"- [{msg.sender}]: {msg.content}\n"

        build_prompt = (
            "You are implementing a plan. Read the plan below carefully and "
            "execute it step by step. Follow the plan's instructions precisely.\n\n"
            f"--- PLAN START ---\n{plan_content}\n--- PLAN END ---\n"
        )
        if memory_block:
            build_prompt += f"\n## Recalled project context\n{memory_block}\n"
        if planner_context:
            build_prompt += planner_context
        build_prompt += "\nImplement this plan now. Report what was completed for each step."

        # Send to model
        try:
            if hasattr(self.session, "send"):
                result = await self.session.send(
                    build_prompt,
                    agent_type="builder",
                    context_id=builder_ctx_id,
                )
            else:
                return CommandResult(
                    errors=["Session does not support send(). Cannot execute build."]
                )
        except Exception as exc:
            return CommandResult(errors=[f"Build failed: {exc}"])

        content = result.get("content", "")

        # Store build result in memory
        if hasattr(self.session, "memory_layer"):
            summary = content[:200] if content else "No output"
            self.session.memory_layer.store(
                key=f"build:{task_id}",
                content=f"Build result: {summary}",
                category="fact",
                importance=4,
            )

        # Notify via comm bus
        if hasattr(self.session, "agent_comm"):
            self.session.agent_comm.send(
                sender_id="builder",
                recipient_id="orchestrator",
                content=f"Build complete: {task_id}",
                message_type="result",
            )

        # Mark task as completed
        if task_file.is_file():
            try:
                task_data = _json.loads(task_file.read_text(encoding="utf-8"))
                task_data["status"] = "completed"
                task_file.write_text(_json.dumps(task_data, indent=2), encoding="utf-8")
            except Exception:
                logger.debug("Failed to update task status", exc_info=True)

        lines = [f"Building from plan: {plan_path}", f"  ({len(plan_content)} chars)"]
        if content:
            if len(content) > 3000:
                lines.append(content[:3000])
                lines.append(f"... ({len(content) - 3000} more characters)")
            else:
                lines.append(content)

        metrics = result.get("metrics", {})
        total = metrics.get("total_tokens", 0)
        cost = metrics.get("cost_estimate", 0.0)
        lines.append(f"  tokens: {total:,} | cost: ${cost:.4f}")

        if hasattr(self.session, "agent_comm"):
            comm_stats = self.session.agent_comm.get_token_savings()
            lines.append(
                f"  agent messages: {comm_stats['total_messages']}"
                f" • token savings: {comm_stats['context_tokens_saved']:,}"
            )

        return CommandResult(output=lines)

    async def _cmd_complete_w_team(self, arg: str) -> CommandResult:
        """Run the team plan-then-build completion loop.

        Launches a multi-phase agentic pipeline (analyse → plan → validate
        → spec → review) and saves the resulting spec to ``.ollama/spec/``.
        Each agent has knowledge of all available slash commands and may
        autonomously invoke them via ``[CMD: /command]`` directives.
        """
        if not arg:
            return CommandResult(
                errors=[
                    "Usage: /complete_w_team <task description>",
                    "  Runs a team loop: analyse → plan → validate → spec → review",
                    "  Output: .ollama/spec/<slug>.md (executable via /build)",
                ]
            )

        try:
            from runner.team_completion import TeamCompletionLoop

            loop = TeamCompletionLoop(self.session, command_processor=self)
            result = await loop.run(arg)

            lines = [
                "🏗️  Team Completion Loop",
                f"  Task: {arg[:100]}{'...' if len(arg) > 100 else ''}",
                "",
                f"📋 Spec ready (run: {result.run_id})",
                f"  File:     {result.spec_path}",
                f"  Phases:   {len(result.phases)}",
                f"  Duration: {result.total_duration:.1f}s",
            ]

            if result.total_commands:
                lines.append(f"  Commands: {result.total_commands} autonomous executions")

            for phase in result.phases:
                cmds_label = f", {len(phase.commands_executed)} cmds" if phase.commands_executed else ""
                lines.append(
                    f"  • {phase.phase_name}: {len(phase.content)} chars, "
                    f"{phase.duration_seconds:.1f}s{cmds_label}"
                )

            if hasattr(self.session, "agent_comm"):
                comm_stats = self.session.agent_comm.get_token_savings()
                lines.append(
                    f"  Agent messages: {comm_stats['total_messages']}"
                    f" • Token savings: {comm_stats['context_tokens_saved']:,}"
                )

            lines.append("")
            lines.append(f"To execute this spec, run: /build {result.spec_path}")
            return CommandResult(output=lines)
        except ImportError:
            return CommandResult(errors=["Team completion module not available."])
        except Exception as exc:
            logger.exception("Team completion failed")
            return CommandResult(errors=[f"Team completion failed: {exc}"])

    def _cmd_resume(self, arg: str) -> CommandResult:
        """List or resume previous tasks."""
        import json as _json
        from pathlib import Path

        tasks_dir = Path(".ollama/tasks")
        if not tasks_dir.is_dir():
            return CommandResult(output=["No previous tasks found."])

        task_files = sorted(
            tasks_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        if not task_files:
            return CommandResult(output=["No previous tasks found."])

        if not arg:
            lines = ["Previous tasks:"]
            for tf in task_files[:20]:
                try:
                    data = _json.loads(tf.read_text(encoding="utf-8"))
                    status = data.get("status", "unknown")
                    task_type = data.get("type", "unknown")
                    desc = data.get("description", "")[:60]
                    task_id = data.get("id", tf.stem)
                    lines.append(f"  {task_id:30s} [{status:10s}] {task_type}: {desc}")
                except Exception:
                    lines.append(f"  {tf.stem}")
            lines.append("")
            lines.append("Use /resume <task-id> to resume a task.")
            return CommandResult(output=lines)

        task_id = arg.strip()
        task_file = tasks_dir / f"{task_id}.json"
        if not task_file.is_file():
            return CommandResult(errors=[f"Task not found: {task_id}"])

        try:
            data = _json.loads(task_file.read_text(encoding="utf-8"))
        except Exception as exc:
            return CommandResult(errors=[f"Cannot read task: {exc}"])

        lines = [
            f"Resuming task: {task_id}",
            f"  Type:   {data.get('type', 'unknown')}",
            f"  Status: {data.get('status', 'unknown')}",
        ]
        plan_file = data.get("plan_file", "")
        if plan_file:
            lines.append(f"  Plan:   {plan_file}")
            lines.append(f"  Run /build {plan_file} to execute this plan.")
        return CommandResult(output=lines)

    # -- project commands ----------------------------------------------------

    def _cmd_init(self, arg: str) -> CommandResult:
        """Initialize the current folder as an ollama-cli project."""
        from pathlib import Path

        project_memory = Path("OLLAMA.md")
        ollama_dir = Path(".ollama")
        created: list[str] = []

        if project_memory.exists():
            pass  # already exists
        else:
            project_name = Path.cwd().name
            template = (
                f"# {project_name}\n\n"
                "## Project Notes\n\n"
                "<!-- Add project-specific context, conventions, and notes below. -->\n"
                "<!-- ollama-cli reads this file to maintain project memory.       -->\n"
            )
            try:
                project_memory.write_text(template, encoding="utf-8")
                created.append("OLLAMA.md")
            except OSError as exc:
                return CommandResult(errors=[f"Cannot create OLLAMA.md: {exc}"])

        if ollama_dir.exists():
            pass  # already exists
        else:
            try:
                ollama_dir.mkdir(parents=True, exist_ok=True)
                created.append(".ollama/")
            except OSError as exc:
                return CommandResult(errors=[f"Cannot create .ollama/: {exc}"])

        # Import instruction files from other AI tools
        imported: list[str] = []
        try:
            known_files = [
                Path("CLAUDE.md"),
                Path("GEMINI.md"),
                Path("AGENT.md"),
                Path(".github/copilot-instructions.md"),
            ]
            if project_memory.exists():
                existing = project_memory.read_text(encoding="utf-8")
                sections: list[str] = []
                for filepath in known_files:
                    if not filepath.is_file():
                        continue
                    marker = f"<!-- imported: {filepath} -->"
                    if marker in existing:
                        continue
                    try:
                        content = filepath.read_text(encoding="utf-8").strip()
                    except OSError:
                        continue
                    if not content:
                        continue
                    sections.append(
                        f"\n{marker}\n## Imported from {filepath}\n\n{content}\n"
                    )
                    imported.append(str(filepath))
                if sections:
                    with open(project_memory, "a", encoding="utf-8") as f:
                        for section in sections:
                            f.write(section)
        except OSError:
            pass

        lines: list[str] = []
        if imported:
            lines.append(f"Imported context from: {', '.join(imported)}")
        if created:
            lines.append(f"Project initialized — created: {', '.join(created)}")
        elif not imported:
            lines.append("Project already initialized. Nothing to do.")
        return CommandResult(output=lines)

    def _cmd_config(self, arg: str) -> CommandResult:
        """View or set configuration values."""
        from api.config import get_config

        cfg = get_config()

        if not arg:
            lines = [
                "--- Configuration ---",
                f"  ollama_host:       {cfg.ollama_host}",
                f"  ollama_model:      {cfg.ollama_model}",
                f"  provider:          {cfg.provider}",
                f"  context_length:    {cfg.context_length}",
                f"  auto_compact:      {cfg.auto_compact}",
                f"  compact_threshold: {cfg.compact_threshold}",
                f"  hooks_enabled:     {cfg.hooks_enabled}",
                "",
                "Use /config <key> <value> to change a setting.",
                "(also available as /settings)",
            ]
            return CommandResult(output=lines)

        parts = arg.split(maxsplit=1)
        key = parts[0]
        value = parts[1] if len(parts) > 1 else ""

        if not hasattr(cfg, key):
            return CommandResult(errors=[f"Unknown config key: {key}"])

        if not value:
            return CommandResult(output=[f"  {key} = {getattr(cfg, key)}"])

        current = getattr(cfg, key)

        # Only allow setting primitive types (str, bool, int, float).
        # None-typed or complex fields (list, dict) must be edited in
        # settings files directly to avoid silent corruption.
        _PRIMITIVE_TYPES = (str, bool, int, float)
        if current is not None and not isinstance(current, _PRIMITIVE_TYPES):
            return CommandResult(
                errors=[
                    f"Config key '{key}' has a complex type ({type(current).__name__}). "
                    "Edit .ollama/settings.json directly to modify it."
                ]
            )
        if current is None:
            return CommandResult(
                errors=[
                    f"Config key '{key}' is unset (None). "
                    "Edit .ollama/settings.json directly to set it."
                ]
            )

        try:
            if isinstance(current, bool):
                coerced: object = value.lower() in ("1", "true", "yes", "on")
            elif isinstance(current, int):
                coerced = int(value)
            elif isinstance(current, float):
                coerced = float(value)
            else:
                coerced = value
            setattr(cfg, key, coerced)

            from api.config import save_config

            save_config(cfg)
            return CommandResult(output=[f"  {key} = {coerced} (saved)"])
        except (ValueError, TypeError) as exc:
            return CommandResult(errors=[f"Invalid value for {key}: {exc}"])

    def _cmd_bug(self, arg: str) -> CommandResult:
        """File a bug report."""
        import json as _json
        from datetime import datetime, timezone
        from pathlib import Path

        description = arg or "No description provided"
        bug_dir = Path(".ollama/bugs")
        bug_dir.mkdir(parents=True, exist_ok=True)

        bug_id = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        bug_file = bug_dir / f"bug_{bug_id}.json"

        report: dict[str, Any] = {
            "id": bug_id,
            "description": description,
            "model": getattr(self.session, "model", "n/a"),
            "provider": getattr(self.session, "provider", "n/a"),
            "session_id": getattr(self.session, "session_id", "n/a"),
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }

        if hasattr(self.session, "get_status"):
            status = self.session.get_status()
            report["messages"] = status.get("messages", 0)
            report["token_metrics"] = status.get("token_metrics", {})
            report["context_usage"] = status.get("context_usage", {})

        try:
            bug_file.write_text(
                _json.dumps(report, indent=2, default=str), encoding="utf-8"
            )
            return CommandResult(output=[f"Bug report saved: {bug_file}"])
        except OSError as exc:
            return CommandResult(errors=[f"Failed to save bug report: {exc}"])

    def _cmd_update_status_line(self, arg: str) -> CommandResult:
        """Update session status line metadata in the session file."""
        import json as _json
        from pathlib import Path

        if not arg:
            return CommandResult(
                errors=[
                    "Usage: /update_status_line <key> <value>",
                    "  Example: /update_status_line project myapp",
                ]
            )

        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            return CommandResult(errors=["Both key and value are required."])

        key, value = parts[0], parts[1]

        session_dir = Path(".ollama/sessions")
        session_id = getattr(self.session, "session_id", None)
        if not session_id:
            return CommandResult(
                output=[f"Status line updated: {key} = {value}"],
                data={"action": "update_status_line", "key": key, "value": value},
            )

        session_file = session_dir / f"{session_id}.json"
        if not session_file.is_file():
            return CommandResult(
                output=[f"Status line updated: {key} = {value}"],
                data={"action": "update_status_line", "key": key, "value": value},
            )

        try:
            data: Any = _json.loads(session_file.read_text(encoding="utf-8"))
        except Exception as exc:
            return CommandResult(
                errors=[f"Failed to read session file: {exc}"]
            )

        if not isinstance(data, dict):
            return CommandResult(
                errors=["Session file is malformed (expected JSON object)."]
            )

        extras = data.get("extras") or {}
        if not isinstance(extras, dict):
            extras = {}
        old_value = extras.get(key)
        extras[key] = value
        data["extras"] = extras

        try:
            session_file.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        except OSError as exc:
            return CommandResult(errors=[f"Failed to update session file: {exc}"])

        lines = [f"Status line updated: {key} = {value}"]
        if old_value is not None:
            lines.append(f"  Previous value: {old_value}")
        return CommandResult(output=lines)

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
