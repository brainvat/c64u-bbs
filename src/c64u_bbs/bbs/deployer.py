"""BBS deployment orchestration.

Handles modem configuration, disk image upload, program boot, and
connection verification for deploying BBS software to the C64U.
"""

from __future__ import annotations

import socket
import time
from pathlib import Path

from c64u_bbs.bbs.bootloader import generate_boot_loader
from c64u_bbs.bbs.catalog import BBSPackage
from c64u_bbs.client.c64u import C64UClient
from c64u_bbs.ftp.client import C64UFTP


# Asset root: assets/bbs/<package>/ relative to project root
_ASSETS_ROOT = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "bbs"


class DeployError(Exception):
    """BBS deployment error."""


def configure_modem(
    client: C64UClient,
    *,
    port: int = 6400,
    save_to_flash: bool = False,
) -> None:
    """Configure the C64U modem for BBS operation.

    Sets up ACIA/SwiftLink at $DE00, configures listening port,
    enables RING for incoming connections.
    """
    settings = {
        "Modem Interface": "ACIA / SwiftLink",
        "ACIA (6551) Mapping": "DE00/NMI",
        "Hardware Mode": "SwiftLink",
        "Listening Port": str(port),
        "Do RING sequence (incoming)": "Enabled",
        "Drop connection on DTR low": "Enabled",
    }

    for item, value in settings.items():
        client.set_config("Modem Settings", item, value)

    if save_to_flash:
        client.save_config()


def verify_modem_port(host: str, port: int, timeout: float = 5.0) -> bool:
    """Check if the modem port is accepting TCP connections."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        # Try to read some data (the C64 program should send something)
        sock.settimeout(3.0)
        try:
            data = sock.recv(256)
            sock.close()
            return len(data) > 0
        except socket.timeout:
            # Connected but no data yet — still counts as a working connection
            sock.close()
            return True
    except (socket.error, OSError):
        return False


def wait_for_modem_ready(host: str, port: int, retries: int = 10, delay: float = 2.0) -> bool:
    """Wait for the modem port to become available after reset."""
    for _ in range(retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2.0)
            sock.connect((host, port))
            sock.close()
            return True
        except (socket.error, OSError):
            time.sleep(delay)
    return False


def get_assets_dir(package_name: str) -> Path:
    """Return the asset directory for a BBS package."""
    return _ASSETS_ROOT / package_name


def load_disk_image(package_name: str, filename: str) -> bytes:
    """Load a disk image file from the assets directory.

    Raises DeployError if the file is missing or empty.
    """
    path = get_assets_dir(package_name) / filename
    if not path.exists():
        raise DeployError(
            f"Disk image not found: {path}\n"
            f"Run: bash scripts/fetch-imagebbs.sh to download the disk images "
            f"into assets/bbs/{package_name}/"
        )
    data = path.read_bytes()
    if len(data) == 0:
        raise DeployError(f"Disk image is empty: {path}")
    return data


def deploy_bbs(
    client: C64UClient,
    package: BBSPackage,
    *,
    port: int = 6400,
    save_to_flash: bool = False,
    on_step: callable | None = None,
) -> None:
    """Deploy a BBS package to the C64U.

    Orchestrates the full deployment: reset, modem config, disk mounting,
    boot loader injection, and startup verification.

    Args:
        client: Connected C64UClient instance.
        package: BBS package to deploy (from the catalog).
        port: Modem listening port (default 6400).
        save_to_flash: Persist modem config to flash memory.
        on_step: Optional callback(step_name, detail) for progress reporting.
    """
    def step(name: str, detail: str = "") -> None:
        if on_step:
            on_step(name, detail)

    # 1. Reset C64 for clean state
    step("reset", "Resetting C64...")
    client.reset()
    time.sleep(2)

    # 2. Configure modem
    step("modem", f"Configuring modem (port {port})...")
    configure_modem(client, port=port, save_to_flash=save_to_flash)

    # 3. Upload disk images to SD card via FTP, then enable/mount drives
    sd_bbs_dir = "/SD/bbs"
    with C64UFTP(client.host) as ftp:
        for disk in package.disks:
            remote_path = f"{sd_bbs_dir}/{disk.filename}"
            step("upload", f"Uploading {disk.filename} to {remote_path}...")
            local_path = str(get_assets_dir(package.name) / disk.filename)
            ftp.upload(local_path, remote_path)

    for disk in package.disks:
        # Ensure the drive is enabled (Drive B is often disabled by default)
        drive_config = f"Drive {disk.drive.upper()} Settings"
        step("enable_drive", f"Enabling drive {disk.drive.upper()}...")
        client.set_config(drive_config, "Drive", "Enabled")

        step("drive_mode", f"Setting drive {disk.drive.upper()} to {disk.drive_mode.value} mode...")
        client.set_drive_mode(disk.drive, disk.drive_mode)

        step("mount", f"Mounting {disk.filename} on drive {disk.drive.upper()}...")
        client.mount_drive(disk.drive, f"{sd_bbs_dir}/{disk.filename}")

    time.sleep(1)

    # 4. Generate and run boot loader
    step("boot", f'Booting BBS (LOAD"{package.boot_file}",{package.boot_device})...')
    loader_prg = generate_boot_loader(package.boot_file, package.boot_device)
    client.upload_and_run_prg(loader_prg, "BBSBOOT.PRG")

    # 5. Wait for BBS to initialize and open modem port
    step("wait", "Waiting for BBS to start (this may take 30-60 seconds)...")
    ready = wait_for_modem_ready(client.host, port, retries=30, delay=2.0)
    if not ready:
        raise DeployError(
            f"BBS did not open modem port at {client.host}:{port} within 60 seconds. "
            f"Check the C64U screen for errors."
        )
