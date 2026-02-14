#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///
"""
Agent communication bus -- GOTCHA Tools layer, ATLAS Architect phase.

Provides agent-to-agent communication through a message bus pattern.
Enables sub-agents to communicate without going through the parent context,
saving tokens by avoiding redundant context injection.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AgentMessage
# ---------------------------------------------------------------------------


@dataclass
class AgentMessage:
    """A single message exchanged between agents on the communication bus.

    Parameters
    ----------
    sender:
        Identifier of the sending agent.
    recipient:
        Identifier of the receiving agent, or ``"*"`` for broadcasts.
    content:
        The message text.
    message_type:
        One of ``info``, ``request``, ``response``, or ``broadcast``.
    timestamp:
        UTC timestamp of when the message was created.
    token_cost:
        Estimated token cost of the message content.
    """

    sender: str
    recipient: str
    content: str
    message_type: str = "info"
    timestamp: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    token_cost: int = 0


# ---------------------------------------------------------------------------
# AgentCommBus
# ---------------------------------------------------------------------------


class AgentCommBus:
    """Central message bus for agent-to-agent communication.

    Allows agents to exchange messages directly without routing through the
    parent context, reducing token overhead.  All operations are thread-safe.

    Parameters
    ----------
    context_overhead_multiplier:
        Multiplier used to estimate how many tokens a message would cost if
        injected into the parent context instead of sent directly.  Defaults
        to ``3`` (a direct message costs roughly 1/3 of the equivalent
        context injection).
    """

    def __init__(self, context_overhead_multiplier: int = 3) -> None:
        self._messages: list[AgentMessage] = []
        self._lock = threading.Lock()
        self._context_overhead_multiplier = context_overhead_multiplier

    # -- public methods ------------------------------------------------------

    def send(
        self,
        sender_id: str,
        recipient_id: str,
        content: str,
        message_type: str = "info",
    ) -> AgentMessage:
        """Send a targeted message from one agent to another.

        Parameters
        ----------
        sender_id:
            Identifier of the sending agent.
        recipient_id:
            Identifier of the receiving agent.
        content:
            The message text.
        message_type:
            One of ``info``, ``request``, ``response``, or ``broadcast``.

        Returns
        -------
        The created :class:`AgentMessage`.
        """
        token_cost = self._estimate_tokens(content)
        msg = AgentMessage(
            sender=sender_id,
            recipient=recipient_id,
            content=content,
            message_type=message_type,
            token_cost=token_cost,
        )
        with self._lock:
            self._messages.append(msg)
        logger.debug("Agent %s -> %s: %s (%d tokens)", sender_id, recipient_id, content[:80], token_cost)
        return msg

    def broadcast(self, sender_id: str, content: str) -> AgentMessage:
        """Broadcast a message to all agents.

        Parameters
        ----------
        sender_id:
            Identifier of the sending agent.
        content:
            The message text.

        Returns
        -------
        The created :class:`AgentMessage`.
        """
        return self.send(sender_id, "*", content, message_type="broadcast")

    def receive(
        self,
        agent_id: str,
        since: datetime | None = None,
    ) -> list[AgentMessage]:
        """Get pending messages for an agent.

        Returns messages where the agent is the recipient or where the
        message was broadcast (recipient ``"*"``), excluding messages sent
        by the agent itself.

        Parameters
        ----------
        agent_id:
            Identifier of the receiving agent.
        since:
            If provided, only return messages with a timestamp after this
            value.

        Returns
        -------
        List of matching :class:`AgentMessage` instances.
        """
        with self._lock:
            result: list[AgentMessage] = []
            for msg in self._messages:
                if msg.sender == agent_id:
                    continue
                if msg.recipient != agent_id and msg.recipient != "*":
                    continue
                if since is not None and msg.timestamp <= since:
                    continue
                result.append(msg)
        return result

    def get_conversation(
        self,
        agent_a: str,
        agent_b: str,
    ) -> list[AgentMessage]:
        """Get the conversation between two agents.

        Returns all messages where agent_a sent to agent_b or agent_b sent
        to agent_a, ordered chronologically.

        Parameters
        ----------
        agent_a:
            First agent identifier.
        agent_b:
            Second agent identifier.

        Returns
        -------
        List of :class:`AgentMessage` instances between the two agents.
        """
        with self._lock:
            return [
                msg
                for msg in self._messages
                if (msg.sender == agent_a and msg.recipient == agent_b)
                or (msg.sender == agent_b and msg.recipient == agent_a)
            ]

    def get_token_savings(self) -> dict[str, Any]:
        """Return token savings statistics.

        Estimates how many tokens were saved by using direct messaging
        instead of injecting messages into the parent context.

        Returns
        -------
        Dict with ``total_messages``, ``direct_tokens``, and
        ``context_tokens_saved`` keys.
        """
        with self._lock:
            total_messages = len(self._messages)
            direct_tokens = sum(msg.token_cost for msg in self._messages)
        context_tokens = direct_tokens * self._context_overhead_multiplier
        return {
            "total_messages": total_messages,
            "direct_tokens": direct_tokens,
            "context_tokens_saved": context_tokens - direct_tokens,
        }

    def clear(self, agent_id: str | None = None) -> None:
        """Clear messages from the bus.

        Parameters
        ----------
        agent_id:
            If provided, only clear messages sent by or addressed to this
            agent.  If ``None``, clear all messages.
        """
        with self._lock:
            if agent_id is None:
                self._messages.clear()
                logger.debug("Cleared all agent messages")
            else:
                self._messages = [msg for msg in self._messages if msg.sender != agent_id and msg.recipient != agent_id]
                logger.debug("Cleared messages for agent %s", agent_id)

    # -- private helpers -----------------------------------------------------

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Estimate token count from text length.

        Uses the rough approximation of 1 token per 4 characters, consistent
        with :meth:`ContextManager._estimate_tokens`.

        Parameters
        ----------
        text:
            The text to estimate.

        Returns
        -------
        Estimated token count (always >= 0).
        """
        if not text:
            return 0
        return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    bus = AgentCommBus()
    bus.send("planner", "coder", "Please implement the function")
    bus.send("coder", "planner", "Done, here is the result")
    bus.broadcast("reviewer", "Code review complete")

    print(f"Planner inbox: {len(bus.receive('planner'))}")
    print(f"Coder inbox: {len(bus.receive('coder'))}")
    print(f"Conversation: {len(bus.get_conversation('planner', 'coder'))}")
    print(f"Token savings: {bus.get_token_savings()}")
