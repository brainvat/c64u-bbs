"""c64u drives — manage emulated floppy drives."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from c64u_bbs.client.c64u import C64UError
from c64u_bbs.models.drives import DriveMode, MountMode


@click.group()
def drives() -> None:
    """Manage emulated floppy drives."""


@drives.command("list")
@click.pass_context
def drives_list(ctx: click.Context) -> None:
    """List all drives and their status."""
    client = ctx.obj["get_client"]()
    console = Console()

    try:
        drive_list = client.list_drives()
    except C64UError as e:
        raise click.ClickException(str(e))

    table = Table(title="Emulated Drives")
    table.add_column("Drive", style="cyan")
    table.add_column("Enabled", style="white")
    table.add_column("Bus ID", style="white")
    table.add_column("Type", style="yellow")
    table.add_column("ROM", style="white")
    table.add_column("Mounted Image", style="green")

    for d in drive_list:
        table.add_row(
            d.drive_id.upper(),
            "Yes" if d.enabled else "No",
            str(d.bus_id),
            d.drive_type,
            d.rom_file,
            d.mounted_image or "(empty)",
        )

    console.print(table)


@drives.command()
@click.argument("drive", type=click.Choice(["a", "b", "softiec"], case_sensitive=False))
@click.argument("image")
@click.option(
    "--mode",
    type=click.Choice(["readwrite", "readonly", "unlinked"], case_sensitive=False),
    default="readwrite",
    help="Mount mode (default: readwrite).",
)
@click.option(
    "--upload", is_flag=True, default=False,
    help="Upload a local file instead of using a device path.",
)
@click.pass_context
def mount(ctx: click.Context, drive: str, image: str, mode: str, upload: bool) -> None:
    """Mount a disk image on a drive.

    IMAGE is a path on the C64U filesystem (e.g. /usb0/games/game.d64).
    Use --upload to send a local file instead.
    """
    client = ctx.obj["get_client"]()
    mount_mode = MountMode(mode)

    try:
        if upload:
            local_path = Path(image)
            if not local_path.exists():
                raise click.ClickException(f"Local file not found: {image}")
            data = local_path.read_bytes()
            client.upload_and_mount(drive, data, local_path.name, mode=mount_mode)
            click.echo(f"Uploaded and mounted {local_path.name} on drive {drive.upper()}")
        else:
            client.mount_drive(drive, image, mode=mount_mode)
            click.echo(f"Mounted {image} on drive {drive.upper()}")
    except C64UError as e:
        raise click.ClickException(str(e))


@drives.command()
@click.argument("drive", type=click.Choice(["a", "b", "softiec"], case_sensitive=False))
@click.pass_context
def unmount(ctx: click.Context, drive: str) -> None:
    """Unmount/eject the disk from a drive."""
    client = ctx.obj["get_client"]()

    try:
        client.unmount_drive(drive)
        click.echo(f"Unmounted drive {drive.upper()}")
    except C64UError as e:
        raise click.ClickException(str(e))


@drives.command()
@click.argument("drive", type=click.Choice(["a", "b", "softiec"], case_sensitive=False))
@click.argument("mode", type=click.Choice(["1541", "1571", "1581"], case_sensitive=False))
@click.pass_context
def mode(ctx: click.Context, drive: str, mode: str) -> None:
    """Change drive emulation type (1541/1571/1581)."""
    client = ctx.obj["get_client"]()

    try:
        client.set_drive_mode(drive, DriveMode(mode))
        click.echo(f"Drive {drive.upper()} set to {mode}")
    except C64UError as e:
        raise click.ClickException(str(e))
