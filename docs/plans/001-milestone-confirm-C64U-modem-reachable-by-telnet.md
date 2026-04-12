# c64u-bbs v1 Plan

## Context

c64u-bbs should let anyone with a C64 Ultimate clone this repo, run a few commands, and have a working BBS. The golden path is C64U over the network — no SD cards, no physical interaction. From this Mac, we talk to the C64U via its REST API (port 80) and FTP (port 21), deploy BBS software, configure the ACIA modem, and serve incoming telnet connections as dial-in calls.

This plan covers the v1 Python toolchain: API client, CLI, file management, and BBS deployment.

## Architecture Decisions

- **Python 3.10+, sync httpx** — CLI-first tool, no async complexity needed. httpx can migrate to async later if we add MCP/server mode.
- **`DeviceBackend` Protocol** — lightweight typing.Protocol so the same CLI/deployer code can target VICE later. We only implement the C64U backend for now.
- **Config cascade** — CLI flags > env vars (`C64U_HOST`, `C64U_PASSWORD`) > `~/.config/c64u-bbs/config.toml`. No secrets in repo.
- **Click CLI** — `c64u` command with subcommands. Rich for pretty output.
- **Testing** — pytest + pytest-httpx with canned JSON fixtures. `@pytest.mark.integration` for real-device tests. **C64U is on the local network** so we can validate each phase on real hardware as we go.

## Project Layout

```
pyproject.toml
src/c64u_bbs/
    __init__.py
    client/
        __init__.py
        base.py            # DeviceBackend Protocol
        c64u.py            # C64U REST API client
        config.py          # Config loading (toml + env)
        discovery.py       # Network scan for C64U devices
    models/
        __init__.py
        device.py          # DeviceInfo, DriveInfo dataclasses
        drives.py          # DriveMode enum, MountOptions
    ftp/
        __init__.py
        client.py          # ftplib wrapper for file ops
    bbs/
        __init__.py
        deployer.py        # Orchestrates full BBS deployment
        software.py        # BBS catalog + download
    cli/
        __init__.py
        main.py            # Click group, global options
        commands/
            __init__.py
            info.py
            drives.py
            run.py
            files.py
            config.py
            discover.py
            bbs.py
tests/
    conftest.py
    fixtures/              # Canned API responses
    test_client.py
    test_drives.py
    test_ftp.py
    test_bbs.py
    test_cli.py
assets/
    .gitkeep               # BBS disk images downloaded here (gitignored)
```

## Phase 1: Foundation — API Client + Device Info

**Goal:** `pip install -e .` works, `c64u info` connects and prints device details.

**Deliver:**
- `pyproject.toml` with deps (httpx, click, tomli, rich) and `[project.scripts] c64u = "c64u_bbs.cli.main:cli"`
- `DeviceBackend` Protocol in `client/base.py`
- `C64UClient` in `client/c64u.py` — wraps httpx.Client, handles X-Password auth, implements `get_info()` via `GET /v1/info`
- `DeviceInfo` dataclass in `models/device.py`
- Config loading in `client/config.py` (toml file + env vars)
- `c64u info` CLI command
- Tests with mocked httpx responses

**Verify:** `c64u --host <ip> info` prints product name, firmware version, hostname.

## Phase 2: Drive Management + PRG Runner

**Goal:** Mount disk images, switch drive types, upload and run programs.

**Deliver:**
- `list_drives()` — `GET /v1/drives`
- `mount_drive()` — `PUT /v1/drives/{drive}:mount` (device path) or `POST` (upload)
- `unmount_drive()` — `PUT /v1/drives/{drive}:remove`
- `set_drive_mode()` — `PUT /v1/drives/{drive}:set_mode?mode=1541|1571|1581`
- `run_prg()` — `PUT /v1/runners:run_prg` (device path) or `POST` (upload)
- `reset()` — `PUT /v1/machine:reset`
- CLI: `c64u drives list|mount|unmount|mode`, `c64u run <file>`, `c64u reset`

**Verify:** Mount a D64, run a PRG, see it execute on the C64U.

## Phase 3: FTP File Management

**Goal:** Browse, upload, and download files on the C64U filesystem.

**Deliver:**
- `C64UFTP` class wrapping `ftplib.FTP` with context manager
- `list_dir()`, `upload()`, `download()`, `mkdir()`, `delete()`
- CLI: `c64u files ls|put|get|mkdir|rm`

**Verify:** `c64u files ls /` shows the device filesystem. Upload and download a test file.

## Phase 4: Device Config + Discovery

**Goal:** Read/write C64U config remotely. Find devices on the network automatically.

**Deliver:**
- `get_config()` / `set_config()` / `save_config()` via REST `/v1/configs` endpoints
- Network discovery via subnet scan (ThreadPoolExecutor, probe `/v1/info` with 0.5s timeout)
- CLI: `c64u config init|get|set|save`, `c64u discover [--save]`

**Verify:** `c64u discover` finds the C64U. `c64u config get "Modem*"` shows modem settings.

## Phase 5a: PETSCII Auto-Answer (Modem Proof-of-Concept)

**Goal:** Prove the full pipeline — upload a program, configure the modem, accept an incoming TCP connection.

**Deliver:**
- A minimal 6502/BASIC program that initializes the ACIA at $DE00, waits for RING, answers, and sends a PETSCII welcome screen
- Modem configuration helper in `deployer.py` that sets the ACIA config via REST
- `c64u bbs test` command that: configures modem → uploads auto-answer PRG → runs it → verifies by TCP connecting to the modem port

**Verify:** `telnet <c64u-ip> 6400` shows a PETSCII welcome screen. This proves: REST API works, PRG upload works, modem config works, TCP→ACIA pipeline works.

## Phase 5b: BBS Deployment

**Goal:** `c64u bbs deploy` gets a real BBS running end-to-end.

**Strategy:** Once Phase 5a proves the modem pipeline, deploy a real BBS package. Start with whichever has the most accessible freely-distributable D64 (Color 64, CBBS, or Image BBS).

**Deployment sequence in `deployer.py`:**
1. Download BBS disk image (if not cached in `assets/bbs/`)
2. Upload D64 to C64U via FTP
3. Configure ACIA modem via REST config API (reuse Phase 5a helper):
   - `Modem / ACIA` → `$DE00` (SwiftLink compatible)
   - `Modem / Listening Port` → `6400`
   - `Modem / Listen RING` → `Enabled`
   - Save to flash
4. Mount disk on drive A
5. Reset C64
6. Run BBS boot program
7. Verify: TCP connect to modem port, check for BBS response

**CLI:** `c64u bbs list|deploy|status|connect|stop`

**Verify:** `telnet <c64u-ip> 6400` connects to a running BBS with menus and interaction.

## The Golden Path (end-user flow)

```bash
git clone https://github.com/brainvat/c64u-bbs.git
cd c64u-bbs
pip install -e .
c64u discover --save        # Find C64U, save IP to config
c64u info                    # Confirm connectivity
c64u bbs deploy color64      # Deploy BBS
c64u bbs status              # Confirm running
telnet 192.168.1.x 6400     # Connect to BBS
```

## Dependencies

**Runtime:** httpx, click, tomli (py<3.11), rich
**Dev:** pytest, pytest-httpx, ruff

## Risks

1. **BBS disk images** — redistribution rights unclear for some classic BBS software. Start with a proof-of-concept auto-answer program we write ourselves, then add downloadable BBS packages.
2. **Modem config enum values** — exact string values for config items need to be discovered from a real device. Phase 4 must come before Phase 5.
3. **FTP quirks** — C64U's embedded FTP may behave differently from standard servers. Test early.

## Not in v1

- VICE backend (Protocol keeps the door open)
- GUI / web interface
- Video/audio streaming
- MCP server
- Multi-device management
- Custom BBS software authoring
