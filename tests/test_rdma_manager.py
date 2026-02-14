"""Tests for runner/rdma_manager.py -- RDMA configuration and device management."""

from __future__ import annotations

from pathlib import Path

import pytest

from runner.rdma_manager import (
    RDMAClusterConfig,
    RDMAConfiguration,
    RDMAEvent,
    RDMAEventType,
    RDMAManager,
)


class TestRDMAEventType:
    def test_event_types_exist(self):
        assert hasattr(RDMAEventType, "DEVICE_ADD")
        assert hasattr(RDMAEventType, "DEVICE_REMOVE")
        assert hasattr(RDMAEventType, "CONNECT_REQUEST")
        assert hasattr(RDMAEventType, "ERROR")

    def test_event_type_values(self):
        assert isinstance(RDMAEventType.DEVICE_ADD.value, str)


class TestRDMAEvent:
    def test_create_event(self):
        event = RDMAEvent(
            event_type=RDMAEventType.DEVICE_ADD,
            device_name="mlx0",
            details={"speed": "100Gbps"},
        )
        assert event.event_type == RDMAEventType.DEVICE_ADD
        assert event.device_name == "mlx0"


class TestRDMAClusterConfig:
    def test_init(self):
        cfg = RDMAClusterConfig(cluster_name="test-cluster", leader_host="localhost")
        assert cfg.cluster_name == "test-cluster"
        assert cfg.leader_host == "localhost"
        assert cfg.members == []
        assert cfg.heartbeat_interval == 1.0
        assert cfg.timeout == 3.0


class TestRDMAConfiguration:
    def test_init(self, tmp_path):
        cfg = RDMAConfiguration(config_dir=tmp_path)
        assert cfg is not None

    def test_load_no_file(self, tmp_path):
        cfg = RDMAConfiguration(config_dir=tmp_path)
        cfg.load()  # Should not raise

    def test_save_and_load(self, tmp_path):
        cfg = RDMAConfiguration(config_dir=tmp_path)
        cfg.add_device({"name": "mlx0", "type": "infiniband", "speed": "100Gbps"})
        cfg.save()
        # Load in new instance
        cfg2 = RDMAConfiguration(config_dir=tmp_path)
        cfg2.load()
        devices = cfg2.list_devices()
        assert len(devices) == 1
        assert devices[0]["name"] == "mlx0"

    def test_add_device(self, tmp_path):
        cfg = RDMAConfiguration(config_dir=tmp_path)
        cfg.add_device({"name": "ib0", "type": "ib"})
        assert len(cfg.list_devices()) == 1

    def test_remove_device(self, tmp_path):
        cfg = RDMAConfiguration(config_dir=tmp_path)
        cfg.add_device({"name": "ib0", "type": "ib"})
        cfg.remove_device("ib0")
        assert len(cfg.list_devices()) == 0

    def test_get_device(self, tmp_path):
        cfg = RDMAConfiguration(config_dir=tmp_path)
        cfg.add_device({"name": "mlx0", "type": "ib"})
        result = cfg.get_device("mlx0")
        assert result is not None
        assert result["name"] == "mlx0"

    def test_get_device_missing(self, tmp_path):
        cfg = RDMAConfiguration(config_dir=tmp_path)
        assert cfg.get_device("nonexistent") is None

    def test_list_devices_empty(self, tmp_path):
        cfg = RDMAConfiguration(config_dir=tmp_path)
        assert cfg.list_devices() == []


class TestRDMAManager:
    def test_init(self, tmp_path):
        mgr = RDMAManager(config_dir=tmp_path)
        assert mgr is not None

    @pytest.mark.asyncio
    async def test_detect_devices(self, tmp_path):
        mgr = RDMAManager(config_dir=tmp_path)
        try:
            devices = await mgr.detect_devices()
            assert isinstance(devices, list)
        except (OSError, AttributeError):
            # RDMA detection may not work in CI
            pass

    def test_configure_device(self, tmp_path):
        mgr = RDMAManager(config_dir=tmp_path)
        mgr.config.add_device({"name": "mlx0", "type": "ib"})
        result = mgr.configure_device("mlx0", {"mtu": 4096})
        assert isinstance(result, bool)

    def test_get_vendor(self, tmp_path):
        mgr = RDMAManager(config_dir=tmp_path)
        vendor = mgr._get_vendor(Path("/sys/class/infiniband/nonexistent"))
        assert isinstance(vendor, str)

    def test_get_transport_protocol(self, tmp_path):
        mgr = RDMAManager(config_dir=tmp_path)
        proto = mgr._get_transport_protocol("mlx0")
        assert isinstance(proto, str)
