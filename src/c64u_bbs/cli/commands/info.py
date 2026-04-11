"""c64u info — display device information."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from c64u_bbs.client.c64u import C64UConnectionError, C64UError


@click.command()
@click.pass_context
def info(ctx: click.Context) -> None:
    """Show C64U device information."""
    client = ctx.obj["get_client"]()
    console = Console()

    try:
        device = client.get_info()
    except C64UConnectionError as e:
        raise click.ClickException(str(e))
    except C64UError as e:
        raise click.ClickException(f"API error: {e}")

    table = Table(title="C64 Ultimate Device Info", show_header=False)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Product", device.product)
    table.add_row("Firmware", device.firmware_version)
    table.add_row("FPGA", device.fpga_version)
    if device.core_version:
        table.add_row("Core", device.core_version)
    table.add_row("Hostname", device.hostname)
    table.add_row("Host", client.host)
    table.add_row("Unique ID", device.unique_id)

    console.print(table)
