"""c64u files — browse and transfer files on the C64U filesystem."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from c64u_bbs.ftp.client import C64UFTP, C64UFTPError


def _get_ftp(ctx: click.Context) -> C64UFTP:
    """Get an FTP client from the context config."""
    config = ctx.obj["config"]
    if not config.is_configured():
        raise click.ClickException(
            "No C64U host configured. Use --host, set C64U_HOST, or run: c64u config init"
        )
    return C64UFTP(host=config.host, port=config.ftp_port)


@click.group()
def files() -> None:
    """Browse and transfer files on the C64U filesystem."""


@files.command("ls")
@click.argument("path", default="/")
@click.pass_context
def files_ls(ctx: click.Context, path: str) -> None:
    """List directory contents on the C64U."""
    console = Console()

    try:
        with _get_ftp(ctx) as ftp:
            entries = ftp.list_dir(path)
    except C64UFTPError as e:
        raise click.ClickException(str(e))

    if not entries:
        console.print(f"[dim]{path} is empty[/dim]")
        return

    table = Table(title=f"C64U: {path}")
    table.add_column("Name", style="cyan")
    table.add_column("Size", justify="right", style="white")
    table.add_column("Modified", style="dim")
    table.add_column("Type", style="yellow")

    for entry in entries:
        if entry.is_dir:
            table.add_row(entry.name + "/", "", entry.modified, "DIR")
        else:
            size_str = _format_size(entry.size)
            table.add_row(entry.name, size_str, entry.modified, "")

    console.print(table)


@files.command()
@click.argument("local_file", type=click.Path(exists=True))
@click.argument("remote_path")
@click.pass_context
def put(ctx: click.Context, local_file: str, remote_path: str) -> None:
    """Upload a file to the C64U.

    Example: c64u files put ./game.d64 /SD/games/game.d64
    """
    try:
        with _get_ftp(ctx) as ftp:
            size = ftp.upload(local_file, remote_path)
    except C64UFTPError as e:
        raise click.ClickException(str(e))

    click.echo(f"Uploaded {Path(local_file).name} -> {remote_path} ({_format_size(size)})")


@files.command()
@click.argument("remote_path")
@click.argument("local_file", type=click.Path())
@click.pass_context
def get(ctx: click.Context, remote_path: str, local_file: str) -> None:
    """Download a file from the C64U.

    Example: c64u files get /Temp/CONGOBON.D64 ./CONGOBON.D64
    """
    try:
        with _get_ftp(ctx) as ftp:
            size = ftp.download(remote_path, local_file)
    except C64UFTPError as e:
        raise click.ClickException(str(e))

    click.echo(f"Downloaded {remote_path} -> {local_file} ({_format_size(size)})")


@files.command()
@click.argument("path")
@click.pass_context
def mkdir(ctx: click.Context, path: str) -> None:
    """Create a directory on the C64U."""
    try:
        with _get_ftp(ctx) as ftp:
            ftp.mkdir(path)
    except C64UFTPError as e:
        raise click.ClickException(str(e))

    click.echo(f"Created directory: {path}")


@files.command()
@click.argument("path")
@click.option("--force", "-f", is_flag=True, help="Don't prompt for confirmation.")
@click.pass_context
def rm(ctx: click.Context, path: str, force: bool) -> None:
    """Delete a file on the C64U."""
    if not force:
        click.confirm(f"Delete {path} on C64U?", abort=True)

    try:
        with _get_ftp(ctx) as ftp:
            ftp.delete(path)
    except C64UFTPError as e:
        raise click.ClickException(str(e))

    click.echo(f"Deleted: {path}")


def _format_size(size: int) -> str:
    """Format bytes to human-readable."""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"
