"""FTP client for the C64 Ultimate.

Wraps Python's ftplib.FTP to provide file management on the C64U
filesystem (SD card, Flash, Temp, USB storage).
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from ftplib import FTP, error_perm
from pathlib import PurePosixPath


class C64UFTPError(Exception):
    """Base exception for C64U FTP errors."""


@dataclass(frozen=True)
class FileEntry:
    """A file or directory entry from the C64U filesystem."""

    name: str
    size: int
    is_dir: bool
    modified: str  # raw date string from FTP listing

    @classmethod
    def from_list_line(cls, line: str) -> FileEntry:
        """Parse a Unix-style FTP LIST line."""
        parts = line.split(None, 8)
        if len(parts) < 9:
            # Fallback for short lines
            return cls(name=parts[-1] if parts else line, size=0, is_dir=False, modified="")

        perms = parts[0]
        size = int(parts[4]) if parts[4].isdigit() else 0
        date_str = f"{parts[5]} {parts[6]} {parts[7]}"
        name = parts[8]
        is_dir = perms.startswith("d")

        return cls(name=name, size=size, is_dir=is_dir, modified=date_str)


class C64UFTP:
    """FTP client for the C64 Ultimate.

    Args:
        host: IP address or hostname of the C64U.
        port: FTP port (default 21).
        timeout: Connection timeout in seconds.
    """

    def __init__(self, host: str, port: int = 21, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._ftp: FTP | None = None

    def connect(self) -> None:
        """Open FTP connection."""
        self._ftp = FTP()
        try:
            self._ftp.connect(self.host, self.port, timeout=self.timeout)
            self._ftp.login()  # C64U FTP has no auth (or uses device password)
        except Exception as e:
            self._ftp = None
            raise C64UFTPError(f"Cannot connect to FTP at {self.host}:{self.port}: {e}") from e

    def close(self) -> None:
        """Close FTP connection."""
        if self._ftp:
            try:
                self._ftp.quit()
            except Exception:
                try:
                    self._ftp.close()
                except Exception:
                    pass
            self._ftp = None

    def __enter__(self) -> C64UFTP:
        self.connect()
        return self

    def __exit__(self, *args) -> None:
        self.close()

    @property
    def ftp(self) -> FTP:
        if self._ftp is None:
            raise C64UFTPError("Not connected. Use 'with C64UFTP(...) as ftp:' or call connect().")
        return self._ftp

    def list_dir(self, path: str = "/") -> list[FileEntry]:
        """List directory contents."""
        lines: list[str] = []
        try:
            self.ftp.dir(path, lines.append)
        except error_perm as e:
            raise C64UFTPError(f"Cannot list {path}: {e}") from e

        entries = []
        for line in lines:
            if line.strip():
                entries.append(FileEntry.from_list_line(line))
        return entries

    def upload(self, local_path: str, remote_path: str) -> int:
        """Upload a local file. Returns bytes transferred."""
        with open(local_path, "rb") as f:
            data = f.read()

        try:
            self.ftp.storbinary(f"STOR {remote_path}", io.BytesIO(data))
        except error_perm as e:
            raise C64UFTPError(f"Upload failed for {remote_path}: {e}") from e

        return len(data)

    def download(self, remote_path: str, local_path: str) -> int:
        """Download a remote file. Returns bytes transferred."""
        buf = io.BytesIO()
        try:
            self.ftp.retrbinary(f"RETR {remote_path}", buf.write)
        except error_perm as e:
            raise C64UFTPError(f"Download failed for {remote_path}: {e}") from e

        data = buf.getvalue()
        with open(local_path, "wb") as f:
            f.write(data)

        return len(data)

    def mkdir(self, path: str) -> None:
        """Create a directory."""
        try:
            self.ftp.mkd(path)
        except error_perm as e:
            raise C64UFTPError(f"Cannot create directory {path}: {e}") from e

    def delete(self, path: str) -> None:
        """Delete a file."""
        try:
            self.ftp.delete(path)
        except error_perm as e:
            raise C64UFTPError(f"Cannot delete {path}: {e}") from e

    def rmdir(self, path: str) -> None:
        """Remove a directory."""
        try:
            self.ftp.rmd(path)
        except error_perm as e:
            raise C64UFTPError(f"Cannot remove directory {path}: {e}") from e

    def size(self, path: str) -> int:
        """Get file size in bytes."""
        try:
            return self.ftp.size(path) or 0
        except error_perm as e:
            raise C64UFTPError(f"Cannot get size of {path}: {e}") from e
