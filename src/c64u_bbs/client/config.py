"""Configuration loading for the c64u CLI.

Cascade: CLI flags > environment variables > config file.
Config file: ~/.config/c64u-bbs/config.toml
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


CONFIG_DIR = Path.home() / ".config" / "c64u-bbs"
CONFIG_FILE = CONFIG_DIR / "config.toml"


@dataclass
class Config:
    """Client configuration for connecting to a C64U device."""

    host: str = ""
    password: str | None = None
    http_port: int = 80
    ftp_port: int = 21

    def is_configured(self) -> bool:
        return bool(self.host)


def load_config(
    *,
    host: str | None = None,
    password: str | None = None,
) -> Config:
    """Load configuration with cascade: explicit args > env vars > config file."""
    config = Config()

    # Layer 1: config file
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)
        device = data.get("device", {})
        config.host = device.get("host", "")
        config.password = device.get("password")
        config.http_port = device.get("http_port", 80)
        config.ftp_port = device.get("ftp_port", 21)

    # Layer 2: environment variables
    if env_host := os.environ.get("C64U_HOST"):
        config.host = env_host
    if env_password := os.environ.get("C64U_PASSWORD"):
        config.password = env_password

    # Layer 3: explicit CLI args (highest priority)
    if host is not None:
        config.host = host
    if password is not None:
        config.password = password

    return config


def save_config(config: Config) -> Path:
    """Write configuration to the config file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "[device]",
        f'host = "{config.host}"',
    ]
    if config.password:
        lines.append(f'password = "{config.password}"')
    if config.http_port != 80:
        lines.append(f"http_port = {config.http_port}")
    if config.ftp_port != 21:
        lines.append(f"ftp_port = {config.ftp_port}")
    lines.append("")

    CONFIG_FILE.write_text("\n".join(lines), encoding="utf-8")
    return CONFIG_FILE
