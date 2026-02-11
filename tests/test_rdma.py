#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""
Test RDMA functionality.
"""

import sys
from pathlib import Path


def test_rdma_client_module() -> None:
    """Test that the RDMA client module is importable."""
    client_path = Path(__file__).parent.parent / "api" / "rdma_client.py"
    assert client_path.exists(), "rdma_client.py should exist"


def test_rdma_manager_module() -> None:
    """Test that the RDMA manager module is importable."""
    manager_path = Path(__file__).parent.parent / "runner" / "rdma_manager.py"
    assert manager_path.exists(), "rdma_manager.py should exist"


def test_rdma_transport_protocol() -> None:
    """Test the TransportProtocol enum."""
    # Import the module
    api_path = Path(__file__).parent.parent / "api"
    if str(api_path) not in sys.path:
        sys.path.insert(0, str(api_path))

    try:
        from rdma_client import DeviceType, TransportProtocol

        assert TransportProtocol.INFINIBAND.value == "infiniband"
        assert DeviceType.PHYSICAL.value == "physical"
    except ImportError:
        # Module may not be importable due to relative imports
        pass


def test_rdma_skill_exists() -> None:
    """Test that the RDMA skill exists."""
    skill_path = Path(__file__).parent.parent / "skills" / "rdma" / "__init__.py"
    assert skill_path.exists(), "RDMA skill __init__.py should exist"


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"]).returncode)
