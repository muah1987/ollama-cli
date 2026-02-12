#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
#     "rich",
# ]
# ///
"""Interactive REPL mode -- GOTCHA Tools layer, ATLAS Assemble phase.

Readline-based REPL with slash commands and streaming output.
"""

from __future__ import annotations

import asyncio
import logging
import readline
import sys
import threading
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ensure sibling modules are importable when run as a script
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from model.session import Session  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_HISTORY_DIR = Path(".ollama")
_HISTORY_FILE = _HISTORY_DIR / "history"
_VALID_PROVIDERS = ("ollama", "claude", "gemini", "codex")
_BUG_CONTEXT_MESSAGES = 5  # number of recent messages to include in bug reports

# ---------------------------------------------------------------------------
# ANSI escape helpers
# ---------------------------------------------------------------------------

_RESET = "\033[0m"


def _green(text: str) -> str:
    """Wrap *text* in green ANSI escape codes."""
    return f"\033[32m{text}{_RESET}"


def _dim(text: str) -> str:
    """Wrap *text* in dim/gray ANSI escape codes."""
    return f"\033[2m{text}{_RESET}"


def _red(text: str) -> str:
    """Wrap *text* in red ANSI escape codes."""
    return f"\033[31m{text}{_RESET}"


def _cyan(text: str) -> str:
    """Wrap *text* in cyan ANSI escape codes."""
    return f"\033[36m{text}{_RESET}"


def _bold(text: str) -> str:
    """Wrap *text* in bold ANSI escape codes."""
    return f"\033[1m{text}{_RESET}"


def _yellow(text: str) -> str:
    """Wrap *text* in yellow ANSI escape codes."""
    return f"\033[33m{text}{_RESET}"


def _magenta(text: str) -> str:
    """Wrap *text* in magenta ANSI escape codes."""
    return f"\033[35m{text}{_RESET}"


def _blue(text: str) -> str:
    """Wrap *text* in blue ANSI escape codes."""
    return f"\033[34m{text}{_RESET}"


def _white(text: str) -> str:
    """Wrap *text* in bright white ANSI escape codes."""
    return f"\033[97m{text}{_RESET}"


# ---------------------------------------------------------------------------
# Agent color scheme – each agent type gets a unique color
# ---------------------------------------------------------------------------

_AGENT_COLORS: dict[str, str] = {
    "code": "\033[36m",       # cyan
    "review": "\033[35m",     # magenta
    "test": "\033[33m",       # yellow
    "plan": "\033[34m",       # blue
    "docs": "\033[32m",       # green
    "debug": "\033[31m",      # red
    "default": "\033[37m",    # white
    "orchestrator": "\033[95m",  # bright magenta
    "builder": "\033[96m",    # bright cyan
    "validator": "\033[93m",  # bright yellow
}


def _agent_color(agent_type: str, text: str) -> str:
    """Colorize text for a specific agent type."""
    color = _AGENT_COLORS.get(agent_type, _AGENT_COLORS["default"])
    return f"{color}{text}{_RESET}"


# ---------------------------------------------------------------------------
# Llama ASCII art – based on the Ollama brand llama
# ---------------------------------------------------------------------------

_LLAMA_BANNER = r"""
       ##########                             ##########
      #############                         #############
     ######  ######                         ######  ######
    ######    ######                       ######    ######
    #####      ###### ################### ######      #####
    #####       ###############################       #####
    ######      ######                 ######      ######
    ################                     ################
   ###############                       ###############
  ########                                       ########
 ######                                             ######
 #####          ###         ############         ###          #####
 #####         #####    ##################    #####         #####
 #####        ######  ######          ###### ######        #####
  #####        ####  ####                ####  ####        #####
   ######           ####     ##  ###      ####           ######
    ######          ####     ######       ####          ######
      ######        ####      ###        ####        ######
       ######        ####               ####        ######
        ######         #####         #####         ######
         ######           ################           ######
          #####              ############              #####
          #####                                        #####
          #####                                        #####
"""

# Funny llama-themed spinner frames for "thinking" animation
_LLAMA_SPINNER_FRAMES = [
    "🦙 Thinking...",
    "🦙 Chewing on that...",
    "🦙 Ruminating...",
    "🦙 Spitting ideas...",
    "🦙 Grazing for answers...",
    "🦙 Trotting through context...",
    "🦙 Llama-nating...",
    "🦙 Herding tokens...",
]

_LLAMA_PLAN_SPINNER = [
    "🦙📋 Assembling the herd...",
    "🦙📋 Planning the trail...",
    "🦙📋 Mapping the pasture...",
    "🦙📋 Organizing the caravan...",
]

_LLAMA_BUILD_SPINNER = [
    "🦙🔨 Building the barn...",
    "🦙🔨 Hammering away...",
    "🦙🔨 Laying foundation...",
    "🦙🔨 Constructing...",
]


# ---------------------------------------------------------------------------
# Llama spinner – funny animated waiting indicator
# ---------------------------------------------------------------------------


class _LlamaSpinner:
    """Threaded spinner that cycles through funny llama-themed messages.

    Usage::

        spinner = _LlamaSpinner(_LLAMA_SPINNER_FRAMES)
        spinner.start()
        try:
            await some_long_operation()
        finally:
            spinner.stop()
    """

    _JOIN_TIMEOUT: float = 2.0  # seconds to wait for spinner thread to stop
    _DEFAULT_INTERVAL: float = 0.8  # seconds between frame changes

    def __init__(self, frames: list[str], interval: float = 0.8) -> None:
        self._frames = frames
        self._interval = interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the spinner in a background thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the spinner and clear the line."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._JOIN_TIMEOUT)
        # Clear the spinner line
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

    def _run(self) -> None:
        """Cycle through frames until stopped."""
        idx = 0
        while not self._stop_event.is_set():
            frame = self._frames[idx % len(self._frames)]
            sys.stdout.write(f"\r\033[2m{frame}\033[0m")
            sys.stdout.flush()
            idx += 1
            self._stop_event.wait(self._interval)

    def __enter__(self) -> "_LlamaSpinner":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()


# ---------------------------------------------------------------------------
# InteractiveMode
# ---------------------------------------------------------------------------


class InteractiveMode:
    """Readline-based interactive REPL with slash commands and streaming output.

    Provides a conversational interface to an active :class:`Session`, with
    command history persistence, slash-command processing, and ANSI-formatted
    output.

    Parameters
    ----------
    session:
        An initialised :class:`Session` instance that handles model
        communication, context management, and token tracking.
    """

    # Maps slash commands to their handler method names
    _COMMAND_TABLE: dict[str, str] = {
        "/model": "_cmd_model",
        "/provider": "_cmd_provider",
        "/compact": "_cmd_compact",
        "/status": "_cmd_status",
        "/clear": "_cmd_clear",
        "/save": "_cmd_save",
        "/load": "_cmd_load",
        "/history": "_cmd_history",
        "/memory": "_cmd_memory",
        "/tools": "_cmd_tools",
        "/tool": "_cmd_tool",
        "/diff": "_cmd_diff",
        "/config": "_cmd_config",
        "/bug": "_cmd_bug",
        "/team_planning": "_cmd_team_planning",
        "/build": "_cmd_build",
        "/resume": "_cmd_resume",
        "/update_status_line": "_cmd_update_status_line",
        "/help": "_cmd_help",
        "/quit": "_cmd_quit",
        "/exit": "_cmd_quit",
        "/set-agent-model": "_cmd_set_agent_model",
        "/list-agent-models": "_cmd_list_agent_models",
        "/agents": "_cmd_agents",
        "/remember": "_cmd_remember",
        "/recall": "_cmd_recall",
    }

    def __init__(self, session: Session) -> None:
        self.session = session
        self._running: bool = False
        self._setup_readline()

    # -- readline setup ------------------------------------------------------

    def _setup_readline(self) -> None:
        """Configure readline with history file and tab completion."""
        _HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        try:
            readline.read_history_file(str(_HISTORY_FILE))
        except FileNotFoundError:
            pass
        except OSError:
            logger.warning("Could not read history file %s", _HISTORY_FILE, exc_info=True)

        readline.set_history_length(1000)

        # Basic completer for slash commands
        commands = list(self._COMMAND_TABLE.keys())

        def completer(text: str, state: int) -> str | None:
            matches = [c for c in commands if c.startswith(text)]
            return matches[state] if state < len(matches) else None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")

    def _save_history(self) -> None:
        """Persist readline history to disk."""
        try:
            readline.write_history_file(str(_HISTORY_FILE))
        except OSError:
            logger.warning("Could not write history file %s", _HISTORY_FILE, exc_info=True)

    # -- output helpers ------------------------------------------------------

    @staticmethod
    def _print_system(text: str) -> None:
        """Print a system-level message in dim gray."""
        print(_dim(text))

    @staticmethod
    def _print_error(text: str) -> None:
        """Print an error message in red."""
        print(_red(text))

    @staticmethod
    def _print_info(text: str) -> None:
        """Print informational text in cyan."""
        print(_cyan(text))

    def _print_response(self, text: str, agent_type: str | None = None) -> None:
        """Print an assistant response with a colored model-name prefix.

        Parameters
        ----------
        text:
            The response text to display.
        agent_type:
            Optional agent type for color-coded output.
        """
        if agent_type:
            prefix = _agent_color(agent_type, f"[{agent_type}:{self.session.model}] ")
        else:
            prefix = _green(f"[{self.session.model}] ")
        print(f"{prefix}{text}")

    # -- llama spinner -------------------------------------------------------

    @staticmethod
    def _spinner(frames: list[str], interval: float = 0.8) -> "_LlamaSpinner":
        """Return a llama-themed spinner context manager.

        Usage::

            with self._spinner(_LLAMA_SPINNER_FRAMES):
                await some_long_operation()
        """
        return _LlamaSpinner(frames, interval)

    def _print_banner(self) -> None:
        """Print the welcome banner on REPL startup.

        Uses the Ollama llama face branding with status info in a clean layout.
        """
        from cmd.root import VERSION

        status = self.session.get_status()
        msg_count = status["messages"]
        ctx = status["context_usage"]
        compact_pct = int(self.session.context_manager.compact_threshold * 100)
        compact_status = _green("on") if self.session.context_manager.auto_compact else _red("off")
        state = "resumed" if msg_count > 0 else "new session"

        # Print llama face ASCII art in dim white
        print()
        for line in _LLAMA_BANNER.strip().splitlines():
            print(_dim(line))

        # Title line
        print()
        print(_bold(f"  ollama-cli v{VERSION}") + _dim(f"  ({state})"))
        print()

        # Status block in a box
        w = 58
        print(f"  ┌{'─' * w}┐")
        print(f"  │{'':>{w}}│")
        self._banner_line(w, "Model", self.session.model)
        self._banner_line(w, "Provider", self.session.provider)
        sid = self.session.session_id
        sid_display = (sid[:24] + "…") if len(sid) > 25 else sid
        self._banner_line(w, "Session", sid_display)
        self._banner_line(w, "Context", f"{ctx['used']:,}/{ctx['max']:,} tokens ({ctx['percentage']}%)")
        self._banner_line(w, "Compact", f"auto-compact {compact_status} (threshold {compact_pct}%)")
        if msg_count > 0:
            self._banner_line(w, "History", f"{msg_count} messages")
        mem_stats = self.session.memory_layer.get_token_savings()
        if mem_stats["total_entries"] > 0:
            self._banner_line(w, "Memory", f"{mem_stats['total_entries']} entries ({mem_stats['context_tokens_used']:,} tokens)")
        print(f"  │{'':>{w}}│")
        print(f"  └{'─' * w}┘")

        # Tips footer
        print()
        print(_dim("  💡 /help for commands • /tools for built-in tools"))
        print(_dim("  🦙 /compact to free memory • /agents to see the herd"))
        print(_dim("  ⌨  Ctrl+C to cancel • Ctrl+D or /quit to exit"))
        print()

    @staticmethod
    def _banner_line(width: int, label: str, value: str) -> None:
        """Print a single line inside the banner box."""
        content = f"  {_cyan(f'{label}:')}  {value}"
        # We need to account for ANSI escape codes in the padding
        visible_len = len(f"  {label}:  {value}")
        padding = width - visible_len
        if padding < 0:
            padding = 0
        print(f"  │{content}{' ' * padding}│")

    # -- input reading -------------------------------------------------------

    @staticmethod
    def _read_input() -> str | None:
        """Read user input, supporting multi-line entry.

        A single line is returned immediately.  If the first line ends with
        ``\\``, additional lines are collected until a blank line or EOF.

        Returns
        -------
        The collected input string, or ``None`` on EOF (Ctrl+D on empty).
        """
        try:
            first_line = input(">>> ")
        except EOFError:
            return None

        # Single-line fast path
        if not first_line.endswith("\\"):
            return first_line

        # Multi-line mode: collect until blank line or EOF
        lines = [first_line.rstrip("\\")]
        try:
            while True:
                continuation = input("... ")
                if continuation == "":
                    break
                if continuation.endswith("\\"):
                    lines.append(continuation.rstrip("\\"))
                else:
                    lines.append(continuation)
                    break
        except EOFError:
            pass

        return "\n".join(lines)

    # -- slash command dispatch -----------------------------------------------

    async def _dispatch_command(self, line: str) -> bool:
        """Parse and dispatch a slash command.

        Parameters
        ----------
        line:
            The raw input line starting with ``/``.

        Returns
        -------
        ``True`` if the REPL should exit, ``False`` to continue.
        """
        parts = line.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        handler_name = self._COMMAND_TABLE.get(cmd)
        if handler_name is None:
            self._print_error(f"Unknown command: {cmd}")
            self._print_system("Type /help to see available commands.")
            return False

        handler = getattr(self, handler_name)
        result = handler(arg)

        # Some handlers are coroutines
        if asyncio.iscoroutine(result):
            result = await result

        return bool(result)

    # -- slash command handlers -----------------------------------------------

    def _cmd_model(self, arg: str) -> bool:
        """Switch the active model.

        Parameters
        ----------
        arg:
            The model name to switch to.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        if not arg:
            self._print_error("Usage: /model <name>")
            self._print_system(f"  Current model: {self.session.model}")
            return False

        old_model = self.session.model
        self.session.model = arg
        self._print_info(f"Model switched: {old_model} -> {arg}")
        return False

    def _cmd_provider(self, arg: str) -> bool:
        """Switch the active provider.

        Parameters
        ----------
        arg:
            The provider name (ollama, claude, gemini, codex).

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        if not arg:
            self._print_error("Usage: /provider <name>")
            self._print_system(f"  Current provider: {self.session.provider}")
            self._print_system(f"  Available: {', '.join(_VALID_PROVIDERS)}")
            return False

        name = arg.lower()
        if name not in _VALID_PROVIDERS:
            self._print_error(f"Unknown provider: {arg}")
            self._print_system(f"  Available: {', '.join(_VALID_PROVIDERS)}")
            return False

        old_provider = self.session.provider
        self.session.provider = name
        self.session.token_counter.provider = name
        self._print_info(f"Provider switched: {old_provider} -> {name}")
        return False

    async def _cmd_compact(self, _arg: str) -> bool:
        """Force context compaction and display before/after stats.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        cm = self.session.context_manager
        usage_before = cm.get_context_usage()

        print()
        self._print_info("Context Compaction")
        self._print_system(
            f"  Before: {usage_before['used']:,} / {usage_before['max']:,} tokens "
            f"({usage_before['percentage']}%) — {len(cm.messages)} messages"
        )
        compact_label = "on" if cm.auto_compact else "off"
        self._print_system(
            f"  Auto-compact: {compact_label} | threshold: {int(cm.compact_threshold * 100)}% "
            f"| keep last: {cm.keep_last_n} messages"
        )

        if len(cm.messages) <= cm.keep_last_n:
            self._print_system("  Nothing to compact (message count ≤ keep_last_n).")
            print()
            return False

        try:
            result = await self.session.compact()
        except Exception as exc:
            self._print_error(f"  Compaction failed: {exc}")
            return False

        usage_after = cm.get_context_usage()
        removed = result.get("messages_removed", 0)
        saved = result.get("before_tokens", 0) - result.get("after_tokens", 0)

        self._print_info(
            f"  After:  {usage_after['used']:,} / {usage_after['max']:,} tokens "
            f"({usage_after['percentage']}%) — {len(cm.messages)} messages"
        )
        self._print_info(f"  Removed {removed} messages, freed ~{saved:,} tokens")
        print()
        return False

    def _cmd_status(self, _arg: str) -> bool:
        """Display current session status.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        status = self.session.get_status()
        token_info: dict[str, Any] = status["token_metrics"]
        context_info: dict[str, Any] = status["context_usage"]
        cm = self.session.context_manager

        print()
        self._print_info("Session")
        self._print_info(f"  ID:         {status['session_id']}")
        self._print_info(f"  Model:      {status['model']}")
        self._print_info(f"  Provider:   {status['provider']}")
        self._print_info(f"  Uptime:     {status['uptime_str']}")
        self._print_info(f"  Messages:   {status['messages']}")
        self._print_info(f"  Hooks:      {'enabled' if status['hooks_enabled'] else 'disabled'}")

        self._print_info("Tokens")
        self._print_info(f"  Prompt:     {token_info.get('prompt_tokens', 0):,}")
        self._print_info(f"  Completion: {token_info.get('completion_tokens', 0):,}")
        self._print_info(f"  Total:      {token_info.get('total_tokens', 0):,}")
        self._print_info(f"  Speed:      {token_info.get('tokens_per_second', 0):.1f} tok/s")
        self._print_info(f"  Cost:       ${token_info.get('cost_estimate', 0):.4f}")

        self._print_info("Context")
        self._print_info(f"  Used:       {context_info.get('used', 0):,} / {context_info.get('max', 0):,} tokens")
        self._print_info(f"  Usage:      {context_info.get('percentage', 0)}%")
        self._print_info(f"  Remaining:  {context_info.get('remaining', 0):,}")

        compact_label = _green("on") if cm.auto_compact else _red("off")
        self._print_info(
            f"  Auto-compact: {compact_label} (threshold {int(cm.compact_threshold * 100)}%, keep last {cm.keep_last_n})"
        )
        if cm.should_compact():
            self._print_info("  ⚠ Context above threshold — run /compact to free space")

        # Agent Communication
        comm_stats = self.session.agent_comm.get_token_savings()
        self._print_info("Agent Communication")
        self._print_info(f"  Messages:     {comm_stats['total_messages']}")
        self._print_info(f"  Token savings: ~{comm_stats['context_tokens_saved']:,}")

        # Memory Layer
        mem_stats = self.session.memory_layer.get_token_savings()
        self._print_info("Memory")
        self._print_info(f"  Entries:      {mem_stats['total_entries']}")
        self._print_info(f"  Raw tokens:   {mem_stats['total_raw_tokens']:,}")
        self._print_info(f"  Context used: {mem_stats['context_tokens_used']:,}")
        self._print_info(f"  Saved:        ~{mem_stats['tokens_saved']:,}")
        print()

        return False

    def _cmd_clear(self, _arg: str) -> bool:
        """Clear the conversation history.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        self.session.context_manager.clear()
        self.session._message_count = 0
        self._print_info("Conversation history cleared.")
        return False

    def _cmd_save(self, arg: str) -> bool:
        """Save the session to a file.

        Parameters
        ----------
        arg:
            Optional session name.  When empty the session ID is used.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        if arg:
            save_path = str(Path(".ollama/sessions") / f"{arg}.json")
        else:
            save_path = None  # Session.save() uses default path

        path = self.session.save(save_path)
        self._print_info(f"Session saved to: {path}")
        return False

    def _cmd_load(self, arg: str) -> bool:
        """Load a session from a file.

        Parameters
        ----------
        arg:
            The session name or ID to load.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        if not arg:
            self._print_error("Usage: /load <name>")
            return False

        try:
            loaded = Session.load(arg)
        except FileNotFoundError as exc:
            self._print_error(str(exc))
            return False

        # Replace the current session state with the loaded one
        self.session.session_id = loaded.session_id
        self.session.model = loaded.model
        self.session.provider = loaded.provider
        self.session.context_manager = loaded.context_manager
        self.session.token_counter = loaded.token_counter
        self.session.hooks_enabled = loaded.hooks_enabled
        self.session.start_time = loaded.start_time
        self.session._end_time = loaded._end_time
        self.session._message_count = loaded._message_count

        self._print_info(
            f"Session loaded: {loaded.session_id} ({loaded._message_count} messages, model={loaded.model})"
        )
        return False

    def _cmd_history(self, _arg: str) -> bool:
        """Display the conversation history with role prefixes.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        messages = self.session.context_manager.messages
        if not messages:
            self._print_system("No conversation history.")
            return False

        print()
        for i, msg in enumerate(messages, start=1):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if role == "user":
                prefix = _bold(f"[{i}] user:")
            elif role == "assistant":
                prefix = _green(f"[{i}] {self.session.model}:")
            elif role == "system":
                prefix = _dim(f"[{i}] system:")
            else:
                prefix = _dim(f"[{i}] {role}:")

            # Truncate long messages in history view
            display = content if len(content) <= 200 else content[:200] + "..."
            print(f"{prefix} {display}")
        print()

        return False

    def _cmd_help(self, _arg: str) -> bool:
        """Display all available slash commands.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        print()
        self._print_info("Available commands:")
        print(f"  {_cyan('/model <name>')}     Switch active model")
        print(f"  {_cyan('/provider <name>')}  Switch provider (ollama|claude|gemini|codex)")
        print(f"  {_cyan('/compact')}          Force context compaction")
        print(f"  {_cyan('/status')}           Show session status (tokens, context, uptime)")
        print(f"  {_cyan('/clear')}            Clear conversation history")
        print(f"  {_cyan('/save [name]')}      Save session to file")
        print(f"  {_cyan('/load <name>')}      Load session from file")
        print(f"  {_cyan('/history')}          Show conversation history")
        print(f"  {_cyan('/memory [note]')}    View or add to project memory (OLLAMA.md)")
        print(f"  {_cyan('/tools')}            List available built-in tools")
        print(f"  {_cyan('/tool <name> ...')}  Invoke a tool (file_read, shell_exec, ...)")
        print(f"  {_cyan('/diff')}             Show git diff of working directory")
        print(f"  {_cyan('/config [k] [v]')}   View or set configuration")
        print(f"  {_cyan('/bug [desc]')}       File a bug report about the session")
        print(f"  {_cyan('/team_planning ...')} Generate an implementation plan to specs/")
        print(f"  {_cyan('/build <plan>')}     Execute a saved plan file")
        print(f"  {_cyan('/resume [id]')}      List or resume previous tasks")
        print(f"  {_cyan('/update_status_line <k> <v>')}  Update session status metadata")
        print(f"  {_cyan('/set-agent-model <type:provider:model>}')}  Assign model to agent type")
        print(f"  {_cyan('/list-agent-models')} List agent model assignments")
        print(f"  {_cyan('/agents')}           List active agents and communication stats")
        print(f"  {_cyan('/remember <k> <v>')} Store a memory entry for token-efficient recall")
        print(f"  {_cyan('/recall [query]')}   Recall stored memories (all or by keyword)")
        print(f"  {_cyan('/help')}             Show this help message")
        print(f"  {_cyan('/quit')}             Exit the session")
        print()
        self._print_system("Multi-line input: end a line with \\ to continue on the next line.")
        self._print_system("Press Ctrl+C to cancel input, Ctrl+D to exit.")
        print()

        return False

    def _cmd_set_agent_model(self, arg: str) -> bool:
        """Set a specific model for an agent type.

        Parameters
        ----------
        arg:
            Agent type and model specification (format: type:provider:model)

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        if not arg:
            self._print_error("Usage: /set-agent-model <type:provider:model>")
            self._print_system("  Example: /set-agent-model code:hf:mistralai/Mistral-7B-Instruct-v0.3")
            return False

        parts = arg.split(":")
        if len(parts) != 3:
            self._print_error("Invalid format. Use: type:provider:model")
            return False

        agent_type, provider, model = parts
        self.session.provider_router.set_agent_model(agent_type, provider, model)
        self._print_info(f"Agent '{agent_type}' assigned to {provider}:{model}")
        return False

    def _cmd_list_agent_models(self, _arg: str) -> bool:
        """List all configured agent model assignments.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        from api.provider_router import _AGENT_MODEL_MAP

        if not _AGENT_MODEL_MAP:
            self._print_system("No agent model assignments configured.")
        else:
            self._print_info("Agent Model Assignments:")
            for agent_type, (provider, model) in _AGENT_MODEL_MAP.items():
                self._print_system(f"  {agent_type}: {provider}:{model}")
        return False

    # -- new commands (Gemini CLI / Claude Code / Codex parity) ----------------

    def _cmd_agents(self, _arg: str) -> bool:
        """List all active sub-agents with color-coded types and communication stats.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        sub_contexts = self.session.context_manager._sub_contexts
        if sub_contexts:
            print()
            self._print_info("🦙 Active Sub-Agents (the herd):")
            for cid, sub in sub_contexts.items():
                usage = sub.get_context_usage()
                # Color-code each agent by type
                agent_type = cid.split("-")[0] if "-" in cid else cid
                colored_name = _agent_color(agent_type, cid)
                dot = _agent_color(agent_type, "●")
                print(f"  {dot} {colored_name}: {usage['used']:,}/{usage['max']:,} tokens ({usage['percentage']}%)")
        else:
            self._print_system("🦙 No active sub-agents. The herd is resting.")

        print()
        comm_stats = self.session.agent_comm.get_token_savings()
        self._print_info("📡 Agent Communication:")
        self._print_info(f"  Messages:     {comm_stats['total_messages']}")
        self._print_info(f"  Direct tokens: {comm_stats['direct_tokens']:,}")
        self._print_info(f"  Tokens saved:  ~{comm_stats['context_tokens_saved']:,}")

        # Show color legend
        print()
        self._print_system("  Agent colors: " + " ".join(
            _agent_color(t, f"●{t}") for t in ["code", "review", "test", "plan", "docs", "debug"]
        ))
        print()
        return False

    def _cmd_remember(self, arg: str) -> bool:
        """Store a memory entry for token-efficient recall.

        Usage: ``/remember <key> <content>``

        Parameters
        ----------
        arg:
            Key and content separated by a space.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        if not arg or " " not in arg:
            self._print_error("Usage: /remember <key> <content>")
            return False

        key, content = arg.split(" ", 1)
        self.session.memory_layer.store(key, content)
        self._print_info(f"Remembered '{key}': {content}")
        return False

    def _cmd_recall(self, arg: str) -> bool:
        """Recall stored memories (all or by keyword).

        Usage: ``/recall`` to show all, ``/recall <query>`` to search.

        Parameters
        ----------
        arg:
            Optional search query.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        if not arg:
            # Show all memories
            stats = self.session.memory_layer.get_token_savings()
            if stats["total_entries"] == 0:
                self._print_system("No memories stored. Use /remember <key> <content> to add.")
                return False
            self._print_info(f"Stored Memories ({stats['total_entries']} entries):")
            for entry in self.session.memory_layer.get_all_entries():
                self._print_info(f"  [{entry.category}] {entry.key}: {entry.content}")
            return False

        # Search by keyword
        results = self.session.memory_layer.recall_relevant(arg)
        if not results:
            self._print_system(f"No memories matching '{arg}'.")
        else:
            self._print_info(f"Memories matching '{arg}':")
            for entry in results:
                self._print_info(f"  [{entry.category}] {entry.key}: {entry.content}")
        return False

    def _cmd_memory(self, arg: str) -> bool:
        """Read or append to OLLAMA.md project memory file.

        Usage: ``/memory`` to view, ``/memory <note>`` to append a note.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        memory_file = Path("OLLAMA.md")

        if not arg:
            # Display current memory
            if memory_file.is_file():
                try:
                    content = memory_file.read_text(encoding="utf-8")
                    self._print_info("--- Project Memory (OLLAMA.md) ---")
                    print(content[:2000])
                    if len(content) > 2000:
                        print("...")
                except OSError as exc:
                    self._print_error(f"Cannot read OLLAMA.md: {exc}")
            else:
                self._print_system("No OLLAMA.md found. Use /memory <note> to create one.")
            return False

        # Append a note
        try:
            with open(memory_file, "a", encoding="utf-8") as f:
                f.write(f"\n- {arg}\n")
            self._print_info(f"Added to OLLAMA.md: {arg}")
        except OSError as exc:
            self._print_error(f"Cannot write to OLLAMA.md: {exc}")
        return False

    def _cmd_tools(self, _arg: str) -> bool:
        """List all available built-in tools.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        from skills.tools import list_tools

        tools = list_tools()
        print()
        self._print_info("Available tools:")
        for t in tools:
            risk_color = {"low": _green, "medium": _cyan, "high": _red}.get(t["risk"], _dim)
            print(f"  {_cyan(t['name']):30s} {t['description']:35s} [{risk_color(t['risk'])}]")
        print()
        self._print_system("Use /tool <name> [args...] to invoke a tool.")
        print()
        return False

    def _cmd_tool(self, arg: str) -> bool:
        """Invoke a built-in tool by name.

        Usage: ``/tool file_read path/to/file``

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        import json as _json

        from server.hook_runner import HookRunner
        from skills.tools import get_tool

        if not arg:
            self._print_error("Usage: /tool <name> [args...]")
            self._print_system("  Example: /tool file_read README.md")
            return False

        parts = arg.split(maxsplit=1)
        tool_name = parts[0]
        tool_arg = parts[1] if len(parts) > 1 else ""

        entry = get_tool(tool_name)
        if entry is None:
            self._print_error(f"Unknown tool: {tool_name}")
            return False

        # Check allowed-tools filter
        from api.config import get_config

        cfg = get_config()
        allowed = getattr(cfg, "allowed_tools", None)
        if allowed and tool_name not in allowed:
            self._print_error(f"Tool '{tool_name}' is not in --allowed-tools list.")
            return False

        # Run PreToolUse hook for approval
        hook_payload = {"tool_name": tool_name, "arguments": tool_arg, "risk": entry["risk"]}
        try:
            runner = HookRunner()
            if runner.is_enabled():
                results = runner.run_hook("PreToolUse", hook_payload, timeout=10)
                for r in results:
                    decision = r.permission_decision
                    if decision == "deny":
                        self._print_error(f"Tool '{tool_name}' blocked by PreToolUse hook.")
                        return False
                    if decision == "ask":
                        try:
                            answer = input(f"Allow tool '{tool_name}'? [y/N] ").strip().lower()
                        except (EOFError, KeyboardInterrupt):
                            answer = "n"
                        if answer != "y":
                            self._print_system("Tool execution cancelled.")
                            return False
        except Exception:
            logger.debug("PreToolUse hook check failed, proceeding", exc_info=True)

        # Execute the tool
        func = entry["function"]
        try:
            if tool_name == "file_read":
                result = func(tool_arg)
            elif tool_name == "file_write":
                # /tool file_write path content...
                write_parts = tool_arg.split(maxsplit=1)
                if len(write_parts) < 2:
                    self._print_error("Usage: /tool file_write <path> <content>")
                    return False
                result = func(write_parts[0], write_parts[1])
            elif tool_name == "file_edit":
                # /tool file_edit path|||old_text|||new_text
                edit_parts = tool_arg.split("|||")
                if len(edit_parts) != 3:
                    self._print_error("Usage: /tool file_edit <path>|||<old_text>|||<new_text>")
                    return False
                result = func(edit_parts[0].strip(), edit_parts[1], edit_parts[2])
            elif tool_name == "grep_search":
                search_parts = tool_arg.split(maxsplit=1)
                pattern = search_parts[0] if search_parts else ""
                path = search_parts[1] if len(search_parts) > 1 else "."
                result = func(pattern, path)
            elif tool_name == "shell_exec":
                result = func(tool_arg)
            elif tool_name == "web_fetch":
                result = func(tool_arg)
            else:
                result = {"error": f"No invocation handler for tool: {tool_name}"}
        except Exception as exc:
            result = {"error": str(exc)}

        # Run PostToolUse hook
        try:
            runner = HookRunner()
            if runner.is_enabled():
                post_payload = {"tool_name": tool_name, "result": str(result)[:500]}
                runner.run_hook("PostToolUse", post_payload, timeout=10)
        except Exception:
            logger.debug("PostToolUse hook failed", exc_info=True)

        # Display result
        if "error" in result:
            self._print_error(f"Error: {result['error']}")
        else:
            self._print_info(f"[{tool_name}] result:")
            print(_json.dumps(result, indent=2, default=str)[:3000])
        return False

    def _cmd_diff(self, _arg: str) -> bool:
        """Show git diff of the working directory.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        import subprocess

        try:
            proc = subprocess.run(
                ["git", "diff", "--stat"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode != 0:
                self._print_error("Not a git repository or git not available.")
                return False
            stat_output = proc.stdout.strip()
            if not stat_output:
                self._print_system("No uncommitted changes.")
                return False
            self._print_info("--- Git Diff (stat) ---")
            print(stat_output)
            # Also show short diff
            proc2 = subprocess.run(
                ["git", "diff", "--no-color"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            diff_text = proc2.stdout.strip()
            if diff_text:
                print()
                # Truncate very long diffs
                if len(diff_text) > 3000:
                    print(diff_text[:3000])
                    self._print_system(f"... ({len(diff_text) - 3000} more characters)")
                else:
                    print(diff_text)
        except FileNotFoundError:
            self._print_error("git is not installed.")
        except subprocess.TimeoutExpired:
            self._print_error("git diff timed out.")
        return False

    def _cmd_config(self, arg: str) -> bool:
        """View or set configuration values.

        Usage: ``/config`` to view all, ``/config <key> <value>`` to set.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        from api.config import get_config, save_config

        cfg = get_config()

        if not arg:
            # Show current configuration
            print()
            self._print_info("--- Configuration ---")
            self._print_info(f"  ollama_host:       {cfg.ollama_host}")
            self._print_info(f"  ollama_model:      {cfg.ollama_model}")
            self._print_info(f"  provider:          {cfg.provider}")
            self._print_info(f"  context_length:    {cfg.context_length}")
            self._print_info(f"  auto_compact:      {cfg.auto_compact}")
            self._print_info(f"  compact_threshold: {cfg.compact_threshold}")
            self._print_info(f"  hooks_enabled:     {cfg.hooks_enabled}")
            print()
            self._print_system("Use /config <key> <value> to change a setting.")
            return False

        parts = arg.split(maxsplit=1)
        key = parts[0]
        value = parts[1] if len(parts) > 1 else ""

        if not hasattr(cfg, key):
            self._print_error(f"Unknown config key: {key}")
            return False

        if not value:
            self._print_info(f"  {key} = {getattr(cfg, key)}")
            return False

        # Type-coerce the value
        current = getattr(cfg, key)
        try:
            if isinstance(current, bool):
                coerced = value.lower() in ("1", "true", "yes", "on")
            elif isinstance(current, int):
                coerced = int(value)
            elif isinstance(current, float):
                coerced = float(value)
            else:
                coerced = value
            setattr(cfg, key, coerced)
            save_config(cfg)
            self._print_info(f"  {key} = {coerced} (saved)")
        except (ValueError, TypeError) as exc:
            self._print_error(f"Invalid value for {key}: {exc}")
        return False

    def _cmd_bug(self, arg: str) -> bool:
        """File a bug report about the current session.

        Saves session context and a description to ``.ollama/bugs/``.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        import json as _json
        from datetime import datetime, timezone

        description = arg or "No description provided"
        bug_dir = Path(".ollama/bugs")
        bug_dir.mkdir(parents=True, exist_ok=True)

        bug_id = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        bug_file = bug_dir / f"bug_{bug_id}.json"

        status = self.session.get_status()
        report = {
            "id": bug_id,
            "description": description,
            "session_id": status["session_id"],
            "model": status["model"],
            "provider": status["provider"],
            "messages": status["messages"],
            "token_metrics": status["token_metrics"],
            "context_usage": status["context_usage"],
            "recent_messages": self.session.context_manager.messages[-_BUG_CONTEXT_MESSAGES:],
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        }

        try:
            bug_file.write_text(_json.dumps(report, indent=2, default=str), encoding="utf-8")
            self._print_info(f"Bug report saved: {bug_file}")
        except OSError as exc:
            self._print_error(f"Failed to save bug report: {exc}")
        return False

    # -- orchestration commands (team planning / build / resume) ---------------

    async def _cmd_team_planning(self, arg: str) -> bool:
        """Generate an engineering implementation plan and save it to ``specs/``.

        Usage: ``/team_planning <description of what to build>``

        The plan is generated by sending the request to the active model and
        saving the structured output to ``specs/<name>.md``.  A ``Stop`` hook
        is fired after the file is written so validators can check content.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        import json as _json
        import re
        from datetime import datetime, timezone

        if not arg:
            self._print_error("Usage: /team_planning <description of what to build>")
            self._print_system("  Example: /team_planning Add user authentication with JWT tokens")
            return False

        specs_dir = Path("specs")
        specs_dir.mkdir(parents=True, exist_ok=True)

        # Derive a kebab-case filename from the first few words
        slug = re.sub(r"[^a-z0-9]+", "-", arg.lower()).strip("-")[:60]
        plan_file = specs_dir / f"{slug}.md"

        self._print_system("Generating implementation plan ...")

        # Build the planning prompt
        planning_prompt = (
            "Create a detailed engineering implementation plan for the following requirement.\n\n"
            f"Requirement: {arg}\n\n"
            "The plan MUST include ALL of the following sections:\n"
            "## Task Description\n"
            "## Objective\n"
            "## Relevant Files\n"
            "## Step by Step Tasks\n"
            "## Acceptance Criteria\n"
            "## Team Orchestration\n"
            "### Team Members\n\n"
            "For each step in 'Step by Step Tasks', include:\n"
            "- Task ID (kebab-case)\n"
            "- Depends On (task IDs or 'none')\n"
            "- Assigned To (team member name)\n"
            "- Parallel (true/false)\n"
            "- Specific actions to complete\n\n"
            "Format the output as a complete Markdown document starting with:\n"
            f"# Plan: {arg[:80]}\n"
        )

        try:
            spinner = self._spinner(_LLAMA_PLAN_SPINNER)
            spinner.start()
            try:
                result = await self.session.send(planning_prompt)
            finally:
                spinner.stop()
        except Exception as exc:
            self._print_error(f"Failed to generate plan: {exc}")
            return False

        plan_content = result.get("content", "")
        if not plan_content or plan_content.startswith("[placeholder]"):
            self._print_error("Model returned an empty or placeholder plan.")
            return False

        # Write the plan
        try:
            plan_file.write_text(plan_content, encoding="utf-8")
            self._print_info(f"Plan saved: {plan_file}")
        except OSError as exc:
            self._print_error(f"Cannot write plan: {exc}")
            return False

        # Fire the Stop hook so validators can check the plan
        try:
            from server.hook_runner import HookRunner

            runner = HookRunner()
            if runner.is_enabled():
                hook_payload = {
                    "event": "team_planning",
                    "plan_file": str(plan_file),
                    "directory": "specs",
                    "extension": ".md",
                }
                results = runner.run_hook("Stop", hook_payload, timeout=15)
                for r in results:
                    if not r.success:
                        self._print_system(f"  Hook warning: {r.error or r.stderr.strip()}")
        except Exception:
            logger.debug("Stop hook failed after team_planning", exc_info=True)

        # Save a task record so /resume can find it later
        task_record = {
            "id": slug,
            "type": "team_planning",
            "description": arg,
            "plan_file": str(plan_file),
            "session_id": self.session.session_id,
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

        # Report
        print()
        self._print_info("✅ Implementation Plan Created")
        self._print_info(f"  File: {plan_file}")
        self._print_info(f"  Topic: {arg[:100]}")
        print()
        self._print_system(f"To execute this plan, run: /build {plan_file}")
        print()
        return False

    async def _cmd_build(self, arg: str) -> bool:
        """Read a plan file and send it to the model for implementation.

        Usage: ``/build <path-to-plan>``

        Reads the plan file, sends the content to the model with
        implementation instructions, and displays the response.  Updates
        the task record status to ``in_progress`` / ``completed``.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        import json as _json

        if not arg:
            self._print_error("Usage: /build <path-to-plan>")
            self._print_system("  Example: /build specs/add-user-auth.md")
            return False

        plan_path = Path(arg.strip())
        if not plan_path.is_file():
            self._print_error(f"Plan file not found: {plan_path}")
            return False

        try:
            plan_content = plan_path.read_text(encoding="utf-8")
        except OSError as exc:
            self._print_error(f"Cannot read plan: {exc}")
            return False

        self._print_system(f"Building from plan: {plan_path}")
        self._print_system(f"  ({len(plan_content)} chars)")

        # Update task status if a matching task record exists
        task_id = plan_path.stem
        task_file = Path(".ollama/tasks") / f"{task_id}.json"
        if task_file.is_file():
            try:
                task_data = _json.loads(task_file.read_text(encoding="utf-8"))
                task_data["status"] = "in_progress"
                task_file.write_text(_json.dumps(task_data, indent=2), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to update task status for %s: %s", task_file, exc)

        build_prompt = (
            "You are implementing a plan. Read the plan below carefully and "
            "execute it step by step. Follow the plan's instructions precisely.\n\n"
            f"--- PLAN START ---\n{plan_content}\n--- PLAN END ---\n\n"
            "Implement this plan now. Report what was completed for each step."
        )

        try:
            spinner = self._spinner(_LLAMA_BUILD_SPINNER)
            spinner.start()
            try:
                result = await self.session.send(build_prompt)
            finally:
                spinner.stop()
        except Exception as exc:
            self._print_error(f"Build failed: {exc}")
            return False

        content = result.get("content", "")
        self._print_response(content)

        # Show token usage
        metrics = result.get("metrics", {})
        total = metrics.get("total_tokens", 0)
        cost = metrics.get("cost_estimate", 0.0)
        self._print_system(f"  tokens: {total:,} | cost: ${cost:.4f}")

        # Mark task as completed
        if task_file.is_file():
            try:
                task_data = _json.loads(task_file.read_text(encoding="utf-8"))
                task_data["status"] = "completed"
                task_file.write_text(_json.dumps(task_data, indent=2), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to update task status for %s: %s", task_file, exc)

        return False

    def _cmd_resume(self, arg: str) -> bool:
        """List previous tasks and resume one.

        Usage: ``/resume`` to list, ``/resume <task-id>`` to resume.

        Scans ``.ollama/tasks/`` for saved task records and lets the user
        pick one to continue working on.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        import json as _json

        tasks_dir = Path(".ollama/tasks")
        if not tasks_dir.is_dir():
            self._print_system("No previous tasks found.")
            return False

        task_files = sorted(tasks_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not task_files:
            self._print_system("No previous tasks found.")
            return False

        if not arg:
            # List all tasks
            print()
            self._print_info("Previous tasks:")
            for tf in task_files[:20]:
                try:
                    data = _json.loads(tf.read_text(encoding="utf-8"))
                    status = data.get("status", "unknown")
                    task_type = data.get("type", "unknown")
                    desc = data.get("description", "")[:60]
                    status_color = {"planned": _cyan, "in_progress": _bold, "completed": _green}.get(status, _dim)
                    task_id = data.get("id", tf.stem)
                    padded_status = f"{status:<10s}"
                    print(f"  {_cyan(task_id):30s} [{status_color(padded_status)}] {task_type}: {desc}")
                except Exception:
                    print(f"  {_dim(tf.stem)}")
            print()
            self._print_system("Use /resume <task-id> to resume a task.")
            return False

        # Resume a specific task
        task_id = arg.strip()
        task_file = tasks_dir / f"{task_id}.json"
        if not task_file.is_file():
            self._print_error(f"Task not found: {task_id}")
            return False

        try:
            data = _json.loads(task_file.read_text(encoding="utf-8"))
        except Exception as exc:
            self._print_error(f"Cannot read task: {exc}")
            return False

        task_type = data.get("type", "")
        plan_file = data.get("plan_file", "")

        self._print_info(f"Resuming task: {task_id}")
        self._print_info(f"  Type:   {task_type}")
        self._print_info(f"  Status: {data.get('status', 'unknown')}")
        if plan_file:
            self._print_info(f"  Plan:   {plan_file}")
            self._print_system(f"  Run /build {plan_file} to execute this plan.")

        # Update status
        data["status"] = "in_progress"
        try:
            task_file.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        except OSError:
            # Best-effort status update; failures should not prevent resuming the task.
            pass

        return False

    def _cmd_update_status_line(self, arg: str) -> bool:
        """Update session status line metadata.

        Usage: ``/update_status_line <key> <value>``

        Stores arbitrary key-value pairs in the session file's ``extras``
        object, enabling dynamic status line customisation.

        Returns
        -------
        Always ``False`` (continue REPL).
        """
        import json as _json

        if not arg:
            self._print_error("Usage: /update_status_line <key> <value>")
            self._print_system("  Example: /update_status_line project myapp")
            return False

        parts = arg.split(maxsplit=1)
        if len(parts) < 2:
            self._print_error("Both key and value are required.")
            self._print_system("  Usage: /update_status_line <key> <value>")
            return False

        key, value = parts[0], parts[1]

        # Update the session file's extras object.
        # Only update an existing, valid session file to avoid creating
        # incomplete JSON that --resume or Session.save() would clobber.
        session_dir = Path(".ollama/sessions")
        session_file = session_dir / f"{self.session.session_id}.json"

        if not session_file.is_file():
            self._print_error("Session file not found; cannot update status line. Start a session first.")
            return False

        try:
            data: Any = _json.loads(session_file.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            self._print_error(f"Failed to read session file; not updating status line: {exc}")
            return False

        if not isinstance(data, dict):
            self._print_error("Session file is malformed (expected JSON object); cannot update status line.")
            return False

        extras = data.get("extras") or {}
        if not isinstance(extras, dict):
            extras = {}
        old_value = extras.get(key)
        extras[key] = value
        data["extras"] = extras

        try:
            session_file.write_text(_json.dumps(data, indent=2), encoding="utf-8")
        except OSError as exc:
            self._print_error(f"Failed to update session file: {exc}")
            return False

        self._print_info(f"Status line updated: {key} = {value}")
        if old_value is not None:
            self._print_system(f"  Previous value: {old_value}")
        return False

    def _cmd_quit(self, _arg: str) -> bool:
        """Signal the REPL to exit gracefully.

        Returns
        -------
        Always ``True`` (exit REPL).
        """
        return True

    # -- main REPL loop -------------------------------------------------------

    async def run(self) -> None:
        """Start the interactive REPL loop.

        Prints a welcome banner, then enters a read-eval-print loop that
        processes slash commands and sends regular input to the session for
        model response.  Handles Ctrl+C (cancel current input) and Ctrl+D
        (exit) gracefully.
        """
        self._running = True
        self._print_banner()

        try:
            while self._running:
                try:
                    user_input = self._read_input()
                except KeyboardInterrupt:
                    # Ctrl+C: cancel current input, print a blank line, continue
                    print()
                    continue

                # Ctrl+D on empty line -> exit
                if user_input is None:
                    print()
                    self._print_system("Goodbye.")
                    break

                # Skip blank lines
                stripped = user_input.strip()
                if not stripped:
                    continue

                # Slash command
                if stripped.startswith("/"):
                    should_exit = await self._dispatch_command(stripped)
                    if should_exit:
                        self._print_system("Goodbye.")
                        break
                    continue

                # Check if this is an agent-specific command
                agent_type = None
                if stripped.startswith("@"):
                    # Extract agent type from command (e.g., "@code write a function")
                    parts = stripped.split(" ", 1)
                    if len(parts) > 1:
                        agent_type = parts[0][1:]  # Remove the @ symbol
                        stripped = parts[1]

                # Regular message -> send to session with llama spinner
                try:
                    spinner = self._spinner(_LLAMA_SPINNER_FRAMES)
                    spinner.start()
                    try:
                        result = await self.session.send(stripped, agent_type=agent_type)
                    finally:
                        spinner.stop()
                except Exception as exc:
                    self._print_error(f"Error: {exc}")
                    logger.exception("Failed to send message")
                    continue

                # Display response with agent-colored output
                content = result.get("content", "")
                self._print_response(content, agent_type=agent_type)

                # Show token usage after each response (like Claude Code)
                metrics = result.get("metrics", {})
                total = metrics.get("total_tokens", 0)
                cost = metrics.get("cost_estimate", 0.0)
                context = self.session.context_manager.get_context_usage()
                pct = context.get("percentage", 0)
                self._print_system(f"  tokens: {total:,} | context: {pct}% | cost: ${cost:.4f}")

                # Notify on auto-compaction
                if result.get("compacted"):
                    self._print_system("(Context was auto-compacted)")

        finally:
            self._running = False
            self._save_history()

            # Auto-save the session so --resume can pick it up
            try:
                self.session.save()
            except Exception:
                logger.warning(
                    "Failed to auto-save session; --resume may not work for this session",
                    exc_info=True,
                )

            # End the session
            try:
                summary = await self.session.end()
                duration = summary.get("duration_str", "unknown")
                total_msgs = summary.get("messages", 0)
                total_tokens = summary.get("total_tokens", 0)
                cost = summary.get("cost_estimate", 0.0)
                self._print_system(
                    f"Session ended: {duration}, {total_msgs} messages, {total_tokens:,} tokens, ${cost:.4f}"
                )
            except Exception:
                logger.warning("Failed to end session cleanly", exc_info=True)


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    async def _test() -> None:
        """Create a mock session and verify the REPL initialises correctly."""
        session = Session(model="llama3.2", provider="ollama")
        await session.start()

        repl = InteractiveMode(session)

        # Verify the object was created and configured
        assert repl.session is session
        assert repl._running is False
        assert "/help" in InteractiveMode._COMMAND_TABLE
        assert "/quit" in InteractiveMode._COMMAND_TABLE
        assert "/exit" in InteractiveMode._COMMAND_TABLE

        # Test command dispatch: /status should not exit
        should_exit = await repl._dispatch_command("/status")
        assert should_exit is False

        # Test command dispatch: /quit should exit
        should_exit = await repl._dispatch_command("/quit")
        assert should_exit is True

        # Test model switching
        repl._cmd_model("codellama")
        assert session.model == "codellama"

        # Test provider switching
        repl._cmd_provider("claude")
        assert session.provider == "claude"

        # Test invalid provider
        repl._cmd_provider("invalid_provider")
        assert session.provider == "claude"  # unchanged

        # Test clear
        repl._cmd_clear("")
        assert len(session.context_manager.messages) == 0

        # Test history on empty
        repl._cmd_history("")

        # Test help output
        repl._cmd_help("")

        # Verify readline history file path
        assert _HISTORY_FILE == Path(".ollama/history")

        print()
        print(_green("All interactive REPL tests passed."))

        # End the session
        await session.end()

    # Only run tests when not connected to a real terminal (CI / scripted)
    # or when OLLAMA_CLI_TEST is set.  Otherwise, start the full REPL.
    if os.environ.get("OLLAMA_CLI_TEST") or not sys.stdin.isatty():
        asyncio.run(_test())
    else:

        async def _main() -> None:
            session = Session(model="llama3.2", provider="ollama")
            await session.start()
            repl = InteractiveMode(session)
            await repl.run()

        asyncio.run(_main())
