"""c64u bbs — deploy and manage the BBS."""

from __future__ import annotations

import select
import socket
import sys
import time

import click
from rich.console import Console
from rich.table import Table

from c64u_bbs.bbs.autoanswer import generate_basic_autoanswer
from c64u_bbs.bbs.catalog import CATALOG, get_package, list_packages
from c64u_bbs.bbs.deployer import DeployError, backup_bbs, configure_modem, deploy_bbs, verify_modem_port
from c64u_bbs.client.c64u import C64UError


@click.group()
def bbs() -> None:
    """Deploy and manage the C64U BBS."""


@bbs.command()
@click.option("--port", default=6400, help="Modem listening port (default: 6400).")
@click.option("--save", "save_flash", is_flag=True, help="Save modem config to flash.")
@click.pass_context
def test(ctx: click.Context, port: int, save_flash: bool) -> None:
    """Run the auto-answer modem test.

    Configures the modem, uploads a PETSCII welcome program,
    runs it, and verifies the modem accepts connections.
    """
    client = ctx.obj["get_client"]()
    console = Console()

    # Step 1: Configure modem
    console.print("\n[bold]Phase 5a: Modem Pipeline Test[/bold]\n")
    console.print(f"  Configuring modem (port {port})...", end=" ")
    try:
        configure_modem(client, port=port, save_to_flash=save_flash)
        console.print("[green]OK[/green]")
    except C64UError as e:
        console.print(f"[red]FAILED[/red] — {e}")
        raise SystemExit(1)

    # Step 2: Generate and upload auto-answer program
    console.print("  Generating auto-answer PRG...", end=" ")
    prg_data = generate_basic_autoanswer()
    console.print(f"[green]OK[/green] ({len(prg_data)} bytes)")

    console.print("  Uploading and running on C64U...", end=" ")
    try:
        client.upload_and_run_prg(prg_data, "AUTOANSWER.PRG")
        console.print("[green]OK[/green]")
    except C64UError as e:
        console.print(f"[red]FAILED[/red] — {e}")
        raise SystemExit(1)

    # Step 3: Wait for the program to initialize
    console.print("  Waiting for program to start...", end=" ")
    time.sleep(3)
    console.print("[green]OK[/green]")

    # Step 4: Test the modem connection
    console.print(f"  Testing TCP connection to {client.host}:{port}...", end=" ")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        sock.connect((client.host, port))
        console.print("[green]CONNECTED[/green]")

        # Try to read data
        console.print("  Waiting for PETSCII data...", end=" ")
        sock.settimeout(10.0)
        try:
            data = sock.recv(1024)
            if data:
                console.print(f"[green]RECEIVED {len(data)} bytes[/green]")
                # Show first few bytes as hex for debugging
                hex_preview = " ".join(f"{b:02X}" for b in data[:32])
                console.print(f"  [dim]First 32 bytes: {hex_preview}[/dim]")
            else:
                console.print("[yellow]No data yet (connection accepted but program may still be initializing)[/yellow]")
        except socket.timeout:
            console.print("[yellow]Timeout waiting for data (connection accepted, no data sent yet)[/yellow]")

        sock.close()
    except socket.error as e:
        console.print(f"[red]FAILED[/red] — {e}")
        console.print("\n[yellow]The modem port is not accepting connections yet.[/yellow]")
        console.print("Check the C64U screen — the auto-answer program should be running.")
        console.print(f"You can test manually: [cyan]telnet {client.host} {port}[/cyan]")
        raise SystemExit(1)

    # Summary
    console.print("\n[bold green]Modem pipeline test complete.[/bold green]")
    console.print(f"\nTo connect manually: [cyan]telnet {client.host} {port}[/cyan]")
    console.print("The auto-answer program will greet incoming connections with a PETSCII welcome screen.\n")


@bbs.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Check if the BBS is accepting connections."""
    client = ctx.obj["get_client"]()
    console = Console()

    # Read modem config to find port
    try:
        data = client.get_config("Modem Settings")
        modem = data.get("Modem Settings", {})
        port = int(modem.get("Listening Port", 3000))
    except (C64UError, ValueError):
        port = 6400

    console.print(f"Checking modem at {client.host}:{port}...", end=" ")

    if verify_modem_port(client.host, port):
        console.print("[bold green]ONLINE[/bold green] — accepting connections")
    else:
        console.print("[bold red]OFFLINE[/bold red] — not accepting connections")


@bbs.command()
@click.pass_context
def stop(ctx: click.Context) -> None:
    """Stop the BBS by resetting the C64."""
    client = ctx.obj["get_client"]()

    try:
        client.reset()
        click.echo("C64 reset. BBS stopped.")
    except C64UError as e:
        raise click.ClickException(str(e))


@bbs.command("list")
def list_cmd() -> None:
    """List available BBS packages."""
    console = Console()
    packages = list_packages()

    if not packages:
        console.print("[yellow]No BBS packages available.[/yellow]")
        return

    table = Table(title="Available BBS Packages")
    table.add_column("Name", style="cyan")
    table.add_column("Version")
    table.add_column("License", style="green")
    table.add_column("Disks")
    table.add_column("Description")

    for pkg in packages:
        disk_summary = ", ".join(
            f"{d.drive.upper()}:{d.drive_mode.value}" for d in pkg.disks
        )
        table.add_row(
            pkg.name,
            pkg.version,
            pkg.license,
            disk_summary,
            pkg.description,
        )

    console.print(table)


@bbs.command()
@click.argument("package", default="imagebbs")
@click.option("--port", default=6400, help="Modem listening port (default: 6400).")
@click.option("--save", "save_flash", is_flag=True, help="Save modem config to flash.")
@click.option("--no-verify", is_flag=True, help="Skip post-deploy connection check.")
@click.pass_context
def deploy(
    ctx: click.Context,
    package: str,
    port: int,
    save_flash: bool,
    no_verify: bool,
) -> None:
    """Deploy a BBS package to the C64U.

    PACKAGE is the name of the BBS to deploy (default: color64).
    Use 'c64u bbs list' to see available packages.
    """
    console = Console()

    # Look up package
    try:
        pkg = get_package(package)
    except KeyError:
        available = ", ".join(CATALOG.keys())
        raise click.ClickException(
            f"Unknown BBS package: {package!r}. Available: {available}"
        )

    console.print(f"\n[bold]Deploying {pkg.display_name}[/bold]\n")

    def on_step(name: str, detail: str) -> None:
        console.print(f"  {detail}", end=" ")

    # Deploy
    try:
        deploy_bbs(
            ctx.obj["get_client"](),
            pkg,
            port=port,
            save_to_flash=save_flash,
            on_step=lambda name, detail: console.print(f"  {detail}"),
        )
    except DeployError as e:
        console.print(f"\n[red]Deploy failed:[/red] {e}")
        raise SystemExit(1)
    except C64UError as e:
        console.print(f"\n[red]Device error:[/red] {e}")
        raise SystemExit(1)

    # Success
    host = ctx.obj["config"].host
    console.print(f"\n[bold green]{pkg.display_name} is running![/bold green]")
    console.print(f"\nConnect with: [cyan]telnet {host} {port}[/cyan]")
    console.print(f"Or use:       [cyan]c64u bbs connect[/cyan]\n")


@bbs.command()
@click.argument("package", default="imagebbs")
@click.option("--dir", "dest_dir", default="./backups", help="Backup directory (default: ./backups).")
@click.option("--port", default=6400, help="Modem listening port (default: 6400).")
@click.pass_context
def backup(
    ctx: click.Context,
    package: str,
    dest_dir: str,
    port: int,
) -> None:
    """Back up BBS disk images from the C64U.

    Downloads the deployed disk images from the C64U's SD card. The BBS
    must be stopped first (c64u bbs stop).

    PACKAGE is the name of the BBS to back up (default: imagebbs).
    """
    from datetime import datetime
    from pathlib import Path

    console = Console()

    try:
        pkg = get_package(package)
    except KeyError:
        available = ", ".join(CATALOG.keys())
        raise click.ClickException(
            f"Unknown BBS package: {package!r}. Available: {available}"
        )

    # Create timestamped subdirectory
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = Path(dest_dir) / timestamp

    console.print(f"\n[bold]Backing up {pkg.display_name}[/bold]\n")

    try:
        saved = backup_bbs(
            ctx.obj["get_client"](),
            pkg,
            backup_path,
            port=port,
            on_step=lambda name, detail: console.print(f"  {detail}"),
        )
    except DeployError as e:
        console.print(f"\n[red]Backup failed:[/red] {e}")
        raise SystemExit(1)
    except C64UError as e:
        console.print(f"\n[red]Device error:[/red] {e}")
        raise SystemExit(1)

    console.print(f"\n[bold green]Backup complete.[/bold green]")
    console.print(f"\n  {len(saved)} file(s) saved to [cyan]{backup_path}[/cyan]:")
    for path in saved:
        size_kb = path.stat().st_size / 1024
        console.print(f"    {path.name} ({size_kb:.0f} KB)")
    console.print()


@bbs.command()
@click.option("--port", default=6400, help="Modem listening port (default: 6400).")
@click.pass_context
def connect(ctx: click.Context, port: int) -> None:
    """Connect to the running BBS via raw TCP.

    Opens a raw TCP relay to the BBS modem port. For best results,
    use a PETSCII-capable terminal (SyncTerm, CGTerm) pointed at
    the BBS directly. This command is for quick verification.

    Press Ctrl+C to disconnect.
    """
    host = ctx.obj["config"].host
    console = Console()

    console.print(f"Connecting to {host}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10.0)
        sock.connect((host, port))
        sock.setblocking(False)
    except socket.error as e:
        raise click.ClickException(f"Could not connect: {e}")

    console.print("[green]Connected.[/green] Press Ctrl+C to disconnect.\n")

    try:
        while True:
            readable, _, _ = select.select([sock, sys.stdin], [], [], 0.1)
            for s in readable:
                if s is sock:
                    try:
                        data = sock.recv(4096)
                        if not data:
                            console.print("\n[yellow]Connection closed by BBS.[/yellow]")
                            return
                        sys.stdout.buffer.write(data)
                        sys.stdout.buffer.flush()
                    except BlockingIOError:
                        pass
                elif s is sys.stdin:
                    data = sys.stdin.buffer.read1(1024)
                    if data:
                        sock.sendall(data)
    except KeyboardInterrupt:
        console.print("\n[yellow]Disconnected.[/yellow]")
    finally:
        sock.close()
