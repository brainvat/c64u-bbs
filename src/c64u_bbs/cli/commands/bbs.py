"""c64u bbs — deploy and manage the BBS."""

from __future__ import annotations

import socket
import time

import click
from rich.console import Console

from c64u_bbs.bbs.autoanswer import generate_basic_autoanswer
from c64u_bbs.bbs.deployer import configure_modem, verify_modem_port
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
