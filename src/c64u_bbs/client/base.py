"""Abstract backend protocol for C64 device communication.

This Protocol defines the contract that any backend (C64U, VICE, etc.)
must implement. The CLI and BBS deployer depend on this interface,
not on any concrete implementation.
"""

from __future__ import annotations

from typing import Protocol

from c64u_bbs.models.device import DeviceInfo, DriveInfo
from c64u_bbs.models.drives import DriveMode, MountMode


class DeviceBackend(Protocol):
    """Protocol for communicating with a C64 device."""

    def get_info(self) -> DeviceInfo:
        """Get device identification and firmware info."""
        ...

    def reset(self) -> None:
        """Reset the C64."""
        ...

    def list_drives(self) -> list[DriveInfo]:
        """List all emulated drives and their status."""
        ...

    def mount_drive(
        self,
        drive: str,
        image: str,
        *,
        mode: MountMode = MountMode.READWRITE,
    ) -> None:
        """Mount a disk image on a drive (from device filesystem path)."""
        ...

    def unmount_drive(self, drive: str) -> None:
        """Remove/eject the mounted disk from a drive."""
        ...

    def set_drive_mode(self, drive: str, mode: DriveMode) -> None:
        """Change a drive's emulated type (1541/1571/1581)."""
        ...

    def run_prg(self, path: str) -> None:
        """Load and auto-run a PRG from the device filesystem."""
        ...

    def upload_and_run_prg(self, data: bytes, filename: str) -> None:
        """Upload a PRG and auto-run it."""
        ...

    def list_config_categories(self) -> list[str]:
        """List available config categories."""
        ...

    def get_config(self, category: str | None = None) -> dict:
        """Read device configuration, optionally filtered by category."""
        ...

    def set_config(self, category: str, item: str, value: str) -> None:
        """Set a single device configuration value."""
        ...

    def save_config(self) -> None:
        """Persist current configuration to flash."""
        ...
