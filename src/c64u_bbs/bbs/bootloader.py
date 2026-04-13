"""Generate a tiny BASIC loader PRG that boots BBS software from disk.

The C64U's run_prg API injects a PRG into C64 memory, but BBS software
needs to boot from a mounted disk image (it chain-loads files via the
IEC bus). This module bridges the gap: it generates a one-line BASIC
program that LOADs the BBS boot file from the mounted disk.

The classic C64 chaining technique:
  0 LOAD"filename",device

LOAD without ,1 from within a BASIC program loads the file to $0801
and continues execution from the first line of the loaded program.
"""

from __future__ import annotations

from c64u_bbs.bbs.basic import tokenize_basic


def generate_boot_loader(boot_file: str, device: int = 8) -> bytes:
    """Generate a BASIC PRG that LOADs a file from disk and runs it.

    Args:
        boot_file: CBM filename to load (e.g. "+REBOOT", "IMAGE 1.2B")
        device: CBM device number (8 = drive A, 9 = drive B)

    Returns:
        Complete PRG file bytes (2-byte load address + tokenized BASIC).
    """
    lines = [
        f'0 LOAD"{boot_file}",{device}',
    ]
    return tokenize_basic(lines)
