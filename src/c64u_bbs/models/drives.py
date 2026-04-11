"""Drive-related enums and options."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DriveMode(str, Enum):
    """Emulated drive type."""

    D1541 = "1541"
    D1571 = "1571"
    D1581 = "1581"


class MountMode(str, Enum):
    """Disk image mount mode."""

    READWRITE = "readwrite"
    READONLY = "readonly"
    UNLINKED = "unlinked"


@dataclass(frozen=True)
class MountOptions:
    """Options for mounting a disk image."""

    image: str
    drive: str = "a"
    image_type: str | None = None  # d64, g64, d71, g71, d81
    mode: MountMode = MountMode.READWRITE
