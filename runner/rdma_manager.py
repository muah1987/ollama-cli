"""RDMA Manager module for configuring and managing RDMA devices.

This module provides automatic device detection, configuration management,
and connection handling for RDMA-based high-performance computing.
"""

from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RDMAEventType(Enum):
    """Types of RDMA events."""
    DEVICE_ADD = "device_add"
    DEVICE_REMOVE = "device_remove"
    CONNECT_REQUEST = "connect_request"
    CONNECT_RESPONSE = "connect_response"
    DISCONNECT = "disconnect"
    ERROR = "error"


@dataclass
class RDMAEvent:
    """An RDMA event."""
    event_type: RDMAEventType
    device_name: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class RDMAClusterConfig:
    """Configuration for an RDMA cluster."""
    cluster_name: str
    leader_host: str
    members: list[str] = field(default_factory=list)
    heartbeat_interval: float = 1.0
    timeout: float = 3.0


class RDMAConfiguration:
    """Manages RDMA device configuration."""

    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or Path.home() / ".ollama" / "rdma"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._loaded = False
        self._devices: list[dict[str, Any]] = []

    def load(self) -> None:
        """Load configuration from disk."""
        config_file = self.config_dir / "config.json"
        if config_file.exists():
            import json
            try:
                with open(config_file) as f:
                    self._devices = json.load(f)
                self._loaded = True
                logger.info("Loaded RDMA configuration from %s", config_file)
            except Exception as e:
                logger.warning("Failed to load configuration: %s", e)
        self._loaded = True

    def save(self) -> None:
        """Save configuration to disk."""
        import json
        config_file = self.config_dir / "config.json"
        with open(config_file, "w") as f:
            json.dump(self._devices, f, indent=2)
        logger.info("Saved RDMA configuration to %s", config_file)

    def add_device(self, device: dict[str, Any]) -> None:
        """Add a device to the configuration."""
        if not self._loaded:
            self.load()
        self._devices.append(device)
        self.save()

    def remove_device(self, device_name: str) -> None:
        """Remove a device from the configuration."""
        if not self._loaded:
            self.load()
        self._devices = [d for d in self._devices if d.get("name") != device_name]
        self.save()

    def get_device(self, device_name: str) -> dict[str, Any] | None:
        """Get configuration for a specific device."""
        if not self._loaded:
            self.load()
        for device in self._devices:
            if device.get("name") == device_name:
                return device
        return None

    def list_devices(self) -> list[dict[str, Any]]:
        """List all configured devices."""
        if not self._loaded:
            self.load()
        return list(self._devices)


class RDMAManager:
    """Manages RDMA devices and connections."""

    def __init__(self, config_dir: Path | None = None):
        self.config = RDMAConfiguration(config_dir)
        self._connected = False
        self._cluster_config: RDMAClusterConfig | None = None

    async def detect_devices(self) -> list[dict[str, Any]]:
        """Detect all available RDMA devices."""
        devices = []

        # Detect USB<>RDMA devices
        usb_devices = await self._detect_usb_rdma()
        devices.extend(usb_devices)

        # Detect Thunderbolt<>RDMA devices
        tb_devices = await self._detect_thunderbolt_rdma()
        devices.extend(tb_devices)

        # Detect Network<>RDMA devices
        network_devices = await self._detect_network_rdma()
        devices.extend(network_devices)

        # Save to configuration
        for device in devices:
            self.config.add_device(device)

        logger.info("Detected %d RDMA devices", len(devices))
        return devices

    async def _detect_usb_rdma(self) -> list[dict[str, Any]]:
        """Detect USB<>RDMA devices."""
        devices = []
        try:
            # Check lsusb for RDMA devices
            result = subprocess.run(
                ["lsusb", "-v"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                # Parse lsusb output for RDMA devices
                # This is a simplified implementation
                for line in result.stdout.split("\n"):
                    if "RDMA" in line or "InfiniBand" in line:
                        devices.append({
                            "name": line.strip(),
                            "type": "usb_rdma",
                            "transport": "tcp",
                            "vendor": "unknown",
                        })
        except Exception as e:
            logger.warning("USB RDMA detection failed: %s", e)
        return devices

    async def _detect_thunderbolt_rdma(self) -> list[dict[str, Any]]:
        """Detect Thunderbolt<>RDMA devices."""
        devices = []
        platform = os.uname().system

        try:
            if platform == "Linux":
                # Check /sys/class/infiniband/ for devices
                ib_path = Path("/sys/class/infiniband")
                if ib_path.exists():
                    for device_dir in ib_path.iterdir():
                        if device_dir.is_dir():
                            devices.append({
                                "name": device_dir.name,
                                "type": "thunderbolt_rdma",
                                "transport": "roce_v2",
                                "vendor": self._get_vendor(device_dir),
                            })
            elif platform == "Darwin":
                # Check for Thunderbolt devices on macOS
                result = subprocess.run(
                    ["system_profiler", "SPThunderboltDataType"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    devices.append({
                        "name": "Thunderbolt RDMA",
                        "type": "thunderbolt_rdma",
                        "transport": "roce_v2",
                        "vendor": "Apple",
                    })
        except Exception as e:
            logger.warning("Thunderbolt RDMA detection failed: %s", e)

        return devices

    async def _detect_network_rdma(self) -> list[dict[str, Any]]:
        """Detect Network<>RDMA devices (RoCE, iWARP)."""
        devices = []
        try:
            # Check for RDMA-capable network interfaces
            result = subprocess.run(
                ["rdma", "link", "show"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.strip():
                        parts = line.split()
                        if parts:
                            devices.append({
                                "name": parts[0].rstrip(":"),
                                "type": "network_rdma",
                                "transport": self._get_transport_protocol(parts[0]),
                                "vendor": "unknown",
                            })
        except Exception as e:
            logger.warning("Network RDMA detection failed: %s", e)

        return devices

    def _get_vendor(self, device_dir: Path) -> str:
        """Get vendor name from device directory."""
        vendor_file = device_dir / "device" / "vendor"
        if vendor_file.exists():
            try:
                with open(vendor_file) as f:
                    vendor_id = f.read().strip()
                    #_map vendor IDs
                    vendor_map = {
                        "0x02c9": "Mellanox",
                        "0x05ad": "Intel",
                        "0x10df": "Cisco",
                        "0x15b3": "Mellanox",
                    }
                    return vendor_map.get(vendor_id, vendor_id)
            except Exception:
                pass
        return "unknown"

    def _get_transport_protocol(self, device_name: str) -> str:
        """Determine transport protocol from device name."""
        name_lower = device_name.lower()

        if "roce" in name_lower:
            if "v2" in name_lower:
                return "roce_v2"
            return "roce"
        elif "iw" in name_lower:
            return "iwarp"
        elif "mlx" in name_lower:
            return "roce_v2"
        else:
            return "roce_v2"

    def configure_device(self, device_name: str, config: dict[str, Any]) -> bool:
        """Configure a specific RDMA device."""
        device_info = self.config.get_device(device_name)
        if not device_info:
            logger.error("Device %s not found", device_name)
            return False

        device_info.update(config)
        self.config.save()
        logger.info("Configured device %s", device_name)
        return True

    async def connect_cluster(self, config: RDMAClusterConfig) -> bool:
        """Connect to an RDMA cluster."""
        self._cluster_config = config
        logger.info("Connecting to cluster %s (leader: %s)",
                    config.cluster_name, config.leader_host)
        self._connected = True
        return True

    async def disconnect_cluster(self) -> None:
        """Disconnect from RDMA cluster."""
        self._connected = False
        self._cluster_config = None
        logger.info("Disconnected from cluster")

    @property
    def is_connected(self) -> bool:
        """Check if connected to a cluster."""
        return self._connected


__all__ = [
    "RDMAEventType",
    "RDMAEvent",
    "RDMAClusterConfig",
    "RDMAConfiguration",
    "RDMAManager",
]
