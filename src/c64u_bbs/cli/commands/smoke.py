"""c64u smoke — run a connectivity smoke test against the C64U."""

from __future__ import annotations

import click
from rich.console import Console

from c64u_bbs.client.c64u import C64UConnectionError, C64UAuthError, C64UError


@click.command()
@click.pass_context
def smoke(ctx: click.Context) -> None:
    """Run a smoke test against the C64U.

    Tests connectivity, authentication, and basic API endpoints.
    """
    client = ctx.obj["get_client"]()
    console = Console()
    passed = 0
    failed = 0

    def check(label: str, fn):
        nonlocal passed, failed
        try:
            result = fn()
            console.print(f"  [green]PASS[/green]  {label}")
            passed += 1
            return result
        except C64UConnectionError as e:
            console.print(f"  [red]FAIL[/red]  {label}")
            console.print(f"         [dim]{e}[/dim]")
            failed += 1
        except C64UAuthError as e:
            console.print(f"  [red]FAIL[/red]  {label}")
            console.print(f"         [dim]{e}[/dim]")
            failed += 1
        except C64UError as e:
            console.print(f"  [red]FAIL[/red]  {label}")
            console.print(f"         [dim]{e}[/dim]")
            failed += 1
        except Exception as e:
            console.print(f"  [red]FAIL[/red]  {label}")
            console.print(f"         [dim]{type(e).__name__}: {e}[/dim]")
            failed += 1
        return None

    console.print(f"\n[bold]Smoke testing C64U at {client.host}:{client.port}[/bold]\n")

    # Test 1: Device info
    info = check("GET /v1/info — device identification", client.get_info)
    if info:
        console.print(f"         [dim]{info.product} / firmware {info.firmware_version} / {info.hostname}[/dim]")

    # Test 2: Drive listing
    drives = check("GET /v1/drives — list emulated drives", client.list_drives)
    if drives:
        enabled = [d for d in drives if d.enabled]
        console.print(f"         [dim]{len(drives)} drives found, {len(enabled)} enabled[/dim]")

    # Test 3: Config categories
    check("GET /v1/configs — read device configuration", client.list_config_categories)

    # Summary
    console.print()
    total = passed + failed
    if failed == 0:
        console.print(f"[bold green]All {total} checks passed.[/bold green] C64U is reachable and responding.\n")
    else:
        console.print(f"[bold red]{failed}/{total} checks failed.[/bold red]\n")
        raise SystemExit(1)
