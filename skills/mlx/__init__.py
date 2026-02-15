"""MLX (Metal Performance Shaders) integration for Apple Silicon acceleration.

This module provides Apple Metal GPU acceleration for Qarin CLI operations
on macOS with Apple Silicon chips.
"""

from __future__ import annotations

import logging
import os
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class MLXAccelerator:
    """Apple Metal GPU accelerator via MLX framework."""

    def __init__(self):
        self._initialized = False
        self._device_info: dict[str, Any] | None = None

    async def initialize(self) -> bool:
        """Initialize MLX acceleration."""
        if os.uname().system != "Darwin":
            logger.warning("MLX acceleration is only available on macOS")
            return False

        try:
            # Check for Metal availability
            result = subprocess.run(
                ["system_profiler", "SPGPUDataType"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                metal_info = result.stdout.lower()
                has_metal = "metal" in metal_info or "apple" in metal_info

                if has_metal:
                    self._device_info = {
                        "type": "apple_silicon",
                        "cores": self._get_gpu_cores(),
                        "memory": self._get_gpu_memory(),
                        "supports_mlx": True,
                    }
                    self._initialized = True
                    logger.info("MLX acceleration initialized")
                    return True
        except Exception as e:
            logger.warning("MLX initialization failed: %s", e)

        return False

    def _get_gpu_cores(self) -> int:
        """Get number of GPUcores."""
        try:
            result = subprocess.run(
                ["system_profiler", "SPGPUDataType"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.split("\n"):
                if "cores" in line.lower():
                    try:
                        return int("".join(filter(str.isdigit, line)))
                    except ValueError:
                        pass
        except Exception:
            pass
        return 0

    def _get_gpu_memory(self) -> int:
        """Get GPU memory in bytes."""
        try:
            result = subprocess.run(
                ["system_profiler", "SPGPUDataType"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            for line in result.stdout.split("\n"):
                if "shared" in line.lower() or "memory" in line.lower():
                    # Parse memory info
                    pass
        except Exception:
            pass
        return 0

    @property
    def is_available(self) -> bool:
        """Check if MLX acceleration is available."""
        return self._initialized

    @property
    def device_info(self) -> dict[str, Any]:
        """Get device information."""
        return self._device_info or {}


class MLXSkill:
    """Skill for MLX acceleration management."""

    name = "mlx_acceleration"
    description = "Apple Metal GPU acceleration via MLX framework"

    def __init__(self):
        self.accelerator = MLXAccelerator()

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute MLX acceleration skill.

        Args:
            action: Action to perform ('check', 'enable', 'disable')
            **kwargs: Additional arguments

        Returns:
            Result dictionary with action outcome
        """
        action = kwargs.get("action", "check")
        result: dict[str, Any] = {"action": action}

        if action == "check":
            await self.accelerator.initialize()
            result.update(
                {
                    "available": self.accelerator.is_available,
                    "device_info": self.accelerator.device_info,
                }
            )
        elif action == "enable":
            success = await self.accelerator.initialize()
            result.update(
                {
                    "enabled": success,
                }
            )
        elif action == "disable":
            self.accelerator._initialized = False
            self.accelerator._device_info = None
            result.update(
                {
                    "disabled": True,
                }
            )

        return result

    def should_accelerate(self, task_type: str) -> bool:
        """Determine if a task should use MLX acceleration."""
        if not self.accelerator.is_available:
            return False

        # Accelerate inference and embedding tasks
        accelerate_types = ["inference", "embedding", "generation"]
        return task_type in accelerate_types


__all__ = ["MLXAccelerator", "MLXSkill"]
