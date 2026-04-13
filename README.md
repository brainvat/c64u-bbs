# c64u-bbs

Deploy and manage a Commodore 64 BBS on the [C64 Ultimate](https://ultimate64.com/) — over the network, no SD cards.

Ships with [Image BBS v3.0](https://8bitboyz.com/) by the 8-Bit Boyz community (Ray Kelm, John Moore, Jack Followay, Larry Hedman, and contributors). Pre-configured golden disk images boot directly on the C64U with SwiftLink modem emulation.

## Requirements

- Python 3.10+
- A C64 Ultimate (Ultimate 64 or Ultimate-II+) on your local network
- [MuffinTerm](https://muffinterm.com/) or another PETSCII terminal for connecting to the BBS

## Quick Start

```bash
# Clone and install
git clone https://github.com/brainvat/c64u-bbs.git
cd c64u-bbs
bash install.sh          # or: bash install.sh --dev (includes test tools)
source venv/bin/activate

# Deploy the BBS (first time — specify your C64U's IP)
c64u --host <your-c64u-ip> bbs deploy

# Connect
c64u bbs connect
# Or: telnet <your-c64u-ip> 6400
```

### Disk Image Setup

Golden (pre-configured) disk images ship with the repo. To manage them
or install fresh copies from the original source:

```bash
bash setup-bbs.sh
```

This menu-driven script lets you:
1. Re-download the original Image BBS 3.0 files from [8bitboyz.com](https://8bitboyz.com/)
2. Install base (unmodified) images to a C64 Ultimate or VICE
3. Install pre-configured golden images to a C64 Ultimate or VICE

## What It Does

The `c64u bbs deploy` command:

1. Resets the C64 to a clean state
2. Configures the C64U modem (ACIA/SwiftLink at $DE00, port 6400)
3. Uploads golden disk images to the C64U's SD card via FTP
4. Blanks the modem welcome banner so callers see the BBS directly
5. Mounts D1 (programs) on drive A and D2 (data) on drive B as 1581 drives
6. Boots Image BBS via a BASIC loader
7. Waits for the BBS to accept connections on the modem port

After deploy, callers connect via `telnet <c64u-ip> 6400`.

## CLI Commands

```bash
c64u bbs deploy [PACKAGE]   # Deploy a BBS (default: imagebbs)
c64u bbs list               # List available BBS packages
c64u bbs status             # Check if BBS is accepting connections
c64u bbs connect            # Raw TCP connection to the BBS
c64u bbs stop               # Reset C64 (stops the BBS)
c64u bbs test               # Run modem auto-answer test

c64u info                   # Show C64U device info
c64u drives                 # Show drive status
c64u config init            # Configure C64U connection
c64u discover               # Find C64U devices on the network
c64u smoke                  # Run hardware smoke tests
```

## Disk Images

The BBS runs from two 1581 disk images:

| Image | Drive | Contents |
|-------|-------|----------|
| `Master_D1_260125.d81` | A (device 8) | Programs: boot loader, ML engine, all BBS modules |
| `Master_D2_260125.d81` | B (device 9) | Data: menus, screens, user files, config, logs |

Golden (deploy-ready) images are in `assets/bbs/imagebbs/`. Untouched upstream originals are in `assets/bbs/imagebbs/upstream/`. See [`PROVENANCE.md`](assets/bbs/imagebbs/PROVENANCE.md) for exactly what was changed and why.

## Post-Deploy

The golden images ship with a working sysop account and SwiftLink modem
configuration. The BBS boots to its idle screen and accepts callers
immediately — no manual setup required.

To log in as sysop from the C64U console:

1. Press F1 (full screen), F7 (local logon), I (instant login)
2. Enter the sysop password

To customize the BBS (board name, access groups, message bases, etc.),
enter `IM` at the main prompt to open the Configuration Editor. Log off
with `O` (not F7) to save changes.

See the [Image BBS v3.0 Sysop Guide](https://8bitboyz.com/) for full
configuration details.

## Project Structure

```
src/c64u_bbs/
  cli/               # Click CLI commands
  client/            # C64U HTTP/REST client
  ftp/               # C64U FTP client
  bbs/               # BBS catalog, deployer, bootloader, BASIC tokenizer
  models/            # Drive modes, device config

assets/bbs/imagebbs/
  Master_D1_260125.d81    # Golden D1 (programs) — deploy-ready
  Master_D2_260125.d81    # Golden D2 (data) — deploy-ready
  upstream/               # Untouched originals from 8bitboyz.com
  PROVENANCE.md           # What changed, why, and where originals came from

docs/                # Documentation (GitHub Pages)
setup-bbs.sh              # BBS disk image manager (download, install, configure)
scripts/                  # Utility scripts
.githooks/                # Git hooks (secrets scan, docs consistency)
```

## Documentation

Full documentation: [brainvat.github.io/c64u-bbs](https://brainvat.github.io/c64u-bbs/)

## Credits

- **Image BBS v3.0** — (C) 2020-2025 NISSA BBS Software. Written by Ray Kelm, John Moore, Jack Followay, and Larry Hedman, with contributions by Al DeRosa, Bob Leary, Fred Dart, and Ryan Sherwood. Distributed by the [8-Bit Boyz](https://8bitboyz.com/) community.
- **C64 Ultimate** — by Gideon Zweijtzer, [ultimate64.com](https://ultimate64.com/)

## Repository

[github.com/brainvat/c64u-bbs](https://github.com/brainvat/c64u-bbs)
