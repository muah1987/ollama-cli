#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///
"""
Session manager -- GOTCHA Tools layer, ATLAS Assemble phase.

Manages complete CLI sessions with state persistence.  Coordinates the
ContextManager and TokenCounter, handles OLLAMA.md project context, and
provides session save/load for continuity across runs.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ensure sibling modules are importable when run as a script
# ---------------------------------------------------------------------------

_SCRIPT_DIR = Path(__file__).resolve().parent
_PACKAGE_DIR = _SCRIPT_DIR.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))
if str(_PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_DIR))

from src.context_manager import ContextManager  # noqa: E402
from src.token_counter import TokenCounter  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SESSIONS_DIR = ".ollama/sessions"
_OLLAMA_MD = "OLLAMA.md"

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class Session:
    """Manages a complete CLI session with context, tokens, and persistence.

    Coordinates the :class:`ContextManager` for conversation history and the
    :class:`TokenCounter` for usage tracking.  On start, reads ``OLLAMA.md``
    (if present) to seed the system prompt with project context.  On end,
    optionally appends a session summary back to ``OLLAMA.md``.

    Parameters
    ----------
    session_id:
        Unique identifier.  Generated as a UUID if not provided.
    model:
        Model name (e.g. ``llama3.2``).
    provider:
        Provider name (``ollama``, ``claude``, ``gemini``, ``codex``).
    context_manager:
        Pre-configured :class:`ContextManager`.  One is created with
        defaults if not supplied.
    token_counter:
        Pre-configured :class:`TokenCounter`.  One is created with
        defaults if not supplied.
    hooks_enabled:
        Whether lifecycle hooks are active for this session.
    """

    def __init__(
        self,
        session_id: str | None = None,
        model: str = "llama3.2",
        provider: str = "ollama",
        context_manager: ContextManager | None = None,
        token_counter: TokenCounter | None = None,
        hooks_enabled: bool = True,
    ) -> None:
        self.session_id: str = session_id or uuid.uuid4().hex[:12]
        self.model: str = model
        self.provider: str = provider
        self.context_manager: ContextManager = context_manager or ContextManager()
        self.token_counter: TokenCounter = token_counter or TokenCounter(provider=provider)
        self.hooks_enabled: bool = hooks_enabled

        self.start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._message_count: int = 0

    # -- lifecycle -----------------------------------------------------------

    async def start(self) -> None:
        """Initialize the session.

        Records the start time and loads ``OLLAMA.md`` project context (if
        found in the current working directory) as the system message.
        """
        self.start_time = datetime.now(tz=timezone.utc)
        logger.info("Session %s started (model=%s, provider=%s)", self.session_id, self.model, self.provider)

        # Load OLLAMA.md as project context if it exists
        ollama_md = self._find_ollama_md()
        if ollama_md is not None:
            try:
                content = ollama_md.read_text(encoding="utf-8")
                system_prompt = (
                    "You are an AI coding assistant.  The following project context "
                    "was loaded from OLLAMA.md:\n\n" + content
                )
                self.context_manager.set_system_message(system_prompt)
                logger.info("Loaded project context from %s (%d chars)", ollama_md, len(content))
            except OSError:
                logger.warning("Found OLLAMA.md but failed to read it", exc_info=True)

    async def send(self, message: str) -> dict[str, Any]:
        """Send a user message and get a response.

        This method adds the user message to the context, delegates to the
        provider for a response (currently a placeholder), updates token
        metrics, and triggers auto-compaction when the threshold is reached.

        Parameters
        ----------
        message:
            The user's input text.

        Returns
        -------
        Dict with ``content`` (response text), ``metrics`` (token info),
        and ``compacted`` (whether compaction was triggered).
        """
        self._message_count += 1
        self.context_manager.add_message("user", message)

        # --- Provider call placeholder ---
        # In production this delegates to OllamaClient.chat() or the
        # appropriate cloud provider.  For now we return a stub so the
        # session pipeline can be tested end-to-end without a running server.
        response_content = f"[placeholder] Response to: {message[:80]}"
        response_metrics: dict[str, Any] = {
            "prompt_eval_count": self.context_manager._estimated_context_tokens,
            "eval_count": max(1, len(response_content) // 4),
            "eval_duration": 1_000_000_000,  # 1 second stub
            "total_duration": 1_500_000_000,
        }

        # Record assistant response
        self.context_manager.add_message("assistant", response_content)
        self.context_manager.update_metrics(response_metrics)
        self.token_counter.update(response_metrics)

        # Sync context window info into the token counter
        usage = self.context_manager.get_context_usage()
        self.token_counter.set_context(usage["used"], usage["max"])

        # Auto-compact if threshold reached
        compacted = False
        if self.context_manager.auto_compact and self.context_manager.should_compact():
            try:
                compact_result = await self.context_manager.compact()
                compacted = True
                logger.info("Auto-compacted: %s", compact_result)
            except Exception:
                logger.warning("Auto-compaction failed", exc_info=True)

        return {
            "content": response_content,
            "metrics": self.token_counter.format_json(),
            "compacted": compacted,
        }

    async def end(self) -> dict[str, Any]:
        """End the session and generate a summary.

        Records the end time, builds a summary dict, and optionally appends
        a brief session record to ``OLLAMA.md``.

        Returns
        -------
        Session summary dict with duration, tokens, messages, and model info.
        """
        self._end_time = datetime.now(tz=timezone.utc)
        summary = self._build_summary()

        # Append summary to OLLAMA.md if the file exists
        ollama_md = self._find_ollama_md()
        if ollama_md is not None:
            self._append_to_ollama_md(ollama_md, summary)

        logger.info("Session %s ended (%s)", self.session_id, summary.get("duration_str", "unknown"))
        return summary

    async def compact(self) -> dict[str, int]:
        """Manually trigger context compaction.

        Returns
        -------
        Compaction result dict from :meth:`ContextManager.compact`.
        """
        result = await self.context_manager.compact()

        # Sync context info after compaction
        usage = self.context_manager.get_context_usage()
        self.token_counter.set_context(usage["used"], usage["max"])

        return result

    # -- status and display --------------------------------------------------

    def get_status(self) -> dict[str, Any]:
        """Return the current session status for display.

        Returns
        -------
        Dict with session_id, model, provider, uptime, token metrics,
        context usage, and message count.
        """
        uptime_seconds = 0.0
        if self.start_time is not None:
            delta = datetime.now(tz=timezone.utc) - self.start_time
            uptime_seconds = delta.total_seconds()

        return {
            "session_id": self.session_id,
            "model": self.model,
            "provider": self.provider,
            "uptime_seconds": round(uptime_seconds, 1),
            "uptime_str": self._format_duration(uptime_seconds),
            "messages": self._message_count,
            "token_metrics": self.token_counter.format_json(),
            "context_usage": self.context_manager.get_context_usage(),
            "hooks_enabled": self.hooks_enabled,
        }

    # -- persistence ---------------------------------------------------------

    def save(self, path: str | None = None) -> str:
        """Persist the full session state to a JSON file.

        Parameters
        ----------
        path:
            File path.  Defaults to ``.ollama/sessions/{session_id}.json``.

        Returns
        -------
        The path the session was saved to.
        """
        if path is None:
            save_dir = Path(_SESSIONS_DIR)
            save_dir.mkdir(parents=True, exist_ok=True)
            path = str(save_dir / f"{self.session_id}.json")

        session_data = {
            "session_id": self.session_id,
            "model": self.model,
            "provider": self.provider,
            "hooks_enabled": self.hooks_enabled,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self._end_time.isoformat() if self._end_time else None,
            "message_count": self._message_count,
            "token_counter": self.token_counter.format_json(),
            "context_manager": {
                "system_message": self.context_manager.system_message,
                "messages": self.context_manager.messages,
                "max_context_length": self.context_manager.max_context_length,
                "compact_threshold": self.context_manager.compact_threshold,
                "auto_compact": self.context_manager.auto_compact,
                "keep_last_n": self.context_manager.keep_last_n,
                "estimated_context_tokens": self.context_manager._estimated_context_tokens,
                "total_prompt_tokens": self.context_manager.total_prompt_tokens,
                "total_completion_tokens": self.context_manager.total_completion_tokens,
            },
            "saved_at": datetime.now(tz=timezone.utc).isoformat(),
        }

        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(session_data, f, indent=2)
            logger.info("Session saved to %s", path)
        except OSError:
            logger.warning("Failed to save session to %s", path, exc_info=True)

        return path

    @classmethod
    def load(cls, session_id: str, path: str | None = None) -> Session:
        """Restore a session from a JSON file.

        Parameters
        ----------
        session_id:
            The session ID to look up.
        path:
            Explicit file path.  Defaults to
            ``.ollama/sessions/{session_id}.json``.

        Returns
        -------
        A restored :class:`Session` instance.

        Raises
        ------
        FileNotFoundError
            If the session file does not exist.
        """
        if path is None:
            path = str(Path(_SESSIONS_DIR) / f"{session_id}.json")

        try:
            with open(path) as f:
                data = json.load(f)
        except OSError as exc:
            raise FileNotFoundError(f"Session file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise FileNotFoundError(f"Session file is corrupted: {path}") from exc

        # Rebuild ContextManager
        cm_data = data.get("context_manager", {})
        cm = ContextManager(
            max_context_length=cm_data.get("max_context_length", 4096),
            compact_threshold=cm_data.get("compact_threshold", 0.85),
            auto_compact=cm_data.get("auto_compact", True),
            keep_last_n=cm_data.get("keep_last_n", 4),
        )
        cm.system_message = cm_data.get("system_message")
        cm.messages = cm_data.get("messages", [])
        cm._estimated_context_tokens = cm_data.get("estimated_context_tokens", 0)
        cm.total_prompt_tokens = cm_data.get("total_prompt_tokens", 0)
        cm.total_completion_tokens = cm_data.get("total_completion_tokens", 0)

        # Rebuild TokenCounter
        tc_data = data.get("token_counter", {})
        provider = data.get("provider", "ollama")
        tc = TokenCounter(provider=provider, context_max=tc_data.get("context_max", 4096))
        tc.prompt_tokens = tc_data.get("prompt_tokens", 0)
        tc.completion_tokens = tc_data.get("completion_tokens", 0)
        tc.tokens_per_second = tc_data.get("tokens_per_second", 0.0)
        tc.context_used = tc_data.get("context_used", 0)
        tc.cost_estimate = tc_data.get("cost_estimate", 0.0)

        # Rebuild Session
        session = cls(
            session_id=data.get("session_id", session_id),
            model=data.get("model", "llama3.2"),
            provider=provider,
            context_manager=cm,
            token_counter=tc,
            hooks_enabled=data.get("hooks_enabled", True),
        )
        session._message_count = data.get("message_count", 0)

        # Restore timestamps
        start_str = data.get("start_time")
        if start_str:
            try:
                session.start_time = datetime.fromisoformat(start_str)
            except ValueError:
                logger.warning("Could not parse start_time: %s", start_str)

        end_str = data.get("end_time")
        if end_str:
            try:
                session._end_time = datetime.fromisoformat(end_str)
            except ValueError:
                logger.warning("Could not parse end_time: %s", end_str)

        logger.info("Session %s loaded from %s", session.session_id, path)
        return session

    # -- private helpers -----------------------------------------------------

    @staticmethod
    def _find_ollama_md() -> Path | None:
        """Look for OLLAMA.md in the current working directory and parent dirs.

        Returns
        -------
        Path to OLLAMA.md if found, otherwise ``None``.
        """
        current = Path.cwd()
        for _ in range(5):  # search up to 5 levels
            candidate = current / _OLLAMA_MD
            if candidate.is_file():
                return candidate
            parent = current.parent
            if parent == current:
                break
            current = parent
        return None

    def _build_summary(self) -> dict[str, Any]:
        """Build a session summary dict."""
        duration_seconds = 0.0
        if self.start_time and self._end_time:
            duration_seconds = (self._end_time - self.start_time).total_seconds()

        return {
            "session_id": self.session_id,
            "model": self.model,
            "provider": self.provider,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self._end_time.isoformat() if self._end_time else None,
            "duration_seconds": round(duration_seconds, 1),
            "duration_str": self._format_duration(duration_seconds),
            "messages": self._message_count,
            "total_tokens": self.token_counter.total_tokens,
            "prompt_tokens": self.token_counter.prompt_tokens,
            "completion_tokens": self.token_counter.completion_tokens,
            "cost_estimate": self.token_counter.cost_estimate,
        }

    @staticmethod
    def _append_to_ollama_md(ollama_md: Path, summary: dict[str, Any]) -> None:
        """Append a short session record to OLLAMA.md.

        Parameters
        ----------
        ollama_md:
            Path to the OLLAMA.md file.
        summary:
            Session summary dict.
        """
        entry = (
            f"\n\n<!-- session:{summary['session_id']} -->\n"
            f"### Session {summary['session_id']}\n"
            f"- Model: {summary['model']} ({summary['provider']})\n"
            f"- Duration: {summary.get('duration_str', 'unknown')}\n"
            f"- Messages: {summary['messages']}\n"
            f"- Tokens: {summary['total_tokens']:,} "
            f"(prompt: {summary['prompt_tokens']:,}, "
            f"completion: {summary['completion_tokens']:,})\n"
        )

        try:
            with open(ollama_md, "a", encoding="utf-8") as f:
                f.write(entry)
            logger.info("Appended session summary to %s", ollama_md)
        except OSError:
            logger.warning("Failed to append session summary to %s", ollama_md, exc_info=True)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format a duration in seconds to a human-readable string.

        Parameters
        ----------
        seconds:
            Duration in seconds.

        Returns
        -------
        String like ``1h 23m 45s`` or ``45s``.
        """
        if seconds < 0:
            return "0s"
        total = int(seconds)
        hours, remainder = divmod(total, 3600)
        minutes, secs = divmod(remainder, 60)

        parts: list[str] = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import asyncio

    async def _test() -> None:
        session = Session(model="llama3.2", provider="ollama")
        await session.start()

        # Simulate a conversation turn
        result = await session.send("Hello, write me a Python function that reverses a string")
        print(f"Response: {result['content']}")
        print(f"Metrics: {result['metrics']}")
        print(f"Compacted: {result['compacted']}")

        # Check status
        status = session.get_status()
        print(f"\nStatus: session_id={status['session_id']}")
        print(f"  Uptime: {status['uptime_str']}")
        print(f"  Messages: {status['messages']}")
        print(f"  Tokens: {status['token_metrics']}")

        # Save and reload
        save_path = session.save()
        print(f"\nSaved to: {save_path}")

        loaded = Session.load(session.session_id)
        print(f"Loaded session: {loaded.session_id} ({loaded._message_count} messages)")

        # End session
        summary = await session.end()
        print(f"\nSession summary: {summary}")

    asyncio.run(_test())
