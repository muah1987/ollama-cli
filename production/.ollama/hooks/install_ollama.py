#!/usr/bin/env python3
"""
Auto-install Ollama if not present.
Hook: install_ollama.py

This hook runs before the CLI starts and checks if Ollama is installed.
If not, it prompts the user or automatically installs Ollama.

Usage: uv run install_ollama.py [--prompt]

Options:
  --prompt  Prompt user before installing (default: auto-install)
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def check_ollama_installed() -> bool:
    """Check if Ollama is installed and accessible."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_ollama_version() -> str | None:
    """Get the installed Ollama version."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def install_ollama_linux() -> bool:
    """Install Ollama on Linux using the official installer."""
    try:
        print("Installing Ollama for Linux...")
        result = subprocess.run(
            ["curl", "-fsSL", "https://ollama.com/install.sh", "|", "sh"],
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Linux installation failed: {e}")
        return False


def install_ollama_macos() -> bool:
    """Install Ollama on macOS using Homebrew or direct download."""
    try:
        # Try Homebrew first
        brew_result = subprocess.run(
            ["brew", "install", "ollama"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if brew_result.returncode == 0:
            return True

        # Fall back to direct download
        version = os.environ.get("OLLAMA_VERSION", "0.3.5")
        download_url = (
            f"https://github.com/ollama/ollama/releases/download/v{version}/"
            f"ollama-darwin-amd64.tar.gz"
        )
        print(f"Downloading Ollama from {download_url}...")
        result = subprocess.run(
            ["curl", "-L", download_url, "|", "tar", "xz", "-C", "/usr/local/bin"],
            shell=True,
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"macOS installation failed: {e}")
        return False


def install_ollama_windows() -> bool:
    """Install Ollama on Windows using WSL or direct download."""
    # Check if running in WSL
    if "WSL_DISTRO_NAME" in os.environ:
        print("Detected WSL environment. Please install Ollama in your WSL distribution.")
        print("Run: curl -fsSL https://ollama.com/install.sh | sh")
        return False

    # For native Windows, recommend manual installation
    print("Please install Ollama for Windows from:")
    print("https://ollama.ai/download")
    return False


def install_ollama() -> bool:
    """Install Ollama based on the current platform."""
    platform = sys.platform

    if platform.startswith("linux"):
        return install_ollama_linux()
    elif platform == "darwin":
        return install_ollama_macos()
    elif platform.startswith("win"):
        return install_ollama_windows()
    else:
        print(f"Auto-installation not supported for platform: {platform}")
        return False


def main() -> int:
    """Main entry point."""
    prompt = "--prompt" in sys.argv

    print("=== Ollama Installation Check ===")

    if check_ollama_installed():
        version = get_ollama_version()
        print(f"Ollama is already installed: {version}")
        return 0

    print("Ollama not found.")

    if prompt:
        print("Install Ollama automatically? [y/N]")
        response = input().strip().lower()
        if response not in ("y", "yes"):
            print("Please install Ollama manually from https://ollama.ai")
            return 1
    else:
        print("Auto-installing Ollama...")

    if install_ollama():
        print("\nOllama installation completed successfully!")
        return 0
    else:
        print("\nOllama installation failed.")
        print("Please install manually from https://ollama.ai")
        print("\nAfter installation, run: ollama serve")
        return 1


if __name__ == "__main__":
    sys.exit(main())
