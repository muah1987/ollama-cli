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

# ---------------------------------------------------------------------------
# ANSI escape helpers
# ---------------------------------------------------------------------------


def _green(text: str) -> str:
    """Wrap *text* in green ANSI escape codes."""
    return f"\033[32m{text}\033[0m"


def _dim(text: str) -> str:
    """Wrap *text* in dim/gray ANSI escape codes."""
    return f"\033[2m{text}\033[0m"


def _red(text: str) -> str:
    """Wrap *text* in red ANSI escape codes."""
    return f"\033[31m{text}\033[0m"


def _cyan(text: str) -> str:
    """Wrap *text* in cyan ANSI escape codes."""
    return f"\033[36m{text}\033[0m"


def _bold(text: str) -> str:
    """Wrap *text* in bold ANSI escape codes."""
    return f"\033[1m{text}\033[0m"


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
        "/help": "_cmd_help",
        "/quit": "_cmd_quit",
        "/exit": "_cmd_quit",
        "/set-agent-model": "_cmd_set_agent_model",
        "/list-agent-models": "_cmd_list_agent_models",
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

    def _print_response(self, text: str) -> None:
        """Print an assistant response with a green model-name prefix."""
        prefix = _green(f"[{self.session.model}] ")
        print(f"{prefix}{text}")

    def _print_banner(self) -> None:
        """Print the welcome banner on REPL startup."""
        print()
        print(_bold("ollama-cli interactive mode"))
        self._print_info(f"  model:    {self.session.model}")
        self._print_info(f"  provider: {self.session.provider}")
        self._print_info(f"  session:  {self.session.session_id}")
        self._print_system("  Type /help for commands, Ctrl+D to exit.")
        print()

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
        usage_before = self.session.context_manager.get_context_usage()
        self._print_system(
            f"Before compaction: {usage_before['used']:,} / {usage_before['max']:,} tokens "
            f"({usage_before['percentage']}%)"
        )

        try:
            result = await self.session.compact()
        except Exception as exc:
            self._print_error(f"Compaction failed: {exc}")
            return False

        usage_after = self.session.context_manager.get_context_usage()
        self._print_info(
            f"After compaction:  {usage_after['used']:,} / {usage_after['max']:,} tokens ({usage_after['percentage']}%)"
        )
        self._print_info(f"Messages removed:  {result.get('messages_removed', 0)}")
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

        print()
        self._print_info("--- Session Status ---")
        self._print_info(f"  Session ID: {status['session_id']}")
        self._print_info(f"  Model:      {status['model']}")
        self._print_info(f"  Provider:   {status['provider']}")
        self._print_info(f"  Uptime:     {status['uptime_str']}")
        self._print_info(f"  Messages:   {status['messages']}")
        self._print_info(f"  Hooks:      {'enabled' if status['hooks_enabled'] else 'disabled'}")

        self._print_info("--- Tokens ---")
        self._print_info(f"  Prompt:     {token_info.get('prompt_tokens', 0):,}")
        self._print_info(f"  Completion: {token_info.get('completion_tokens', 0):,}")
        self._print_info(f"  Total:      {token_info.get('total_tokens', 0):,}")
        self._print_info(f"  Speed:      {token_info.get('tokens_per_second', 0):.1f} tok/s")
        self._print_info(f"  Cost:       ${token_info.get('cost_estimate', 0):.4f}")

        self._print_info("--- Context ---")
        self._print_info(f"  Used:       {context_info.get('used', 0):,} / {context_info.get('max', 0):,} tokens")
        self._print_info(f"  Usage:      {context_info.get('percentage', 0)}%")
        self._print_info(f"  Remaining:  {context_info.get('remaining', 0):,}")
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
        print(f"  {_cyan('/set-agent-model <type:provider:model>}')}  Assign model to agent type")
        print(f"  {_cyan('/list-agent-models')} List agent model assignments")
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

                # Regular message -> send to session
                try:
                    result = await self.session.send(stripped, agent_type=agent_type)
                except Exception as exc:
                    self._print_error(f"Error: {exc}")
                    logger.exception("Failed to send message")
                    continue

                # Display response
                content = result.get("content", "")
                self._print_response(content)

                # Notify on auto-compaction
                if result.get("compacted"):
                    self._print_system("(Context was auto-compacted)")

        finally:
            self._running = False
            self._save_history()

            # End the session
            try:
                summary = await self.session.end()
                duration = summary.get("duration_str", "unknown")
                total_msgs = summary.get("messages", 0)
                total_tokens = summary.get("total_tokens", 0)
                self._print_system(f"Session ended: {duration}, {total_msgs} messages, {total_tokens:,} tokens")
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
