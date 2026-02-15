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
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def test_install_script_exists() -> None:
    """Test that the install.sh script exists."""
    install_script = PROJECT_ROOT / "install.sh"
    assert install_script.exists(), "install.sh should exist"
    assert install_script.is_file(), "install.sh should be a file"


def test_install_script_executable() -> None:
    """Test that the install.sh script is executable."""
    install_script = PROJECT_ROOT / "install.sh"
    assert install_script.stat().st_mode & 0o111, "install.sh should be executable"


def test_ollama_detection_command() -> None:
    """Test that ollama detection is implemented."""
    # Test that the install_qarin.py hook exists
    hook_path = PROJECT_ROOT / ".qarin" / "hooks" / "install_qarin.py"
    assert hook_path.exists(), "install_qarin.py hook should exist"


def test_pyproject_only_has_qarin_cli_entry_point() -> None:
    """Test that pyproject.toml only defines 'qarin', not a bare 'ollama' entry point."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    scripts = data.get("project", {}).get("scripts", {})
    assert "qarin" in scripts, "pyproject.toml [project.scripts] must contain 'qarin'"
    assert "ollama" not in scripts, (
        "pyproject.toml [project.scripts] must NOT contain a bare 'ollama' entry (only 'qarin' should exist)"
    )


def test_install_sh_wrapper_is_qarin_cli() -> None:
    """Test that install.sh creates a 'qarin' wrapper and not a bare 'ollama' wrapper."""
    install_script = PROJECT_ROOT / "install.sh"
    content = install_script.read_text()

    # The WRAPPER variable must point to qarin
    assert 'WRAPPER="$BIN_DIR/qarin"' in content, "install.sh WRAPPER variable should reference 'qarin'"

    # There should be no line creating a bare 'ollama' wrapper
    for line in content.splitlines():
        stripped = line.strip()
        # Skip comments and lines that reference 'qarin' (which is fine)
        if stripped.startswith("#"):
            continue
        if "qarin" in stripped:
            continue
        # Check for wrapper creation targeting a bare 'ollama' name
        if stripped.startswith("WRAPPER=") and "/ollama" in stripped:
            msg = f"install.sh must not create a bare 'ollama' wrapper: {stripped}"
            raise AssertionError(msg)


def test_install_sh_ollama_version_is_current() -> None:
    """Test that install.sh pins OLLAMA_VERSION to the current expected version (0.5.7)."""
    install_script = PROJECT_ROOT / "install.sh"
    content = install_script.read_text()

    assert 'OLLAMA_VERSION="0.5.7"' in content, (
        "install.sh should set OLLAMA_VERSION to '0.5.7', not the old '0.3.5' or any other value"
    )


if __name__ == "__main__":
    sys.exit(subprocess.run([sys.executable, "-m", "pytest", __file__, "-v"]).returncode)
