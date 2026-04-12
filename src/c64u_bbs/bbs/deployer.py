"""BBS deployment orchestration.

Handles modem configuration, program upload, and connection verification.
"""

from __future__ import annotations

import socket
import time

from c64u_bbs.client.c64u import C64UClient


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
