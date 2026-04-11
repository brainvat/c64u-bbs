"""Data models for C64U device information."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceInfo:
    """Information returned by GET /v1/info."""

    product: str
    firmware_version: str
    fpga_version: str
    core_version: str  # U64 only, empty string for UII+
    hostname: str
    unique_id: str

    @classmethod
    def from_api(cls, data: dict) -> DeviceInfo:
        return cls(
            product=data.get("product", ""),
            firmware_version=data.get("firmware_version", data.get("version", "")),
            fpga_version=data.get("fpga_version", data.get("fpga", "")),
            core_version=data.get("core_version", data.get("core", "")),
            hostname=data.get("hostname", ""),
            unique_id=data.get("unique_id", ""),
        )


@dataclass(frozen=True)
class DriveInfo:
    """Information about a single emulated drive."""

    drive_id: str  # "a", "b", or "softiec"
    enabled: bool
    bus_id: int
    drive_type: str  # "1541", "1571", "1581"
    rom_file: str
    mounted_image: str

    @classmethod
    def from_api(cls, drive_id: str, data: dict) -> DriveInfo:
        # The API returns image info as image_file/image_path (or image in some firmware)
        mounted = data.get("image_file", "") or data.get("image", "")
        image_path = data.get("image_path", "")
        if image_path and mounted:
            mounted = f"{image_path}{mounted}"

        return cls(
            drive_id=drive_id,
            enabled=data.get("enabled", False),
            bus_id=data.get("bus_id", 8),
            drive_type=data.get("type", ""),
            rom_file=data.get("rom", ""),
            mounted_image=mounted,
        )
