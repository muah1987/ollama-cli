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
ContextManager and TokenCounter, handles QARIN.md project context, and
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

from api.provider_router import ProviderRouter  # noqa: E402
from runner.agent_comm import AgentCommBus  # noqa: E402
from runner.context_manager import ContextManager  # noqa: E402
from runner.memory_layer import MemoryLayer  # noqa: E402
from runner.token_counter import TokenCounter  # noqa: E402

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SESSIONS_DIR = ".qarin/sessions"
_MEMORY_FILE = ".qarin/memory.json"
_QARIN_MD = "QARIN.md"

# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class Session:
    """Manages a complete CLI session with context, tokens, and persistence.

    Coordinates the :class:`ContextManager` for conversation history and the
    :class:`TokenCounter` for usage tracking.  On start, reads ``QARIN.md``
    (if present) to seed the system prompt with project context.  On end,
    optionally appends a session summary back to ``QARIN.md``.

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
        provider_router: ProviderRouter | None = None,
    ) -> None:
        self.session_id: str = session_id or uuid.uuid4().hex[:12]
        self.model: str = model
        self.provider: str = provider
        self.context_manager: ContextManager = context_manager or ContextManager()
        self.token_counter: TokenCounter = token_counter or TokenCounter(provider=provider)
        self.agent_comm: AgentCommBus = AgentCommBus()
        self.memory_layer: MemoryLayer = MemoryLayer()
        self.hooks_enabled: bool = hooks_enabled
        self.provider_router: ProviderRouter = provider_router or ProviderRouter()

        self.start_time: datetime | None = None
        self._end_time: datetime | None = None
        self._message_count: int = 0

    # -- sub-context helpers -------------------------------------------------

    def create_sub_context(self, context_id: str, **kwargs: Any) -> ContextManager:
        """Create a sub-context on the underlying :class:`ContextManager`.

        Parameters
        ----------
        context_id:
            Unique identifier for the sub-context.
        **kwargs:
            Optional overrides forwarded to
            :meth:`ContextManager.create_sub_context`.

        Returns
        -------
        The newly created child :class:`ContextManager`.
        """
        return self.context_manager.create_sub_context(context_id, **kwargs)

    def get_sub_context(self, context_id: str) -> ContextManager | None:
        """Return a sub-context by identifier.

        Parameters
        ----------
        context_id:
            The sub-context identifier.

        Returns
        -------
        The child :class:`ContextManager`, or ``None`` if not found.
        """
        return self.context_manager.get_sub_context(context_id)

    # -- lifecycle -----------------------------------------------------------

    async def start(self) -> None:
        """Initialize the session.

        Records the start time and loads ``QARIN.md`` project context (if
        found in the current working directory) as the system message.
        """
        self.start_time = datetime.now(tz=timezone.utc)
        logger.info("Session %s started (model=%s, provider=%s)", self.session_id, self.model, self.provider)

        # Load persistent memory if it exists
        memory_path = Path(_MEMORY_FILE)
        if memory_path.is_file():
            self.memory_layer.load(str(memory_path))

        # Build the system prompt with tool awareness
        system_prompt = self._build_system_prompt()

        # Load QARIN.md as project context if it exists
        ollama_md = self._find_ollama_md()
        if ollama_md is not None:
            try:
                content = ollama_md.read_text(encoding="utf-8")
                system_prompt += "\n\nThe following project context was loaded from QARIN.md:\n\n" + content
                logger.info("Loaded project context from %s (%d chars)", ollama_md, len(content))
            except OSError:
                logger.warning("Found QARIN.md but failed to read it", exc_info=True)

        self.context_manager.set_system_message(system_prompt)

    async def send(
        self,
        message: str,
        agent_type: str | None = None,
        context_id: str | None = None,
    ) -> dict[str, Any]:
        """Send a user message and get a response.

        This method adds the user message to the context, delegates to the
        provider for a response via ProviderRouter, updates token
        metrics, and triggers auto-compaction when the threshold is reached.

        Parameters
        ----------
        message:
            The user's input text.
        agent_type:
            Specific agent type for custom model assignment.
        context_id:
            If provided, route the message through the named sub-context.

        Returns
        -------
        Dict with ``content`` (response text), ``metrics`` (token info),
        and ``compacted`` (whether compaction was triggered).
        """
        self._message_count += 1

        # Determine target context
        target_cm = self.context_manager
        if context_id is not None:
            sub = self.context_manager.get_sub_context(context_id)
            if sub is not None:
                target_cm = sub

        target_cm.add_message("user", message)

        # Prepare messages for the provider
        messages = target_cm.messages.copy()
        # Add the new user message if it's not already in the context
        if not messages or messages[-1]["role"] != "user" or messages[-1]["content"] != message:
            messages.append({"role": "user", "content": message})

        # Load native tool definitions for function calling
        tools_schema = self._get_tools_schema()

        try:
            response_content, response_metrics = await self._route_with_tools(
                messages=messages,
                target_cm=target_cm,
                tools_schema=tools_schema,
                agent_type=agent_type,
            )
        except Exception as e:
            logger.warning("Provider call failed, using placeholder: %s", e)
            # Fallback to placeholder on error
            response_content = f"[placeholder] Response to: {message[:80]}"
            response_metrics = {
                "prompt_eval_count": target_cm._estimated_context_tokens,
                "eval_count": max(1, len(response_content) // 4),
                "eval_duration": 1_000_000_000,  # 1 second stub
                "total_duration": 1_500_000_000,
            }

        # Record assistant response
        target_cm.add_message("assistant", response_content)
        target_cm.update_metrics(response_metrics)
        self.token_counter.update(response_metrics)

        # Sync context window info into the token counter
        usage_info = target_cm.get_context_usage()
        self.token_counter.set_context(usage_info["used"], usage_info["max"])

        # Auto-compact if threshold reached
        compacted = False
        if target_cm.auto_compact and target_cm.should_compact():
            try:
                compact_result = await target_cm.compact()
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
        a brief session record to ``QARIN.md``.

        Returns
        -------
        Session summary dict with duration, tokens, messages, and model info.
        """
        self._end_time = datetime.now(tz=timezone.utc)
        summary = self._build_summary()

        # Save persistent memory
        self.memory_layer.save(str(Path(_MEMORY_FILE)))

        # Append summary to QARIN.md if the file exists
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
            "agent_comm": self.agent_comm.get_token_savings(),
            "memory": self.memory_layer.get_token_savings(),
        }

    # -- persistence ---------------------------------------------------------

    def save(self, path: str | None = None) -> str:
        """Persist the full session state to a JSON file.

        Parameters
        ----------
        path:
            File path.  Defaults to ``.qarin/sessions/{session_id}.json``.

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
                "sub_contexts": {
                    cid: {
                        "messages": sub.messages,
                        "system_message": sub.system_message,
                        "max_context_length": sub.max_context_length,
                        "compact_threshold": sub.compact_threshold,
                        "auto_compact": sub.auto_compact,
                        "keep_last_n": sub.keep_last_n,
                        "estimated_context_tokens": sub._estimated_context_tokens,
                        "total_prompt_tokens": sub.total_prompt_tokens,
                        "total_completion_tokens": sub.total_completion_tokens,
                    }
                    for cid, sub in self.context_manager._sub_contexts.items()
                },
            },
            "saved_at": datetime.now(tz=timezone.utc).isoformat(),
            "agent_comm": self.agent_comm.get_token_savings(),
            "memory_layer": self.memory_layer.get_token_savings(),
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
            ``.qarin/sessions/{session_id}.json``.

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

        # Restore sub-contexts
        for cid, sub_data in cm_data.get("sub_contexts", {}).items():
            sub = cm.create_sub_context(
                cid,
                max_context_length=sub_data.get("max_context_length", cm.max_context_length),
                compact_threshold=sub_data.get("compact_threshold", cm.compact_threshold),
                auto_compact=sub_data.get("auto_compact", cm.auto_compact),
                keep_last_n=sub_data.get("keep_last_n", cm.keep_last_n),
            )
            sub.system_message = sub_data.get("system_message")
            sub.messages = sub_data.get("messages", [])
            sub._estimated_context_tokens = sub_data.get("estimated_context_tokens", 0)
            sub.total_prompt_tokens = sub_data.get("total_prompt_tokens", 0)
            sub.total_completion_tokens = sub_data.get("total_completion_tokens", 0)

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

    # Maximum number of consecutive tool-call rounds to prevent runaway loops
    _MAX_TOOL_ROUNDS = 10
    # Maximum characters to include in a tool result message
    _MAX_TOOL_RESULT_LENGTH = 3000

    @staticmethod
    def _get_tools_schema() -> list[dict[str, Any]]:
        """Return the native tool definitions for the Ollama API.

        Falls back to an empty list if the tools module is unavailable.
        """
        try:
            from skills.tools import get_tools_schema

            return get_tools_schema()
        except Exception:
            return []

    @staticmethod
    def _extract_response(response: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
        """Extract text content and tool calls from a provider response.

        Returns
        -------
        Tuple of (response_text, tool_calls_list).
        """
        tool_calls: list[dict[str, Any]] = []

        # 1. OpenAI/Codex/HF format: {"choices": [{"message": {"content":..., "tool_calls":...}}]}
        choices = response.get("choices", [])
        if choices and isinstance(choices, list) and len(choices) > 0:
            msg = choices[0].get("message", {})
            content = msg.get("content") or ""
            tool_calls = msg.get("tool_calls", []) or []
            return content or "[empty response]", tool_calls

        # 2. Ollama native format: {"message": {"role": "assistant", "content":..., "tool_calls":...}}
        if "message" in response and isinstance(response["message"], dict):
            msg = response["message"]
            content = msg.get("content") or ""
            tool_calls = msg.get("tool_calls", []) or []
            return content or "[empty response]", tool_calls

        # 3. Anthropic format: {"content": [{"text":...} | {"type":"tool_use",...}]}
        if "content" in response and isinstance(response["content"], list):
            parts = response["content"]
            text_parts = [p.get("text", "") for p in parts if isinstance(p, dict) and p.get("text")]
            content = " ".join(text_parts) or "[empty response]"
            return content, tool_calls

        # 4. Gemini format: {"candidates": [{"content": {"parts": [{"text":...}]}}]}
        if "candidates" in response:
            candidates = response["candidates"]
            if isinstance(candidates, list) and candidates:
                first = candidates[0]
                if isinstance(first, dict):
                    cparts = first.get("content", {})
                    if isinstance(cparts, dict):
                        part_list = cparts.get("parts", [])
                        if isinstance(part_list, list) and part_list:
                            return str(part_list[0].get("text", "[empty response]")), tool_calls
            return "[empty response]", tool_calls

        # 5. Direct content string
        if "content" in response:
            return str(response["content"]), tool_calls

        # 6. Ollama generate format: {"response": "..."}
        if "response" in response:
            return str(response["response"]), tool_calls

        return "[no content]", tool_calls

    @staticmethod
    def _extract_metrics(response: dict[str, Any]) -> dict[str, Any]:
        """Extract token usage metrics from a provider response."""
        usage = response.get("usage", {})
        return {
            "prompt_eval_count": usage.get("prompt_tokens", 0),
            "eval_count": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
        }

    async def _route_with_tools(
        self,
        messages: list[dict[str, Any]],
        target_cm: Any,
        tools_schema: list[dict[str, Any]],
        agent_type: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Route a request and handle tool-call loops.

        When the model responds with tool calls, this method auto-executes
        the tools and feeds the results back to the model, repeating until
        the model produces a final text response or the maximum number of
        rounds is reached.

        Returns
        -------
        Tuple of (final_response_content, response_metrics).
        """
        kwargs: dict[str, Any] = {}
        if tools_schema:
            kwargs["tools"] = tools_schema

        accumulated_content: list[str] = []

        for _round in range(self._MAX_TOOL_ROUNDS):
            response = await self.provider_router.route(
                task_type="agent",
                messages=messages,
                agent_type=agent_type,
                model=self.model,
                provider=self.provider,
                **kwargs,
            )

            if not isinstance(response, dict):
                # Streaming response – no tool-call support
                content = "[streaming response]"
                metrics: dict[str, Any] = {
                    "prompt_eval_count": target_cm._estimated_context_tokens,
                    "eval_count": max(1, len(content) // 4),
                    "eval_duration": 1_000_000_000,
                    "total_duration": 1_500_000_000,
                }
                return content, metrics

            response_content, tool_calls = self._extract_response(response)
            response_metrics = self._extract_metrics(response)

            if not tool_calls:
                # No tool calls – return the final text response
                if accumulated_content:
                    accumulated_content.append(response_content)
                    return "\n".join(accumulated_content), response_metrics
                return response_content, response_metrics

            # The model wants to call tools – execute them
            if response_content and response_content != "[empty response]":
                accumulated_content.append(response_content)

            # Append the assistant message with tool calls to the conversation
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": response_content or ""}
            assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

            # Execute each tool call and append results
            for tc in tool_calls:
                func_info = tc.get("function", tc)
                tool_name = func_info.get("name", "")
                arguments = func_info.get("arguments", {})
                if isinstance(arguments, str):
                    try:
                        arguments = json.loads(arguments)
                    except (json.JSONDecodeError, TypeError):
                        arguments = {}

                tool_result = self._execute_tool(tool_name, arguments)
                result_str = json.dumps(tool_result, default=str)[: self._MAX_TOOL_RESULT_LENGTH]

                logger.info("Tool %s executed: %s", tool_name, result_str[:200])

                # Append tool result following the Ollama API tool-call
                # response format: {"role": "tool", "content": "<json_result>"}
                # See https://docs.qarin.com/api/chat for the expected schema.
                messages.append(
                    {
                        "role": "tool",
                        "content": result_str,
                    }
                )

        # Max rounds reached – return what we have
        if accumulated_content:
            return "\n".join(accumulated_content), response_metrics
        return response_content, response_metrics

    @staticmethod
    def _execute_tool(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a built-in tool by name.

        Parameters
        ----------
        tool_name:
            Name of the tool (e.g. ``file_read``).
        arguments:
            Keyword arguments for the tool.

        Returns
        -------
        Tool result dict.
        """
        try:
            from skills.tools import execute_tool_call

            return execute_tool_call(tool_name, arguments)
        except Exception as exc:
            return {"error": str(exc)}

    @staticmethod
    def _build_system_prompt() -> str:
        """Build a system prompt that includes available tools and skills.

        Returns
        -------
        A system prompt string informing the AI about its capabilities.
        """
        try:
            from skills.tools import list_tools

            tools = list_tools()
        except Exception:
            tools = []

        prompt = (
            "You are an AI coding assistant powered by qarin. "
            "You help users with coding tasks, file operations, and project management.\n\n"
        )

        if tools:
            prompt += "You have access to the following built-in tools:\n"
            for t in tools:
                prompt += f"- {t['name']}: {t['description']}\n"
            prompt += (
                "\nYou can call these tools directly using native function calling. "
                "When a user asks you to perform an action (e.g. reading files, editing code, "
                "running shell commands, fetching URLs, searching files, or cloning a repo), "
                "use the appropriate tool call to execute the action. "
                "Analyze the tool results and provide a helpful summary to the user.\n"
            )

        return prompt

    @staticmethod
    def _find_ollama_md() -> Path | None:
        """Look for QARIN.md in the current working directory and parent dirs.

        Returns
        -------
        Path to QARIN.md if found, otherwise ``None``.
        """
        current = Path.cwd()
        for _ in range(5):  # search up to 5 levels
            candidate = current / _QARIN_MD
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
        """Append a short session record to QARIN.md.

        Parameters
        ----------
        ollama_md:
            Path to the QARIN.md file.
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
