#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["python-dotenv"]
# ///
"""
RDMA management commands -- GOTCHA Tools layer, ATLAS Architect phase.

Provides commands for managing RDMA devices and connections.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from rich.console import Console

console = Console()


def cmd_rdma_detect(_args: argparse.Namespace) -> None:
    """Detect all RDMA devices on the system."""
    console.print("[bold cyan]Detecting RDMA devices...[/bold cyan]")

    devices = []

    # Try rdma tool first
    try:
        result = subprocess.run(
            ["rdma", "link", "show"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if line.strip():
                    name = line.split()[0].rstrip(":")
                    devices.append(
                        {
                            "name": name,
                            "type": "network_rdma",
                            "transport": _get_transport_protocol(name),
                        }
                    )
    except FileNotFoundError:
        console.print("[yellow]rdma tool not found. Checking for InfiniBand devices...[/yellow]")

    # Check for InfiniBand devices
    ib_path = Path("/sys/class/infiniband")
    if ib_path.exists():
        for device_dir in ib_path.iterdir():
            if device_dir.is_dir():
                name = device_dir.name
                vendor = _get_vendor(device_dir)
                devices.append(
                    {
                        "name": name,
                        "type": "infiniband",
                        "transport": "infiniband",
                        "vendor": vendor,
                    }
                )

    # Print results
    if not devices:
        console.print("[yellow]No RDMA devices detected.[/yellow]")
        console.print("")
        console.print("Common RDMA devices:")
        console.print("  - mlx5_0, mlx5_1 (Mellanox ConnectX)")
        console.print("  - ib0, ib1 (InfiniBand)")
        console.print("  - roce0, roce1 (RoCE)")
        return

    console.print(f"\n[bold]Found {len(devices)} RDMA device(s):[/bold]\n")
    for device in devices:
        console.print(f"  [cyan]{device['name']}[/cyan]")
        console.print(f"    Type: {device['type']}")
        console.print(f"    Transport: {device['transport']}")
        if "vendor" in device:
            console.print(f"    Vendor: {device['vendor']}")
        console.print()


def _get_transport_protocol(device_name: str) -> str:
    """Determine transport protocol from device name."""
    name_lower = device_name.lower()
    if "mlx" in name_lower:
        return "roce_v2"
    elif "roce" in name_lower:
        if "v2" in name_lower:
            return "roce_v2"
        return "roce"
    elif "iw" in name_lower:
        return "iwarp"
    elif "ib" in name_lower:
        return "infiniband"
    else:
        return "roce_v2"


def _get_vendor(device_dir: Path) -> str:
    """Get vendor name from device directory."""
    vendor_file = device_dir / "device" / "vendor"
    if vendor_file.exists():
        try:
            with open(vendor_file) as f:
                vendor_id = f.read().strip()
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


def cmd_rdma_status(_args: argparse.Namespace) -> None:
    """Show RDMA device status."""
    console.print("[bold cyan]RDMA Status[/bold cyan]")
    console.print("-" * 40)

    try:
        result = subprocess.run(
            ["rdma", "link", "show"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            console.print(result.stdout)
        else:
            console.print("[yellow]RDMA tools not available or no devices found.[/yellow]")
    except FileNotFoundError:
        console.print("[yellow]rdma tool not found. Install rdma-core package.[/yellow]")


def cmd_rdma_connect(args: argparse.Namespace) -> None:
    """Connect to an RDMA device."""
    device = args.device
    console.print(f"[bold cyan]Connecting to RDMA device: {device}[/bold cyan]")

    # Check device exists
    result = subprocess.run(
        ["rdma", "link", "show", device],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode == 0:
        console.print(f"[green]Connected to {device}![/green]")
        console.print("")
        console.print("Note: Full RDMA connection setup requires additional")
        console.print("configuration. This command detects and shows device info.")
        console.print("")
        console.print("Connected device details:")
        console.print(f"  Name: {device}")
        console.print(f"  Transport: {_get_transport_protocol(device)}")
    else:
        console.print(f"[red]Device {device} not found or not accessible.[/red]")
        console.print("")
        console.print("Available devices:")
        cmd_rdma_detect(args)


def cmd_rdma(_args: argparse.Namespace) -> None:
    """RDMA main command handler."""
    console.print("[bold]Ollama CLI - RDMA Management[/bold]")
    console.print("")
    console.print("Commands:")
    console.print("  rdma detect   - Detect all RDMA devices")
    console.print("  rdma status   - Show RDMA status")
    console.print("  rdma connect  - Connect to RDMA device")
    console.print("")
    console.print(" Examples:")
    console.print("  ollama-cli rdma detect")
    console.print("  ollama-cli rdma status")
    console.print("  ollama-cli rdma connect mlx5_0")


# Command registration
def register_commands(parser: argparse._SubParsersAction) -> None:
    """Register RDMA commands with the main parser."""
    subparsers = parser.add_subparsers(help="RDMA management commands")

    # ollama-cli rdma
    rdma_parser = subparsers.add_parser("rdma", help="RDMA management")
    rdma_parser.set_defaults(func=cmd_rdma)

    # ollama-cli rdma detect
    detect_parser = subparsers.add_parser("detect", help="Detect RDMA devices")
    detect_parser.set_defaults(func=cmd_rdma_detect)

    # ollama-cli rdma status
    status_parser = subparsers.add_parser("status", help="Show RDMA status")
    status_parser.set_defaults(func=cmd_rdma_status)

    # ollama-cli rdma connect <device>
    connect_parser = subparsers.add_parser("connect", help="Connect to RDMA device")
    connect_parser.add_argument("device", help="RDMA device name (e.g., mlx5_0)")
    connect_parser.set_defaults(func=cmd_rdma_connect)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="RDMA management")
    subparsers = parser.add_subparsers()
    register_commands(subparsers)

    args = parser.parse_args()

    if hasattr(args, "func"):
        args.func(args)
    else:
        cmd_rdma(args)


if __name__ == "__main__":
    main()
