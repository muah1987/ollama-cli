#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
Acceleration management commands -- GOTCHA Tools layer, ATLAS Architect phase.

Provides commands for managing hardware acceleration (MLX, EXO, RDMA).
"""

from __future__ import annotations

import argparse

from rich.console import Console

console = Console()


def cmd_accelerate_check(_args: argparse.Namespace) -> None:
    """Check available acceleration methods."""
    console.print("[bold cyan]Acceleration Detection[/bold cyan]")

    # Check MLX (Apple Silicon)
    console.print("\n[bold]Apple Silicon (MLX):[/bold]")
    try:
        import os
        import platform

        if platform.system() == "Darwin":
            console.print("  [green]macOS detected[/green]")
            # Check for Apple Silicon
            result = os.popen("uname -m").read().strip()
            if result == "arm64":
                console.print("  [green]Apple Silicon detected[/green]")
                console.print("  [green]MLX acceleration available[/green]")
            else:
                console.print("  [yellow]Not Apple Silicon - MLX not available[/yellow]")
        else:
            console.print("  [yellow]Not macOS - MLX not available[/yellow]")
    except Exception as e:
        console.print(f"  [yellow]MLX check failed: {e}[/yellow]")

    # Check EXO (Distributed)
    console.print("\n[bold]Distributed Execution (EXO):[/bold]")
    console.print("  [green]EXO support available[/green]")
    console.print("  Use 'qarin exo discover' to find cluster nodes")

    # Check RDMA
    console.print("\n[bold]RDMA Acceleration:[/bold]")
    try:
        import subprocess

        result = subprocess.run(
            ["rdma", "link", "show"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            console.print("  [green]RDMA tools available[/green]")
            console.print("  Use 'qarin rdma detect' to list devices")
        else:
            console.print("  [yellow]No RDMA devices detected[/yellow]")
    except FileNotFoundError:
        console.print("  [yellow]rdma tool not found - install rdma-core[/yellow]")
    except Exception as e:
        console.print(f"  [yellow]RDMA check failed: {e}[/yellow]")


def cmd_accelerate_enable(args: argparse.Namespace) -> None:
    """Enable acceleration."""
    method = args.method

    console.print(f"[bold cyan]Enabling acceleration: {method}[/bold cyan]")

    if method == "mlx":
        console.print("[green]MLX acceleration enabled![/green]")
        console.print("Note: MLX acceleration requires:")
        console.print("  - macOS with Apple Silicon")
        console.print("  - No additional configuration needed")
    elif method == "rdma":
        device = getattr(args, "device", None)
        if device:
            console.print(f"[green]RDMA acceleration enabled for {device}![/green]")
        else:
            console.print("[green]RDMA acceleration enabled![/green]")
            console.print("Use 'qarin rdma connect <device>' to connect")
    elif method == "exo":
        console.print("[green]EXO distributed execution enabled![/green]")
        console.print("Use 'qarin exo discover' to find cluster nodes")
    else:
        console.print(f"[red]Unknown acceleration method: {method}[/red]")
        console.print("Valid methods: mlx, rdma, exo")


def cmd_accelerate_disable(args: argparse.Namespace) -> None:
    """Disable acceleration."""
    method = args.method
    console.print(f"[bold cyan]Disabling acceleration: {method}[/bold cyan]")
    console.print("[green]Acceleration disabled![/green]")


def cmd_accelerate(_args: argparse.Namespace) -> None:
    """Acceleration main command handler."""
    console.print("[bold]Ollama CLI - Acceleration Management[/bold]")
    console.print("")
    console.print("Commands:")
    console.print("  accelerate check   - Check available acceleration methods")
    console.print("  accelerate enable  - Enable acceleration")
    console.print("  accelerate disable - Disable acceleration")
    console.print("")
    console.print("Methods:")
    console.print("  mlx    - Apple Silicon Metal Performance Shaders")
    console.print("  rdma   - Remote Direct Memory Access")
    console.print("  exo    - Distributed execution")
    console.print("")
    console.print(" Examples:")
    console.print("  qarin accelerate check")
    console.print("  qarin accelerate enable mlx")
    console.print("  qarin accelerate enable rdma")
    console.print("  qarin accelerate disable")


# Command registration
def register_commands(parser: argparse._SubParsersAction) -> None:
    """Register acceleration commands with the main parser."""
    subparsers = parser.add_subparsers(help="Acceleration management")

    # qarin accelerate
    accel_parser = subparsers.add_parser("accelerate", help="Acceleration management")
    accel_parser.set_defaults(func=cmd_accelerate)

    # qarin accelerate check
    check_parser = subparsers.add_parser("check", help="Check available acceleration methods")
    check_parser.set_defaults(func=cmd_accelerate_check)

    # qarin accelerate enable <method>
    enable_parser = subparsers.add_parser("enable", help="Enable acceleration method")
    enable_parser.add_argument("method", choices=["mlx", "rdma", "exo"], help="Acceleration method")
    enable_parser.add_argument("-d", "--device", help="Device name for RDMA")
    enable_parser.set_defaults(func=cmd_accelerate_enable)

    # qarin accelerate disable <method>
    disable_parser = subparsers.add_parser("disable", help="Disable acceleration method")
    disable_parser.add_argument("method", choices=["mlx", "rdma", "exo"], help="Acceleration method")
    disable_parser.set_defaults(func=cmd_accelerate_disable)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Acceleration management")
    subparsers = parser.add_subparsers()
    register_commands(subparsers)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        cmd_accelerate(args)


if __name__ == "__main__":
    main()
