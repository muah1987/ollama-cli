#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///
"""
Memory layer with token saving -- GOTCHA Tools layer, ATLAS Architect phase.

Persistent memory layer that stores facts and preferences efficiently,
summarizing and compacting to minimize token usage.  Entries are
prioritized by importance and access frequency.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MemoryEntry
# ---------------------------------------------------------------------------


@dataclass
class MemoryEntry:
    """A single memory entry stored in the memory layer.

    Parameters
    ----------
    key:
        Unique identifier for the memory.
    content:
        The memory text.
    category:
        One of ``fact``, ``preference``, ``context``, or ``learned``.
    importance:
        Priority level from 1 (low) to 5 (high).
    token_cost:
        Estimated token cost of the content.
    created_at:
        UTC timestamp of when the entry was created.
    last_accessed:
        UTC timestamp of the most recent access.
    access_count:
        Number of times the entry has been recalled.
    """

    key: str
    content: str
    category: str = "fact"
    importance: int = 3
    token_cost: int = 0
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    last_accessed: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    access_count: int = 0


# ---------------------------------------------------------------------------
# MemoryLayer
# ---------------------------------------------------------------------------


class MemoryLayer:
    """Persistent memory layer with token-efficient storage and retrieval.

    Stores facts, preferences, and context as prioritized entries.  Supports
    compaction to remove low-value memories and builds context blocks that
    fit within a token budget.

    Parameters
    ----------
    compact_threshold:
        Minimum priority score for an entry to survive compaction.  Score
        is calculated as ``importance * log2(access_count + 1)``.
    """

    def __init__(self, compact_threshold: float = 1.5) -> None:
        self._entries: dict[str, MemoryEntry] = {}
        self._compact_threshold = compact_threshold

    # -- public methods ------------------------------------------------------

    def store(
        self,
        key: str,
        content: str,
        category: str = "fact",
        importance: int = 3,
    ) -> MemoryEntry:
        """Store a memory entry.

        If an entry with the same key already exists, it is overwritten.

        Parameters
        ----------
        key:
            Unique identifier for the memory.
        content:
            The memory text.
        category:
            One of ``fact``, ``preference``, ``context``, or ``learned``.
        importance:
            Priority level from 1 (low) to 5 (high).

        Returns
        -------
        The created :class:`MemoryEntry`.
        """
        token_cost = self._estimate_tokens(content)
        entry = MemoryEntry(
            key=key,
            content=content,
            category=category,
            importance=importance,
            token_cost=token_cost,
        )
        self._entries[key] = entry
        logger.debug("Stored memory '%s' (%s, importance=%d, %d tokens)", key, category, importance, token_cost)
        return entry

    def recall(self, key: str) -> MemoryEntry | None:
        """Retrieve a specific memory by key.

        Updates the access count and last-accessed timestamp on hit.

        Parameters
        ----------
        key:
            The memory key to look up.

        Returns
        -------
        The :class:`MemoryEntry` if found, otherwise ``None``.
        """
        entry = self._entries.get(key)
        if entry is not None:
            entry.access_count += 1
            entry.last_accessed = datetime.now(tz=timezone.utc)
        return entry

    def recall_relevant(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[MemoryEntry]:
        """Find relevant memories by keyword matching.

        Matches entries whose key or content contains any word from the
        query (case-insensitive).  Results are sorted by priority score
        descending.

        Parameters
        ----------
        query:
            Search query string.
        max_results:
            Maximum number of results to return.

        Returns
        -------
        List of matching :class:`MemoryEntry` instances.
        """
        query_words = query.lower().split()
        if not query_words:
            return []

        matches: list[MemoryEntry] = []
        for entry in self._entries.values():
            searchable = f"{entry.key} {entry.content}".lower()
            if any(word in searchable for word in query_words):
                matches.append(entry)

        matches.sort(key=lambda e: self._priority_score(e), reverse=True)
        return matches[:max_results]

    def forget(self, key: str) -> bool:
        """Remove a memory entry.

        Parameters
        ----------
        key:
            The memory key to remove.

        Returns
        -------
        ``True`` if the entry existed and was removed, ``False`` otherwise.
        """
        if key in self._entries:
            del self._entries[key]
            logger.debug("Forgot memory '%s'", key)
            return True
        return False

    def compact(self) -> dict[str, int]:
        """Remove low-importance, rarely-accessed memories to save tokens.

        Entries with a priority score below the configured threshold are
        removed.

        Returns
        -------
        Dict with ``before_count``, ``after_count``, and
        ``entries_removed`` keys.
        """
        before_count = len(self._entries)
        keys_to_remove = [
            key for key, entry in self._entries.items() if self._priority_score(entry) < self._compact_threshold
        ]
        for key in keys_to_remove:
            del self._entries[key]

        after_count = len(self._entries)
        logger.info("Memory compacted: %d -> %d entries (%d removed)", before_count, after_count, len(keys_to_remove))
        return {
            "before_count": before_count,
            "after_count": after_count,
            "entries_removed": len(keys_to_remove),
        }

    def get_context_block(self, max_tokens: int = 500) -> str:
        """Build an efficient context string from stored memories.

        Entries are sorted by priority score (descending) and added to
        the context block until the token budget is exhausted.

        Parameters
        ----------
        max_tokens:
            Maximum token budget for the context block.

        Returns
        -------
        A formatted string containing the highest-priority memories that
        fit within the token budget.
        """
        sorted_entries = sorted(
            self._entries.values(),
            key=lambda e: self._priority_score(e),
            reverse=True,
        )

        lines: list[str] = []
        tokens_used = 0
        for entry in sorted_entries:
            line = f"[{entry.category}] {entry.key}: {entry.content}"
            cost = self._estimate_tokens(line)
            if tokens_used + cost > max_tokens:
                break
            lines.append(line)
            tokens_used += cost

        return "\n".join(lines)

    def get_token_savings(self) -> dict[str, Any]:
        """Return token savings statistics.

        Compares the total raw token cost of all stored entries against
        the cost of the context block that would actually be injected.

        Returns
        -------
        Dict with ``total_entries``, ``total_raw_tokens``,
        ``context_tokens_used``, and ``tokens_saved`` keys.
        """
        total_raw = sum(e.token_cost for e in self._entries.values())
        context_block = self.get_context_block()
        context_used = self._estimate_tokens(context_block)
        return {
            "total_entries": len(self._entries),
            "total_raw_tokens": total_raw,
            "context_tokens_used": context_used,
            "tokens_saved": total_raw - context_used,
        }

    def save(self, path: str) -> None:
        """Persist all memory entries to a JSON file.

        Parameters
        ----------
        path:
            File path for the JSON output.
        """
        data: list[dict[str, Any]] = []
        for entry in self._entries.values():
            data.append(
                {
                    "key": entry.key,
                    "content": entry.content,
                    "category": entry.category,
                    "importance": entry.importance,
                    "token_cost": entry.token_cost,
                    "created_at": entry.created_at.isoformat(),
                    "last_accessed": entry.last_accessed.isoformat(),
                    "access_count": entry.access_count,
                }
            )

        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Memory saved to %s (%d entries)", path, len(data))
        except OSError:
            logger.warning("Failed to save memory to %s", path, exc_info=True)

    def load(self, path: str) -> None:
        """Load memory entries from a JSON file.

        Parameters
        ----------
        path:
            File path to the JSON input.
        """
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            logger.warning("Failed to load memory from %s", path, exc_info=True)
            return

        for item in data:
            entry = MemoryEntry(
                key=item["key"],
                content=item["content"],
                category=item.get("category", "fact"),
                importance=item.get("importance", 3),
                token_cost=item.get("token_cost", 0),
                created_at=datetime.fromisoformat(item["created_at"]),
                last_accessed=datetime.fromisoformat(item["last_accessed"]),
                access_count=item.get("access_count", 0),
            )
            self._entries[entry.key] = entry

        logger.info("Memory loaded from %s (%d entries)", path, len(self._entries))

    def clear(self) -> None:
        """Clear all memory entries."""
        self._entries.clear()
        logger.debug("Cleared all memory entries")

    def get_all_entries(self) -> list[MemoryEntry]:
        """Return all stored memory entries.

        Returns
        -------
        List of all :class:`MemoryEntry` instances.
        """
        return list(self._entries.values())

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

    @staticmethod
    def _priority_score(entry: MemoryEntry) -> float:
        """Calculate the priority score for a memory entry.

        Score is ``importance * log2(access_count + 1)``.

        Parameters
        ----------
        entry:
            The memory entry to score.

        Returns
        -------
        The calculated priority score.
        """
        return entry.importance * math.log2(entry.access_count + 1)


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ml = MemoryLayer()
    ml.store("python_version", "Project uses Python 3.11+", category="fact", importance=5)
    ml.store("user_pref", "User prefers dark theme", category="preference", importance=2)
    ml.store("api_endpoint", "Main API at /v1/chat", category="context", importance=4)

    # Recall to boost access count
    ml.recall("python_version")
    ml.recall("python_version")

    print(f"Context block:\n{ml.get_context_block()}")
    print(f"\nToken savings: {ml.get_token_savings()}")
    print(f"Relevant to 'python': {[e.key for e in ml.recall_relevant('python')]}")
