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
        return CommandResult(
            output=[f"Loading session '{arg}'..."],
            data={"action": "load_session", "name": arg},
        )

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

    def _cmd_compact(self, arg: str) -> CommandResult:
        """Force context compaction."""
        if hasattr(self.session, "context_manager"):
            cm = self.session.context_manager
            if hasattr(cm, "compact"):
                cm.compact()
                return CommandResult(
                    output=["Context compacted."]
                )
        return CommandResult(output=["Context compaction not available."])

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
        """Invoke a tool by name."""
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

            fn = entry.get("function")
            if fn is None:
                return CommandResult(errors=[f"Tool '{tool_name}' has no callable function."])

            result = fn(tool_arg)
            output_text = str(result) if result is not None else "(no output)"
            return CommandResult(output=[output_text])
        except ImportError:
            return CommandResult(errors=["Tools module not available."])

    def _cmd_pull(self, arg: str) -> CommandResult:
        """Pull/download a model."""
        if not arg:
            return CommandResult(
                errors=["Usage: /pull <model_name>", "  Example: /pull llama3.2"]
            )
        return CommandResult(
            output=[f"Pulling model: {arg}..."],
            data={"action": "pull_model", "model": arg},
        )

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
        """Manage MCP servers."""
        try:
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
                        status = "● enabled" if enabled else "○ disabled"
                        lines.append(f"  {status}  {name}")
                return CommandResult(output=lines)

            return CommandResult(
                output=["MCP subcommands: /mcp, /mcp enable <name>, /mcp disable <name>"]
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

    def _cmd_chain(self, arg: str) -> CommandResult:
        """Start multi-wave chain orchestration."""
        if not arg:
            return CommandResult(
                errors=["Usage: /chain <prompt>", "  Runs a multi-wave agent chain on the given prompt."]
            )
        return CommandResult(
            output=["Starting chain orchestration..."],
            data={"action": "chain", "prompt": arg},
        )

    def _cmd_team_planning(self, arg: str) -> CommandResult:
        """Generate an implementation plan."""
        if not arg:
            return CommandResult(
                errors=[
                    "Usage: /team_planning <description>",
                    "  (also available as /plan)",
                    "  Generates an engineering plan and saves it to specs/.",
                ]
            )
        return CommandResult(
            output=[f"Generating plan for: {arg}..."],
            data={"action": "team_planning", "description": arg},
        )

    def _cmd_build(self, arg: str) -> CommandResult:
        """Execute a saved plan."""
        if not arg:
            return CommandResult(
                errors=["Usage: /build <plan_file>", "  Example: /build specs/plan_20240101.md"]
            )
        return CommandResult(
            output=[f"Executing plan: {arg}..."],
            data={"action": "build", "plan_file": arg},
        )

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

        if created:
            return CommandResult(
                output=[f"Project initialized — created: {', '.join(created)}"]
            )
        return CommandResult(output=["Project already initialized. Nothing to do."])

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
        """Update session status line metadata."""
        if not arg:
            return CommandResult(
                errors=["Usage: /update_status_line <key> <value>"]
            )

        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            return CommandResult(errors=["Both key and value are required."])

        key, value = parts[0], parts[1]
        return CommandResult(
            output=[f"Status line updated: {key} = {value}"],
            data={"action": "update_status_line", "key": key, "value": value},
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
