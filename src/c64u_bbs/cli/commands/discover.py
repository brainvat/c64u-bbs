"""c64u discover — find C64U devices on the local network."""

from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed

import click
from rich.console import Console
from rich.table import Table

from c64u_bbs.client.c64u import C64UClient
from c64u_bbs.client.config import Config, save_config
from c64u_bbs.models.device import DeviceInfo


def _get_local_subnet() -> str | None:
    """Get the local IP address and derive the /24 subnet."""
    try:
        # Connect to a public DNS to determine our local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        # Derive /24 subnet
        network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)
        return str(network)
    except Exception:
        return None


def _probe_host(ip: str, timeout: float = 0.5) -> tuple[str, DeviceInfo] | None:
    """Try to reach a C64U at the given IP. Returns (ip, info) or None."""
    try:
        client = C64UClient(host=ip, timeout=timeout)
        info = client.get_info()
        client.close()
        return (ip, info)
    except Exception:
        return None


@click.command()
@click.option("--subnet", default=None, help="Subnet to scan (e.g. 192.168.1.0/24). Auto-detected if omitted.")
@click.option("--timeout", default=0.5, help="Probe timeout per host in seconds.")
@click.option("--save", "do_save", is_flag=True, help="Save the first discovered device to config.")
@click.pass_context
def discover(ctx: click.Context, subnet: str | None, timeout: float, do_save: bool) -> None:
    """Scan the local network for C64U devices."""
    console = Console()

    if subnet is None:
        subnet = _get_local_subnet()
        if subnet is None:
            raise click.ClickException("Cannot determine local subnet. Use --subnet to specify.")

    console.print(f"Scanning {subnet} for C64U devices...\n")

    try:
        network = ipaddress.IPv4Network(subnet, strict=False)
    except ValueError as e:
        raise click.ClickException(f"Invalid subnet: {e}")

    hosts = [str(ip) for ip in network.hosts()]
    found: list[tuple[str, DeviceInfo]] = []

    with ThreadPoolExecutor(max_workers=50) as pool:
        futures = {pool.submit(_probe_host, ip, timeout): ip for ip in hosts}
        for future in as_completed(futures):
            result = future.result()
            if result:
                ip, info = result
                found.append(result)
                console.print(f"  [green]Found:[/green] {info.product} at [cyan]{ip}[/cyan] ({info.hostname})")

    if not found:
        console.print("[yellow]No C64U devices found.[/yellow]")
        console.print("Make sure your C64U is powered on and connected to the same network.")
        return

    console.print(f"\n[bold]{len(found)} device(s) found.[/bold]")

    if do_save:
        ip, info = found[0]
        cfg = Config(host=ip)
        path = save_config(cfg)
        console.print(f"\n[green]Saved {info.hostname} ({ip}) to {path}[/green]")
        console.print("You can now use [cyan]c64u[/cyan] without --host.")
