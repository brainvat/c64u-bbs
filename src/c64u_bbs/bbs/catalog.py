"""BBS package catalog.

Registry of known BBS software packages that can be deployed to the C64U.
Each entry describes the disk images, boot process, and modem configuration
needed for a particular BBS.
"""

from __future__ import annotations

from dataclasses import dataclass

from c64u_bbs.models.drives import DriveMode


@dataclass(frozen=True)
class DiskImage:
    """A disk image that is part of a BBS package."""

    filename: str          # e.g. "color64-sys.d64"
    drive: str             # "a" or "b"
    drive_mode: DriveMode  # D1541, D1571, or D1581
    description: str       # human-readable purpose


@dataclass(frozen=True)
class BBSPackage:
    """A BBS software package that can be deployed."""

    name: str              # short identifier, e.g. "color64"
    display_name: str      # human-readable, e.g. "Color 64 BBS v7.37"
    version: str
    license: str           # e.g. "Public Domain", "GPL-2.0+"
    boot_file: str         # filename on disk to LOAD, e.g. "+REBOOT"
    boot_device: int       # CBM device number (8 = drive A, 9 = drive B)
    disks: tuple[DiskImage, ...]
    description: str       # short summary for `bbs list`


CATALOG: dict[str, BBSPackage] = {
    "imagebbs": BBSPackage(
        name="imagebbs",
        display_name="Image BBS v3.0",
        version="3.0",
        license="Public Domain",
        boot_file="IMAGE 3.0",
        boot_device=8,
        disks=(
            DiskImage(
                "Master_D1_260125.d81", "a", DriveMode.D1581,
                "Programs (boot, ML, modules)",
            ),
            DiskImage(
                "Master_D2_260125.d81", "b", DriveMode.D1581,
                "Data (menus, screens, config)",
            ),
        ),
        description=(
            "Actively maintained BBS by the 8-Bit Boyz community. "
            "SwiftLink support at $DE00. Feb 2026 release."
        ),
    ),
}


def get_package(name: str) -> BBSPackage:
    """Look up a BBS package by name.

    Raises KeyError if the package is not in the catalog.
    """
    return CATALOG[name]


def list_packages() -> list[BBSPackage]:
    """Return all available BBS packages."""
    return list(CATALOG.values())
