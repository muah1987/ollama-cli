#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Install Ollama and ollama-cli -- GOTCHA Tools layer, ATLAS Architect phase.

Provides commands for installing Ollama automatically or manually.
"""

from __future__ import annotations

import argparse
import subprocess
import sys

import httpx
from rich.console import Console

console = Console()


def cmd_install_ollama(args: argparse.Namespace) -> None:
    """Install Ollama automatically if not present.

    Args:
        args: Command line arguments
    """
    console.print("[bold cyan]Checking Ollama installation...[/bold cyan]")

    # Check if Ollama is already installed
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            console.print(f"[green]Ollama is already installed:[/green] {result.stdout.strip()}")
            return
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    console.print("[yellow]Ollama not found. Installing...[/yellow]")

    # Detect platform
    platform = sys.platform

    if platform.startswith("linux"):
        _install_ollama_linux(args)
    elif platform == "darwin":
        _install_ollama_macos(args)
    elif platform.startswith("win"):
        _install_ollama_windows(args)
    else:
        console.print(f"[red]Auto-installation not supported for platform: {platform}[/red]")
        console.print("Please install Ollama manually from https://ollama.ai")
        sys.exit(1)


def _install_ollama_linux(args: argparse.Namespace) -> None:
    """Install Ollama on Linux."""
    console.print("[bold]Installing Ollama for Linux...[/bold]")
    try:
        result = subprocess.run(
            ["curl", "-fsSL", "https://ollama.com/install.sh"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            console.print("[green]Ollama installed successfully![/green]")
        else:
            console.print(f"[red]Installation failed: {result.stderr}[/red]")
            sys.exit(1)
    except Exception as e:
        console.print(f"[red]Installation failed: {e}[/red]")
        sys.exit(1)


def _install_ollama_macos(args: argparse.Namespace) -> None:
    """Install Ollama on macOS."""
    console.print("[bold]Installing Ollama for macOS...[/bold]")

    # Try Homebrew first
    try:
        brew_result = subprocess.run(
            ["brew", "install", "ollama"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if brew_result.returncode == 0:
            console.print("[green]Ollama installed via Homebrew![/green]")
            return
    except FileNotFoundError:
        pass

    # Fall back to direct download
    version = getattr(args, "version", "0.5.7")
    url = f"https://github.com/ollama/ollama/releases/download/v{version}/ollama-darwin-amd64.tar.gz"
    console.print(f"[yellow]Downloading Ollama from {url}...[/yellow]")

    try:
        with httpx.stream("GET", url, timeout=120) as response:
            response.raise_for_status()
            # Extract to /usr/local/bin
            import io
            import tarfile

            with tarfile.open(fileobj=io.BytesIO(response.read()), mode="r:gz") as tar:
                tar.extractall("/usr/local/bin")
        console.print("[green]Ollama installed successfully![/green]")
    except Exception as e:
        console.print(f"[red]Installation failed: {e}[/red]")
        sys.exit(1)


def _install_ollama_windows(args: argparse.Namespace) -> None:
    """Install Ollama on Windows (WSL or native)."""
    console.print("[bold]Ollama Installation for Windows[/bold]")
    console.print("")
    console.print("[yellow]For WSL users:[/yellow]")
    console.print("  Run: curl -fsSL https://ollama.com/install.sh | sh")
    console.print("")
    console.print("[yellow]For native Windows users:[/yellow]")
    console.print("  Please install Ollama from: https://ollama.ai/download")
    console.print("  Or use winget: winget install Ollama.Ollama")


def cmd_check_ollama(_args: argparse.Namespace) -> None:
    """Check if Ollama is installed and running."""
    console.print("[bold cyan]Checking Ollama...[/bold cyan]")

    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            console.print(f"[green]Ollama is installed:[/green] {result.stdout.strip()}")
            console.print()
            console.print("[bold]Checking Ollama server status...[/bold]")

            # Try to connect to Ollama server
            cfg_result = subprocess.run(
                ["ollama", "serve"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if cfg_result.returncode == 0:
                console.print("[green]Ollama server is running![/green]")
            else:
                console.print("[yellow]Ollama server may not be running. Start with:[/yellow] ollama serve")
        else:
            console.print("[red]Ollama installation detected but not working.[/red]")
            console.print("Please reinstall or check your PATH.")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        console.print("[red]Ollama is not installed or not in PATH.[/red]")
        console.print("Install with: ollama-cli install")
        console.print("Or manually from: https://ollama.ai")


def cmd_install(_args: argparse.Namespace) -> None:
    """Main install command handler."""
    cmd_install_ollama(_args)


# Command to add to root.py
def register_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register install commands with the main parser's subparsers action."""
    # ollama-cli install
    install_parser = subparsers.add_parser("install", help="Install Ollama")
    install_parser.set_defaults(func=cmd_install)

    # ollama-cli install ollama
    install_ollama_parser = subparsers.add_parser("install-ollama", help="Install Ollama (legacy alias)")
    install_ollama_parser.set_defaults(func=cmd_install_ollama)

    # ollama-cli check
    check_parser = subparsers.add_parser("check", help="Check if Ollama is installed")
    check_parser.set_defaults(func=cmd_check_ollama)
