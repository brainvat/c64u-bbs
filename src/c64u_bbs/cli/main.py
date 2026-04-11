"""CLI entry point for c64u-bbs."""

from __future__ import annotations

import click

from c64u_bbs.client.c64u import C64UClient
from c64u_bbs.client.config import load_config


pass_client = click.make_pass_decorator(C64UClient, ensure=True)


@click.group()
@click.option("--host", envvar="C64U_HOST", default=None, help="C64U IP address or hostname.")
@click.option("--password", envvar="C64U_PASSWORD", default=None, help="C64U network password.")
@click.version_option(package_name="c64u-bbs")
@click.pass_context
def cli(ctx: click.Context, host: str | None, password: str | None) -> None:
    """c64u — manage your Commodore 64 Ultimate over the network."""
    config = load_config(host=host, password=password)
    ctx.ensure_object(dict)
    ctx.obj["config"] = config

    # Lazily create client only when a subcommand needs it
    def get_client() -> C64UClient:
        if "client" not in ctx.obj:
            if not config.is_configured():
                raise click.ClickException(
                    "No C64U host configured. Use --host, set C64U_HOST, "
                    "or run: c64u config init"
                )
            ctx.obj["client"] = C64UClient(
                host=config.host,
                password=config.password,
                port=config.http_port,
            )
        return ctx.obj["client"]

    ctx.obj["get_client"] = get_client


# Import and register subcommands
from c64u_bbs.cli.commands.info import info  # noqa: E402

cli.add_command(info)
