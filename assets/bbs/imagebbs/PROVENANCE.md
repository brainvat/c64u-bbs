# Image BBS 3.0 Disk Image Provenance

## Origin

Image BBS v3.0, February 2026 release.

- **Website:** https://8bitboyz.com
- **Download:** https://8bitboyz.com/download/image-3-0-install-february-2026/
- **Authors:** Ray Kelm, John Moore, Jack Followay, Larry Hedman
- **Copyright:** (C) 2020-2025 NISSA BBS Software
- **License:** Image BBS v1.2a is explicitly public domain; v3.0 is freely distributed by the 8-Bit Boyz community

## Directory Layout

```
upstream/                    # Untouched files from the download
  Master_D1_260125.d81      # Program disk (boot, ML, modules)
  Master_D2_260125.d81      # Data disk (menus, screens, config)
  3.0 utilities.d81         # Utility disk (fcopy+, copy-all, etc.)
  _Read Me 2026_.txt        # Original readme from the download

Master_D1_260125.d81        # Golden D1 (configured for C64U deploy)
Master_D2_260125.d81        # Golden D2 (configured for C64U deploy)
```

## Golden Image Changes

The golden images are derived from the upstream originals. The deploy
pipeline (`c64u bbs deploy`) uploads these to the C64 Ultimate.

### D1 (Program Disk) — `Master_D1_260125.d81`

Changes from upstream:

- **`bd.data`** (SEQ, 1 block) — added by the Image BBS setup wizard.
  Contains drive assignment table (System=9/0, E-Mail=9/0, Etcetera=9/0,
  Directory=9/0, Program=8/0, User=9/0). This file does not exist on the
  upstream D1.

All other files are identical to upstream.

### D2 (Data Disk) — `Master_D2_260125.d81`

Changes from upstream:

- **`e.modem`** (PRG, 1 block) — replaced. Upstream is 3 blocks (stock
  modem config). Golden version is 1 block, configured for ACIA/SwiftLink
  at $DE00.
- **`e.i.modem`** (REL, 9 blocks) — added. Modem initialization and
  answer configuration for SwiftLink. Transplanted from a prior
  C64U-configured image. This is the file that tells the BBS how to
  detect and answer incoming calls via the ACIA.
- **`u.config`** (REL, 4 blocks) — added. User records file created by the
  setup wizard. Contains sysop account (user #1).
- **`u.index`** (PRG, 1 block) — added. User index created by the setup
  wizard.
- **`u.weedinfo`** (PRG, 1 block) — added. User maintenance data created
  by the setup wizard.
- **`e.stats`** (REL, 4 blocks) — added. System statistics.
- **`e.data`** (REL, 10 blocks) — added. System data.
- **`e.access`** (REL, 7 blocks) — added. Access level definitions.
- **`e.log`**, **`e.log2`**, **`e.idle 2`** — added. Log and idle screen files.
- **`e.last`** (PRG, 3 blocks) — added. Last callers list.

All `s.*` files (menus, screens, config) and `today.*` files are
identical to upstream.

## How the Golden Images Were Created

1. Fresh upstream D81 images were booted in VICE (x64sc 3.9)
2. Image BBS setup wizard was run: option 1 (Configure a New BBS)
3. Drive assignments: Program=8/0, all others=9/0, Clock=Manual, SwiftLink=1
4. Sysop account created and verified (instant login successful)
5. Clean logoff with user file update
6. `e.modem` (PRG) from a prior C64U-configured golden image was
   transplanted onto the VICE D2 (replacing the stock 3-block version)
7. `e.i.modem` (REL) from the same C64U-configured image was transplanted
   via sector-level copy (sectors were free at the same locations on the
   new D2, so no relocation was needed)
8. Result verified: BBS boots in VICE with sysop login, and answers
   incoming modem connections on C64U

## Post-Deploy Steps

After deploying golden images to C64U:

1. BBS boots and reaches idle screen automatically
2. Modem answers incoming TCP connections (SwiftLink pre-configured)
3. Callers connect via `telnet <c64u-ip> 6400`
