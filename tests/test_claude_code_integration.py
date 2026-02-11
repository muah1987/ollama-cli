#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""
Test Claude-Code integration.
"""

import sys
from pathlib import Path


def test_hooks_directory_exists() -> None:
    """Test that the .ollama/hooks directory exists."""
    hooks_dir = Path(__file__).parent.parent / ".ollama" / "hooks"
    assert hooks_dir.exists(), ".ollama/hooks directory should exist"


def test_all_hooks_present() -> None:
    """Test that all expected hooks are present."""
    hooks_dir = Path(__file__).parent.parent / ".ollama" / "hooks"
    expected_hooks = [
        "pre_tool_use.py",
        "post_tool_use.py",
        "session_start.py",
        "session_end.py",
        "pre_compact.py",
        "stop.py",
        "notification.py",
        "install_ollama.py",  # New hook
    ]

    for hook in expected_hooks:
        hook_path = hooks_dir / hook
        assert hook_path.exists(), f"{hook} should exist"


def test_settings_json_exists() -> None:
    """Test that settings.json exists."""
    settings_path = Path(__file__).parent.parent / ".ollama" / "settings.json"
    assert settings_path.exists(), ".ollama/settings.json should exist"


def test_install_hook_implements_detection() -> None:
    """Test that install_ollama.py implements Ollama detection."""
    hook_path = Path(__file__).parent.parent / ".ollama" / "hooks" / "install_ollama.py"
    content = hook_path.read_text(encoding="utf-8")

    assert "check_ollama_installed" in content, "install_ollama.py should have check_ollama_installed function"
    assert "install_ollama_linux" in content, "install_ollama.py should have install_ollama_linux function"
    assert "install_ollama_macos" in content, "install_ollama.py should have install_ollama_macos function"


def test_rdma_client_implements_protocol() -> None:
    """Test that rdma_client.py implements transport protocols."""
    client_path = Path(__file__).parent.parent / "api" / "rdma_client.py"
    content = client_path.read_text(encoding="utf-8")

    assert "TransportProtocol" in content, "rdma_client.py should have TransportProtocol"
    assert "INFINIBAND" in content, "rdma_client.py should support InfiniBand"
    assert "ROCE" in content or "RoCE" in content, "rdma_client.py should support RoCE"


if __name__ == "__main__":
    import subprocess

    sys.exit(subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"]).returncode)
