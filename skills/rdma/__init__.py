"""RDMA (Remote Direct Memory Access) skill for high-performance networking.

This module provides RDMA-based networking acceleration for Ollama CLI operations,
enabling low-latency, high-throughput communication between nodes.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class RDMAAccelerator:
    """RDMA network accelerator for high-performance communication."""

    def __init__(self):
        self._devices: list[dict[str, Any]] = []
        self._connected = False
        self._connected_device: str | None = None

    async def initialize(self) -> bool:
        """Initialize RDMA devices."""
        self._devices = await self._detect_devices()
        self._connected = len(self._devices) > 0
        logger.info("RDMA initialized with %d devices", len(self._devices))
        return self._connected

    async def _detect_devices(self) -> list[dict[str, Any]]:
        """Detect RDMA devices."""
        devices = []

        try:
            # Try rdma tool
            result = subprocess.run(
                ["rdma", "link", "show"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.strip():
                        name = line.split()[0].rstrip(":")
                        devices.append(
                            {
                                "name": name,
                                "type": "network_rdma",
                                "status": "available",
                            }
                        )

            # Check for InfiniBand devices
            ib_path = "/sys/class/infiniband"
            import os

            if os.path.exists(ib_path):
                for item in os.listdir(ib_path):
                    if os.path.isdir(os.path.join(ib_path, item)):
                        devices.append(
                            {
                                "name": item,
                                "type": "infiniband",
                                "status": "available",
                            }
                        )
        except Exception as e:
            logger.warning("RDMA detection failed: %s", e)

        return devices

    async def connect_device(self, device_name: str) -> bool:
        """Connect to a specific RDMA device."""
        if not self._connected:
            await self.initialize()

        for device in self._devices:
            if device["name"] == device_name:
                self._connected_device = device_name
                self._connected = True
                logger.info("Connected to RDMA device %s", device_name)
                return True

        logger.error("Device %s not found", device_name)
        return False

    async def disconnect(self) -> None:
        """Disconnect from RDMA device."""
        self._connected = False
        self._connected_device = None
        logger.info("Disconnected from RDMA device")

    def get_device(self, device_name: str) -> dict[str, Any] | None:
        """Get device information."""
        for device in self._devices:
            if device["name"] == device_name:
                return device
        return None

    @property
    def is_connected(self) -> bool:
        """Check if connected to an RDMA device."""
        return self._connected

    @property
    def connected_device(self) -> str | None:
        """Get the currently connected device name."""
        return self._connected_device

    @property
    def devices(self) -> list[dict[str, Any]]:
        """Get all detected devices."""
        return self._devices


class RDMA_skill:
    """Skill for RDMA network acceleration."""

    name = "rdma_acceleration"
    description = "RDMA network acceleration for high-performance communication"

    def __init__(self):
        self.accelerator = RDMAAccelerator()

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute RDMA skill.

        Args:
            action: Action to perform ('check', 'connect', 'disconnect')
            device: Device name for connection operations
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
                    "initialized": self.accelerator.is_connected,
                    "device_count": len(self.accelerator.devices),
                    "devices": self.accelerator.devices,
                }
            )
        elif action == "connect":
            device = kwargs.get("device")
            if not device:
                result.update({"error": "Device name required for connect action"})
            else:
                success = await self.accelerator.connect_device(device)
                result.update(
                    {
                        "connected": success,
                        "device": device,
                    }
                )
        elif action == "disconnect":
            await self.accelerator.disconnect()
            result.update(
                {
                    "disconnected": True,
                }
            )
        elif action == "status":
            await self.accelerator.initialize()
            result.update(
                {
                    "connected": self.accelerator.is_connected,
                    "device": self.accelerator.connected_device,
                }
            )

        return result

    async def benchmark_bandwidth(self, dest_host: str, size: int = 1048576) -> dict[str, Any]:
        """Benchmark RDMA bandwidth to a destination host."""
        if not self.accelerator.is_connected:
            await self.accelerator.initialize()

        result = {
            "dest_host": dest_host,
            "size_bytes": size,
            "bandwidth_gbps": 0.0,
            "latency_us": 0.0,
        }

        # TODO: Implement actual bandwidth benchmark
        # This would use RDMA send/receive operations
        return result


__all__ = ["RDMAAccelerator", "RDMA_skill"]
