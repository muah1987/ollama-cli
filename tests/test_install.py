#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pytest"]
# ///
"""
Test installation functionality.
"""

import subprocess
import sys
from pathlib import Path


def test_install_script_exists() -> None:
    """Test that the install.sh script exists."""
    install_script = Path(__file__).parent / "install.sh"
    assert install_script.exists(), "install.sh should exist"
    assert install_script.is_file(), "install.sh should be a file"


def test_install_script_executable() -> None:
    """Test that the install.sh script is executable."""
    install_script = Path(__file__).parent / "install.sh"
    assert install_script.stat().st_mode & 0o111, "install.sh should be executable"


def test_ollama_detection_command() -> None:
    """Test that ollama detection is implemented."""
    # Test that the install_ollama.py hook exists
    hook_path = Path(__file__).parent / ".ollama" / "hooks" / "install_ollama.py"
    assert hook_path.exists(), "install_ollama.py hook should exist"


if __name__ == "__main__":
    sys.exit(subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"]).returncode)
