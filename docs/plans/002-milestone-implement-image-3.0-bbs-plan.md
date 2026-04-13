# Phase 5b: Deploy Image BBS 3.0 to C64U

## Context

Phase 5a proved the modem pipeline works (ACIA at $DE00, SwiftLink, TCP on port 6400, auto-answer PRG). Phase 5b deploys real BBS software.

### Dead Ends (archived in `deadends/cbase-color64` branch)
- **Color 64 v7.37:** Public domain but NO SwiftLink support (user-port only, 2400 baud max). Research agents gave wrong info.
- **C\*Base v3.3.7:** GPL-2.0+, has SwiftLink driver, but `configure 1.05` program has a broken save function (silently fails, no disk I/O). We proved the C64U disk writes work fine (OPEN/PRINT#/CLOSE test succeeded), so it's a bug in the configure program itself.

### Decision: Image BBS v3.0 (February 2026 release)
- **Actively maintained** by 8-Bit Boyz community (patches through Dec 2025)
- **SwiftLink support built in** — sysop guide has explicit setup instructions (page 14-15)
- **License:** v1.2a explicitly public domain; v3.0 freely distributed (no formal license file)
- **Two D81 disks:** Disk 1 = programs (498 blocks free), Disk 2 = data/menus/screens (2169 blocks free)
- **Sysop guide PDF included** with step-by-step setup instructions

## What's Already Built (on `feature/image-bbs` branch)

All pipeline code is **generic** and works with any BBS package. 53 tests passing.

### Files (all under `src/c64u_bbs/`):
| File | Purpose | Status |
|------|---------|--------|
| `bbs/basic.py` | BASIC tokenizer + PETSCII utils (extracted from autoanswer.py) | Done |
| `bbs/bootloader.py` | Generates one-line BASIC loader PRGs for any boot file | Done |
| `bbs/catalog.py` | BBS package registry — has Image BBS entry (needs boot_file verified) | Done, needs update |
| `bbs/deployer.py` | `deploy_bbs()` orchestration: reset → modem → mount → boot → verify | Done |
| `bbs/autoanswer.py` | Phase 5a auto-answer (imports from basic.py now) | Done |
| `cli/commands/bbs.py` | CLI: `bbs list`, `bbs deploy`, `bbs connect`, `bbs test/status/stop` | Done |

### Tests (all under `tests/`):
| File | Tests | Status |
|------|-------|--------|
| `test_bootloader.py` | 10 tests — PRG generation, filenames, device numbers | Passing |
| `test_catalog.py` | 7 tests — catalog entries, get_package, list_packages | Passing |
| `test_deployer.py` | 9 tests — deploy orchestration with mocked client | Passing |
| (existing) | 26 tests — client, drives, FTP, runner | Passing |

### Current catalog entry (may need adjustment):
```python
"imagebbs": BBSPackage(
    name="imagebbs",
    display_name="Image BBS v3.0",
    version="3.0",
    license="Public Domain",
    boot_file="image 3.0",       # ← verified on disk
    boot_device=8,
    disks=(DiskImage("imagebbs-sys.d81", "a", DriveMode.D1581, "System disk"),),
    description="Actively maintained BBS by the 8-Bit Boyz community. ..."
)
```

**Note:** Image BBS needs TWO D81 disks (programs + data). The catalog entry currently has one disk. This needs updating — either mount both on drives A+B, or combine onto one disk if possible.

## Source Files (already on local machine)

```
/Users/ahammock/Desktop/C64/BBS/Image-Instal-3/
├── Master_D1_260125.d81          # 819200 bytes — programs (boot, ML, modules)
├── Master_D2_260125.d81          # 819200 bytes — data (menus, screens, config)
├── 3.0 utilities.d81             # 819200 bytes — sysop tools
├── Image-3.0-Sysop-Guide.pdf    # 1080818 bytes — full documentation
└── _Read Me 2026_.txt            # release notes
```

### Key files on Master Disk 1:
- `image 3.0` (17 blocks, PRG) — **boot file**
- `im` (62 blocks) — BASIC routines
- `ml 3.0` (100 blocks) — machine language core
- `ml.rs232` (6 blocks) — RS-232 driver (default = user port; swap for SwiftLink variant)
- `i/su.config` (31 blocks) — configuration/setup program
- `boot 3.0` (1 block) — autostart loader
- `sub.modem` (12 blocks) — modem subroutines

### Key files on Master Disk 2:
- `s.config` (1 block, SEQ) — BBS configuration data
- `e.modem` (3 blocks) — modem configuration data  
- `s.welcome *` — welcome screens (PETSCII + ANSI variants)
- `s.menu *` — menu screens
- `s.logon *` — login screens
- Various SEQ display files

## C64U Device

- **IP:** 192.168.50.124 (moved from 192.168.1.172)
- **Hostname:** C64U-Bean-Thad
- **SD card:** `/SD/bbs/` exists (has leftover cbase.d81 and cbase_side1.d64 to clean up)
- **Modem config:** ACIA/SwiftLink at $DE00, port 6400 (from Phase 5a)

## Implementation Steps

### Step 1: Prepare disk images
1. Copy `Master_D1_260125.d81` and `Master_D2_260125.d81` to `assets/bbs/imagebbs/`
2. Update `.gitignore` if needed (D81 files are ~800KB each, acceptable for repo)
3. Clean up old C\*Base files from `assets/bbs/`

### Step 2: Update catalog entry  
1. Update `catalog.py` with correct Image BBS entry:
   - Two disks: D1 on drive A (device 8), D2 on drive B (device 9)
   - Boot file: `image 3.0`
   - Both drives in 1581 mode
2. Update `test_catalog.py` to match
3. Verify: `venv/bin/pytest -x -q` — all tests pass
4. Verify: `venv/bin/c64u bbs list` shows Image BBS

### Step 3: Upload and first boot on C64U
1. Clean up C64U: `c64u files rm /SD/bbs/cbase.d81` and `cbase_side1.d64`
2. Upload both D81s: `c64u files put` to `/SD/bbs/`
3. Set drives: `c64u drives mode a 1581` and `c64u drives mode b 1581`
4. Mount: `c64u drives mount a /SD/bbs/Master_D1.d81` and B for D2
5. Reset C64: `c64u reset`
6. Boot: On C64U screen, type `LOAD"IMAGE 3.0",8` then `RUN`
7. **Expected:** Image BBS starts loading (chain-loads `im`, `ml 3.0`, etc.)
8. Since no config exists yet, it should enter the **Configuration Setup** wizard

### Step 4: Initial BBS configuration on C64U
The sysop guide (page 4+) describes the setup wizard. Key answers:

**Installation method:** Choose `1` (Configure a New BBS)

**Drive designation:** 
- All on device 8 (drive A) and device 9 (drive B)
- System files: device 8
- Data files: device 9

**SwiftLink selection (Step 9 in guide):**
- Choose option `1` for SwiftLink (not 0 for user port)

**Modem Config (Step 11, menu item J):**
Use "CARTRIDGE PORT: Swiftlink" settings from sysop guide page 15:
- Modem Brand/Name: `SWIFTLINK`
- Author: `CMD`  
- Custom Init String: (just press RETURN)
- Max Connection Rate: `6` (38.4k)
- Hang-Up Method: `D`
- Auto-Answer: `A`
- ATH after ESCape: `H`
- Phone: `H`
- Need 0 after ATH: `0`
- ATH in Init String: `H`
- ATX Setting: `1`
- DTR Normal/Reverse: `N`
- CCITT or Bell: `0`
- RS232 Interface Type: `1`
- Caller ID: `0`

**After config:** The BBS should reach its idle/wait-for-call screen.

### Step 5: Verify modem connectivity
1. From another terminal: `telnet 192.168.50.124 6400`
2. Should see the Image BBS login/welcome screen
3. Or use: `c64u bbs status` to check modem port

### Step 6: Save configured disk images
1. Unmount drives on C64U
2. Download the now-configured D81s from `/SD/bbs/` via FTP
3. Replace the stock images in `assets/bbs/imagebbs/` with configured versions
4. These become the "golden" pre-configured images for `c64u bbs deploy`

### Step 7: Test the deploy pipeline
1. Reset everything on C64U
2. Run: `c64u bbs deploy imagebbs`
3. The pipeline should: reset → configure modem → mount disks → boot → verify
4. Verify: `telnet 192.168.50.124 6400` reaches Image BBS

### Step 8: Update boot loader for two-disk setup
The current `deploy_bbs()` in `deployer.py` already supports multiple disks in the catalog entry. But verify the boot loader works:
- `generate_boot_loader("image 3.0", device=8)` produces correct PRG
- The boot program chain-loads from device 8, and data files are on device 9

### Step 9: Commit and clean up
1. Run full test suite: `venv/bin/pytest -x -q`
2. Commit configured D81 images + catalog updates to `feature/image-bbs`
3. Merge to `main` when everything works
4. Create journal entry documenting the deployment

## Gotchas and Risks

1. **Two-disk boot:** Image BBS expects data files on a separate device. The boot program on D1 will try to read config from D2. Both must be mounted BEFORE booting.

2. **`ml.rs232` driver swap:** The stock `ml.rs232` on D1 is the user-port driver. The SwiftLink config (step 9 in setup) should handle selecting the right driver automatically. If not, we may need to manually rename `ml.rs232/swift` to `ml.rs232` on the D1 image. Check whether the setup wizard does this.

3. **Boot file name:** Verified on disk as `image 3.0` (lowercase, with space). The BASIC loader must use this exact name: `LOAD"image 3.0",8`.

4. **C64U modem vs Hayes modem:** Image BBS expects Hayes AT commands by default. The C64U's modem emulation handles AT commands (ATA for answer, ATH for hangup). The SwiftLink config in the sysop guide should work, but we may need to adjust for C64U-specific behavior.

5. **Config save:** Unlike C\*Base, Image BBS saves config to `s.config` (SEQ file on D2) and `e.modem` (PRG on D2). We proved C64U disk writes work, so this should be fine. Watch for confirmation messages during save.

## Verification Checklist

- [ ] `c64u bbs list` shows Image BBS with correct details
- [ ] `c64u bbs deploy imagebbs` completes all steps
- [ ] `telnet 192.168.50.124 6400` reaches Image BBS login screen
- [ ] Can log in as sysop from telnet
- [ ] `c64u bbs status` reports ONLINE
- [ ] `c64u bbs stop` resets the C64
- [ ] All 53+ tests pass
- [ ] Configured D81 images committed to repo
