"""llama.cpp integration for lightweight, cross-platform local inference.

This module provides management and health-checking of a local llama.cpp
server (``llama-server``).  llama.cpp supports CPU, CUDA, Metal, and Vulkan
backends, making it available on Linux, macOS, and Windows.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
from typing import Any

logger = logging.getLogger(__name__)


class LlamaCppServer:
    """Manager for a local llama.cpp inference server."""

    def __init__(self, host: str | None = None) -> None:
        self._host = host or os.environ.get("LLAMACPP_HOST", "http://localhost:8080")
        self._binary = os.environ.get("LLAMACPP_BIN", "llama-server")
        self._initialized = False
        self._server_info: dict[str, Any] = {}

    async def check(self) -> dict[str, Any]:
        """Check if llama.cpp server is reachable and gather info."""
        import httpx

        info: dict[str, Any] = {
            "host": self._host,
            "binary_found": shutil.which(self._binary) is not None,
            "platform": platform.system(),
            "arch": platform.machine(),
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
        """Check if llama.cpp server is available."""
        return self._initialized


class LlamaCppSkill:
    """Skill for llama.cpp server management and status checking."""

    name = "llamacpp"
    description = "Lightweight cross-platform inference via llama.cpp (CPU/CUDA/Metal/Vulkan)"

    def __init__(self) -> None:
        self.server = LlamaCppServer()

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute llama.cpp skill.

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
                "supported_backends": ["cpu", "cuda", "metal", "vulkan"],
                "platforms": ["linux", "macos", "windows"],
                "available": self.server.is_available,
            })

        return result


__all__ = ["LlamaCppServer", "LlamaCppSkill"]
