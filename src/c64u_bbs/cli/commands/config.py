"""c64u config — manage device and client configuration."""

from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from c64u_bbs.client.c64u import C64UClient, C64UError
from c64u_bbs.client.config import Config, load_config, save_config


@click.group()
def config() -> None:
    """Manage device and client configuration."""


@config.command()
@click.pass_context
def init(ctx: click.Context) -> None:
    """Interactive first-time setup. Saves C64U host to config file."""
    console = Console()
    console.print("[bold]c64u config init[/bold]\n")

    existing = ctx.obj["config"]

    host = click.prompt(
        "C64U IP address or hostname",
        default=existing.host or None,
    )
    password = click.prompt(
        "C64U network password (leave empty if none)",
        default="",
        show_default=False,
    )

    # Test connectivity
    console.print(f"\nTesting connection to {host}...", end=" ")
    try:
        client = C64UClient(host=host, password=password or None)
        info = client.get_info()
        console.print(f"[green]OK[/green] — {info.product} ({info.hostname})")
        client.close()
    except C64UError as e:
        console.print(f"[red]FAILED[/red] — {e}")
        if not click.confirm("Save anyway?"):
            raise SystemExit(1)

    cfg = Config(
        host=host,
        password=password or None,
    )
    path = save_config(cfg)
    console.print(f"\n[green]Saved to {path}[/green]")
    console.print("You can now use [cyan]c64u[/cyan] without --host.")


@config.command("show")
@click.pass_context
def config_show(ctx: click.Context) -> None:
    """Show current client configuration."""
    cfg = ctx.obj["config"]
    console = Console()

    table = Table(title="Client Configuration", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Host", cfg.host or "(not set)")
    table.add_row("Password", "****" if cfg.password else "(not set)")
    table.add_row("HTTP Port", str(cfg.http_port))
    table.add_row("FTP Port", str(cfg.ftp_port))

    console.print(table)


@config.command("categories")
@click.pass_context
def config_categories(ctx: click.Context) -> None:
    """List device config categories."""
    client = ctx.obj["get_client"]()
    console = Console()

    try:
        categories = client.list_config_categories()
    except C64UError as e:
        raise click.ClickException(str(e))

    for cat in categories:
        console.print(f"  [cyan]{cat}[/cyan]")


@config.command("get")
@click.argument("category")
@click.pass_context
def config_get(ctx: click.Context, category: str) -> None:
    """Read a device config category.

    Example: c64u config get "Modem Settings"
    """
    client = ctx.obj["get_client"]()
    console = Console()

    try:
        data = client.get_config(category)
    except C64UError as e:
        raise click.ClickException(str(e))

    # Response is {"Category Name": {"item": "value", ...}, "errors": []}
    for cat_name, items in data.items():
        if cat_name == "errors":
            continue
        if not isinstance(items, dict):
            continue

        table = Table(title=cat_name, show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")

        for key, value in items.items():
            table.add_row(key, str(value))

        console.print(table)


@config.command("set")
@click.argument("category")
@click.argument("item")
@click.argument("value")
@click.option("--save", "save_flash", is_flag=True, help="Also save to flash.")
@click.pass_context
def config_set(ctx: click.Context, category: str, item: str, value: str, save_flash: bool) -> None:
    """Set a device config value.

    Example: c64u config set "Modem Settings" "Listening Port" "6400"
    """
    client = ctx.obj["get_client"]()

    try:
        client.set_config(category, item, value)
        click.echo(f"Set [{category}] {item} = {value}")
        if save_flash:
            client.save_config()
            click.echo("Saved to flash.")
    except C64UError as e:
        raise click.ClickException(str(e))


@config.command("save")
@click.pass_context
def config_save(ctx: click.Context) -> None:
    """Save current device config to flash (persists across reboots)."""
    client = ctx.obj["get_client"]()

    try:
        client.save_config()
        click.echo("Configuration saved to flash.")
    except C64UError as e:
        raise click.ClickException(str(e))
