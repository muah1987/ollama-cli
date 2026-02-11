#!/usr/bin/env python3
"""
Skills framework for the Ollama CLI project.

This module provides a base class for creating reusable skills that can
leverage the enhanced token counting and context management systems.
"""

import json
import logging

# Handle both when run as standalone and when imported
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

try:
    from context_manager import ContextManager
    from token_counter import TokenCounter
except ImportError:
    from runner.context_manager import ContextManager
    from runner.token_counter import TokenCounter

logger = logging.getLogger(__name__)


class BaseSkill(ABC):
    """Base class for all skills in the Ollama CLI project."""

    def __init__(self, name: str, description: str, context_manager: Optional[ContextManager] = None):
        self.name = name
        self.description = description
        self.context_manager = context_manager or ContextManager(context_id=f"skill_{name}")
        self.token_counter = TokenCounter(provider="ollama")

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the skill with the given parameters.

        Args:
            **kwargs: Skill-specific parameters

        Returns:
            Dictionary containing the result of the skill execution
        """
        pass

    def update_context(self, messages: List[Dict[str, str]]) -> None:
        """Update the context with a list of messages.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
        """
        for message in messages:
            self.context_manager.add_message(role=message["role"], content=message["content"])

    def get_token_usage(self) -> Dict[str, Any]:
        """Get current token usage statistics.

        Returns:
            Dictionary with token usage information
        """
        return self.token_counter.format_json()

    def should_compact(self) -> bool:
        """Check if context should be compacted.

        Returns:
            True if context usage exceeds compaction threshold
        """
        return self.context_manager.should_compact()

    async def compact_context(self) -> Dict[str, int]:
        """Compact the context to reduce token usage.

        Returns:
            Dictionary with compaction statistics
        """
        return await self.context_manager.compact()


class TokenCountingSkill(BaseSkill):
    """Skill for advanced token counting and analysis."""

    def __init__(self, context_manager: Optional[ContextManager] = None):
        super().__init__(
            name="token_counter", description="Advanced token counting and analysis", context_manager=context_manager
        )

    async def execute(self, text: str, provider: str = "ollama") -> Dict[str, Any]:
        """Count tokens in the provided text using the specified provider.

        Args:
            text: Text to count tokens for
            provider: Provider to use for token counting

        Returns:
            Dictionary with token count and cost estimation
        """
        # Update the token counter provider
        self.token_counter = TokenCounter(provider=provider)

        # Estimate tokens using the context manager's method
        token_count = self.context_manager._estimate_tokens(text)

        # Update context with the text
        self.context_manager.add_message("user", f"Token counting request for: {text[:50]}...")
        self.context_manager.add_message("assistant", f"Estimated token count: {token_count}")

        # Update token counter with dummy metrics for demonstration
        self.token_counter.update({"prompt_eval_count": token_count, "eval_count": 1, "eval_duration": 1000000000})

        return {
            "text": text,
            "token_count": token_count,
            "provider": provider,
            "cost_estimate": self.token_counter.cost_estimate,
            "metrics": self.token_counter.format_json(),
        }


class AutoCompactSkill(BaseSkill):
    """Skill for managing auto-compaction of context."""

    def __init__(self, context_manager: Optional[ContextManager] = None):
        super().__init__(
            name="auto_compact", description="Context auto-compaction management", context_manager=context_manager
        )

    async def execute(
        self, action: str = "check", threshold: Optional[float] = None, keep_last_n: Optional[int] = None
    ) -> Dict[str, Any]:
        """Manage auto-compaction settings and execution.

        Args:
            action: Action to perform ('check', 'compact', 'configure')
            threshold: New compaction threshold (0.0-1.0)
            keep_last_n: Number of recent messages to preserve

        Returns:
            Dictionary with action results
        """
        result = {"action": action}

        if action == "check":
            usage = self.context_manager.get_context_usage()
            result.update(
                {
                    "context_usage": usage,
                    "should_compact": self.context_manager.should_compact(),
                    "total_tokens": self.context_manager.get_total_context_tokens(),
                }
            )

        elif action == "compact":
            if self.context_manager.should_compact():
                compact_result = await self.context_manager.compact()
                result.update(
                    {
                        "compacted": True,
                        "compact_result": compact_result,
                        "new_usage": self.context_manager.get_context_usage(),
                    }
                )
            else:
                result["compacted"] = False
                result["reason"] = "Context usage below compaction threshold"

        elif action == "configure":
            if threshold is not None:
                self.context_manager.compact_threshold = threshold
            if keep_last_n is not None:
                self.context_manager.keep_last_n = keep_last_n

            result.update(
                {
                    "configured": True,
                    "threshold": self.context_manager.compact_threshold,
                    "keep_last_n": self.context_manager.keep_last_n,
                }
            )

        # Add messages to context
        self.context_manager.add_message("user", f"Auto-compact {action} request")
        self.context_manager.add_message("assistant", json.dumps(result))

        return result


# Skill registry
SKILLS = {
    "token_counter": TokenCountingSkill,
    "auto_compact": AutoCompactSkill,
    "mlx_acceleration": None,  # Dynamic import from skills.mlx
    "exo_execution": None,  # Dynamic import from skills.exo
    "rdma_acceleration": None,  # Dynamic import from skills.rdma
}


def get_skill(skill_name: str, context_manager: Optional[ContextManager] = None) -> BaseSkill:
    """Get a skill instance by name.

    Args:
        skill_name: Name of the skill to instantiate
        context_manager: Optional context manager to use

    Returns:
        Instance of the requested skill

    Raises:
        ValueError: If the skill name is not recognized
    """
    # Handle dynamic imports for new skills
    if skill_name == "mlx_acceleration":
        from skills.mlx import MLXSkill

        return MLXSkill()
    elif skill_name == "exo_execution":
        from skills.exo import EXOSkill

        return EXOSkill()
    elif skill_name == "rdma_acceleration":
        from skills.rdma import RDMA_skill

        return RDMA_skill()

    if skill_name not in SKILLS:
        raise ValueError(f"Unknown skill: {skill_name}")

    skill_class = SKILLS[skill_name]
    return skill_class(context_manager)


async def execute_skill(skill_name: str, context_manager: Optional[ContextManager] = None, **kwargs) -> Dict[str, Any]:
    """Execute a skill by name with the given parameters.

    Args:
        skill_name: Name of the skill to execute
        context_manager: Optional context manager to use
        **kwargs: Skill-specific parameters

    Returns:
        Result of the skill execution
    """
    skill = get_skill(skill_name, context_manager)
    return await skill.execute(**kwargs)


if __name__ == "__main__":
    # Example usage
    import asyncio

    async def demo():
        # Create a context manager
        cm = ContextManager(context_id="demo")

        # Execute token counting skill
        result = await execute_skill("token_counter", cm, text="Hello, world!", provider="claude")
        print("Token counting result:", result)

        # Execute auto-compact skill
        result = await execute_skill("auto_compact", cm, action="check")
        print("Auto-compact check result:", result)

    asyncio.run(demo())
