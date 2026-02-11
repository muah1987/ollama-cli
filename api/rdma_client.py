"""RDMA Client module for high-performance networking.

This module provides a client for Remote Direct Memory Access (RDMA) operations,
supporting multiple transport protocols: InfiniBand, RoCE (RDMA over Converged Ethernet),
iWARP (internet Wide Area RDMA Protocol), and TCP/IP fallback.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class TransportProtocol(Enum):
    """Supported RDMA transport protocols."""

    INFINIBAND = "infiniband"
    ROCETH = "roce"  # RoCE v1
    ROCEV2 = "roce_v2"  # RoCE v2
    IWARP = "iwarp"
    TCP = "tcp"  # Fallback


class DeviceType(Enum):
    """RDMA device types."""

    PHYSICAL = "physical"
    VIRTUAL = "virtual"
    USB_RDMA = "usb_rdma"
    THUNDERBOLT_RDMA = "thunderbolt_rdma"
    NETWORK_RDMA = "network_rdma"


@dataclass
class RDMADeviceInfo:
    """Information about an RDMA device."""

    name: str
    device_type: DeviceType
    transport: TransportProtocol
    node_guid: str
    system_image_guid: str
    max_qp: int
    max_mr: int
    mtu: int
    vendor_id: str
    vendor_part_id: int


@dataclass
class RDMAConnectionConfig:
    """Configuration for an RDMA connection."""

    local_port: int
    remote_host: str
    remote_port: int
    qp_type: str = "RC"  # Reliable Connected
    mtu: int = 4096
    max_inline_data: int = 256
    retry_count: int = 7
    rnr_retry: int = 7
    timeout: int = 14  # 4.096 * 2^14 microseconds


class RDMAError(Exception):
    """Base exception for RDMA errors."""


class RDMAConnectionError(RDMAError):
    """Raised whenRDMA connection fails."""


class RDMATransport:
    """Abstract base class for RDMA transports."""

    name: str = ""

    async def connect(self, config: RDMAConnectionConfig) -> None:
        """Establish an RDMA connection."""
        raise NotImplementedError

    async def disconnect(self) -> None:
        """Close the RDMA connection."""
        raise NotImplementedError

    async def send(self, data: bytes) -> int:
        """Send data over RDMA."""
        raise NotImplementedError

    async def receive(self, size: int) -> bytes:
        """Receive data over RDMA."""
        raise NotImplementedError


class RDMAClient:
    """High-performance RDMA client with multiple transport support."""

    def __init__(self, transport: RDMATransport | None = None):
        self._transport = transport
        self._connected = False
        self._config: RDMAConnectionConfig | None = None

    async def connect(self, config: RDMAConnectionConfig) -> None:
        """Connect to an RDMA endpoint."""
        if self._transport is None:
            raise RDMAError("No transport configured")

        self._config = config
        await self._transport.connect(config)
        self._connected = True
        logger.info("RDMA connection established to %s:%d", config.remote_host, config.remote_port)

    async def disconnect(self) -> None:
        """Disconnect from RDMA endpoint."""
        if self._transport and self._connected:
            await self._transport.disconnect()
            self._connected = False
            logger.info("RDMA connection closed")

    async def send(self, data: bytes) -> int:
        """Send data."""
        if not self._connected:
            raise RDMAConnectionError("Not connected")
        return await self._transport.send(data)

    async def receive(self, size: int) -> bytes:
        """Receive data."""
        if not self._connected:
            raise RDMAConnectionError("Not connected")
        return await self._transport.receive(size)

    @property
    def is_connected(self) -> bool:
        """Check if connected."""
        return self._connected


# Device detection functions
async def detect_rdma_devices() -> list[RDMADeviceInfo]:
    """Detect available RDMA devices on the system."""
    devices: list[RDMADeviceInfo] = []

    # Check for USB<>RDMA devices
    usb_devices = await _detect_usb_rdma()
    devices.extend(usb_devices)

    # Check for Thunderbolt<>RDMA devices
    thunderbolt_devices = await _detect_thunderbolt_rdma()
    devices.extend(thunderbolt_devices)

    # Check for Network<>RDMA devices (RoCE, iWARP)
    network_devices = await _detect_network_rdma()
    devices.extend(network_devices)

    return devices


async def _detect_usb_rdma() -> list[RDMADeviceInfo]:
    """Detect USB<>RDMA devices."""
    devices = []
    # TODO: Implement USB<>RDMA detection
    # This would scan USB devices and identify RDMA-capable devices
    return devices


async def _detect_thunderbolt_rdma() -> list[RDMADeviceInfo]:
    """Detect Thunderbolt<>RDMA devices."""
    devices = []
    # TODO: Implement Thunderbolt<>RDMA detection
    # This would scan Thunderbolt devices and identify RDMA-capable devices
    return devices


async def _detect_network_rdma() -> list[RDMADeviceInfo]:
    """Detect Network<>RDMA devices (RoCE, iWARP)."""
    devices = []
    # TODO: Implement Network<>RDMA detection
    # This would scan network interfaces for RDMA capability
    return devices


def get_rdma_device_type(device_name: str) -> DeviceType:
    """Determine the device type from device name."""
    name_lower = device_name.lower()

    if "usb" in name_lower:
        return DeviceType.USB_RDMA
    elif "thunderbolt" in name_lower or "tb" in name_lower:
        return DeviceType.THUNDERBOLT_RDMA
    elif "roce" in name_lower or "mlx" in name_lower:
        return DeviceType.NETWORK_RDMA
    elif "iw" in name_lower:
        return DeviceType.NETWORK_RDMA
    else:
        return DeviceType.PHYSICAL


def get_transport_protocol(device_type: DeviceType, device_name: str) -> TransportProtocol:
    """Determine the transport protocol based on device type and name."""
    name_lower = device_name.lower()

    if device_type == DeviceType.USB_RDMA:
        return TransportProtocol.TCP
    elif device_type == DeviceType.THUNDERBOLT_RDMA:
        return TransportProtocol.ROCEV2
    elif "infini" in name_lower or "mlx" in name_lower:
        return TransportProtocol.INFINIBAND
    elif "roce" in name_lower:
        if "v2" in name_lower:
            return TransportProtocol.ROCEV2
        return TransportProtocol.ROCETH
    elif "iw" in name_lower:
        return TransportProtocol.IWARP
    else:
        return TransportProtocol.TCP


__all__ = [
    "RDMAError",
    "RDMAConnectionError",
    "RDMADeviceInfo",
    "RDMAConnectionConfig",
    "RDMATransport",
    "RDMAClient",
    "TransportProtocol",
    "DeviceType",
    "detect_rdma_devices",
    "get_rdma_device_type",
    "get_transport_protocol",
]
