"""vLLM integration for high-throughput inference with tensor parallelism.

This module provides management and health-checking of a vLLM inference
server.  vLLM supports tensor parallelism across multiple GPUs via
``--tensor-parallel-size N``, enabling distributed inference for large models.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class VllmServer:
    """Manager for a vLLM inference server with tensor parallelism support."""

    def __init__(self, host: str | None = None) -> None:
        self._host = host or os.environ.get("VLLM_HOST", "http://localhost:8000")
        self._tensor_parallel_size = int(os.environ.get("VLLM_TENSOR_PARALLEL_SIZE", "1"))
        self._initialized = False
        self._server_info: dict[str, Any] = {}

    async def check(self) -> dict[str, Any]:
        """Check if vLLM server is reachable and gather info."""
        import httpx

        info: dict[str, Any] = {
            "host": self._host,
            "tensor_parallel_size": self._tensor_parallel_size,
        }

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                resp = await client.get(f"{self._host}/health")
                info["server_running"] = resp.status_code == 200
                if resp.status_code == 200:
                    self._initialized = True
        except (httpx.ConnectError, httpx.TimeoutException):
            info["server_running"] = False

        # Try to get model info
        if info.get("server_running"):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as client:
                    resp = await client.get(f"{self._host}/v1/models")
                    if resp.status_code == 200:
                        data = resp.json()
                        models = data.get("data", [])
                        info["models"] = [m.get("id", "") for m in models if isinstance(m, dict)]
            except Exception:
                info["models"] = []

        self._server_info = info
        return info

    @property
    def is_available(self) -> bool:
        """Check if vLLM server is available."""
        return self._initialized

    @property
    def tensor_parallel_size(self) -> int:
        """Number of GPUs used for tensor parallelism."""
        return self._tensor_parallel_size


class VllmSkill:
    """Skill for vLLM server management with tensor parallelism support."""

    name = "vllm"
    description = "High-throughput inference with tensor parallelism via vLLM"

    def __init__(self) -> None:
        self.server = VllmServer()

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute vLLM skill.

        Args:
            action: Action to perform ('check', 'info')
            **kwargs: Additional arguments

        Returns:
            Result dictionary with action outcome
        """
        action = kwargs.get("action", "check")
        result: dict[str, Any] = {"action": action, "skill": self.name}

        if action == "check":
            info = await self.server.check()
            result.update(info)
        elif action == "info":
            result.update({
                "description": self.description,
                "features": [
                    "tensor_parallelism",
                    "continuous_batching",
                    "paged_attention",
                    "speculative_decoding",
                ],
                "tensor_parallel_size": self.server.tensor_parallel_size,
                "available": self.server.is_available,
            })

        return result


__all__ = ["VllmServer", "VllmSkill"]
