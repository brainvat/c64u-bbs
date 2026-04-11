"""c64u run — load and execute programs on the C64U."""

from __future__ import annotations

from pathlib import Path

import click

from c64u_bbs.client.c64u import C64UError

# File extensions the C64U runner can handle
RUNNABLE_EXTENSIONS = {".prg", ".t64", ".p00"}

# Disk image extensions for drive mounting
DISK_IMAGE_EXTENSIONS = {".d64", ".g64", ".d71", ".g71", ".d81", ".dnp"}


@click.command()
@click.argument("file")
@click.option(
    "--no-run", is_flag=True, default=False,
    help="Load only, don't auto-run.",
)
@click.pass_context
def run(ctx: click.Context, file: str, no_run: bool) -> None:
    """Load and run a program on the C64U.

    FILE can be a local path (uploaded automatically) or a path on the
    C64U filesystem (e.g. /usb0/programs/game.prg).

    Supports PRG, T64, and P00 files. For disk images (D64, D71, D81),
    use 'c64u drives mount' instead.
    """
    client = ctx.obj["get_client"]()

    local_path = Path(file)
    is_local = local_path.exists() and local_path.is_file()

    # Warn if it looks like a disk image
    ext = local_path.suffix.lower() if is_local else Path(file).suffix.lower()
    if ext in DISK_IMAGE_EXTENSIONS:
        raise click.ClickException(
            f"{ext.upper()} is a disk image — use 'c64u drives mount a {file}' instead."
        )

    try:
        if is_local:
            data = local_path.read_bytes()
            if no_run:
                click.echo("Note: --no-run with local files not yet supported, running instead.")
            client.upload_and_run_prg(data, local_path.name)
            click.echo(f"Uploaded and running {local_path.name} ({len(data)} bytes)")
        else:
            if no_run:
                click.echo("Note: --no-run with device paths not yet supported, running instead.")
            client.run_prg(file)
            click.echo(f"Running {file}")
    except C64UError as e:
        raise click.ClickException(str(e))


@click.command()
@click.pass_context
def reset(ctx: click.Context) -> None:
    """Reset the C64."""
    client = ctx.obj["get_client"]()

    try:
        client.reset()
        click.echo("C64 reset.")
    except C64UError as e:
        raise click.ClickException(str(e))
