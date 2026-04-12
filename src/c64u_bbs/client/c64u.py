"""C64 Ultimate REST API client.

Communicates with the C64U device over HTTP on port 80.
API docs: https://1541u-documentation.readthedocs.io/en/latest/api/api_calls.html
"""

from __future__ import annotations

import httpx

from c64u_bbs.models.device import DeviceInfo, DriveInfo
from c64u_bbs.models.drives import DriveMode, MountMode


class C64UError(Exception):
    """Base exception for C64U API errors."""


class C64UConnectionError(C64UError):
    """Cannot reach the C64U device."""


class C64UAuthError(C64UError):
    """Authentication failed (wrong or missing password)."""


class C64UAPIError(C64UError):
    """The API returned an error response."""

    def __init__(self, status_code: int, detail: str = ""):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"HTTP {status_code}: {detail}")


class C64UClient:
    """Synchronous HTTP client for the C64 Ultimate REST API.

    Args:
        host: IP address or hostname of the C64U device.
        password: Network password (sent via X-Password header). None if no password set.
        port: HTTP port (default 80).
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        host: str,
        password: str | None = None,
        port: int = 80,
        timeout: float = 10.0,
    ):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/v1"

        headers = {}
        if password:
            headers["X-Password"] = password

        self._client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> C64UClient:
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        content: bytes | None = None,
        files: dict | None = None,
    ) -> httpx.Response:
        """Make an API request with standard error handling."""
        try:
            response = self._client.request(
                method,
                path,
                params=params,
                content=content,
                files=files,
            )
        except httpx.ConnectError as e:
            raise C64UConnectionError(
                f"Cannot connect to C64U at {self.host}:{self.port}: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise C64UConnectionError(
                f"Timeout connecting to C64U at {self.host}:{self.port}: {e}"
            ) from e

        if response.status_code == 403:
            raise C64UAuthError(
                "Authentication failed. Check your C64U network password."
            )
        if response.status_code >= 400:
            detail = ""
            try:
                data = response.json()
                errors = data.get("errors", [])
                if errors:
                    detail = "; ".join(errors)
            except Exception:
                detail = response.text[:200]
            raise C64UAPIError(response.status_code, detail)

        return response

    # ── Device Info ──────────────────────────────────────────

    def get_info(self) -> DeviceInfo:
        """Get device identification and firmware info. GET /v1/info"""
        response = self._request("GET", "/info")
        return DeviceInfo.from_api(response.json())

    # ── Machine Control ─────────────────────────────────────

    def reset(self) -> None:
        """Reset the C64. PUT /v1/machine:reset"""
        self._request("PUT", "/machine:reset")

    def reboot(self) -> None:
        """Full reboot with cartridge re-initialization. PUT /v1/machine:reboot"""
        self._request("PUT", "/machine:reboot")

    # ── Drive Management ────────────────────────────────────

    def list_drives(self) -> list[DriveInfo]:
        """List all drives with status. GET /v1/drives"""
        response = self._request("GET", "/drives")
        data = response.json()
        drives = []

        # API returns {"drives": [{"a": {...}}, {"b": {...}}, ...]}
        drive_list = data.get("drives", [])
        if isinstance(drive_list, list):
            for entry in drive_list:
                if isinstance(entry, dict):
                    for drive_id, drive_data in entry.items():
                        if isinstance(drive_data, dict):
                            drives.append(DriveInfo.from_api(drive_id, drive_data))
        else:
            # Fallback: flat dict format (older firmware?)
            for drive_id, drive_data in data.items():
                if isinstance(drive_data, dict):
                    drives.append(DriveInfo.from_api(drive_id, drive_data))

        return drives

    def mount_drive(
        self,
        drive: str,
        image: str,
        *,
        mode: MountMode = MountMode.READWRITE,
    ) -> None:
        """Mount a disk image from the device filesystem. PUT /v1/drives/{drive}:mount"""
        params = {"image": image, "mode": mode.value}
        self._request("PUT", f"/drives/{drive}:mount", params=params)

    def upload_and_mount(
        self,
        drive: str,
        data: bytes,
        filename: str,
        *,
        mode: MountMode = MountMode.READWRITE,
    ) -> None:
        """Upload and mount a disk image. POST /v1/drives/{drive}:mount"""
        self._request(
            "POST",
            f"/drives/{drive}:mount",
            params={"mode": mode.value},
            files={"file": (filename, data)},
        )

    def unmount_drive(self, drive: str) -> None:
        """Remove/eject mounted disk. PUT /v1/drives/{drive}:remove"""
        self._request("PUT", f"/drives/{drive}:remove")

    def set_drive_mode(self, drive: str, mode: DriveMode) -> None:
        """Change drive emulation type. PUT /v1/drives/{drive}:set_mode"""
        self._request("PUT", f"/drives/{drive}:set_mode", params={"mode": mode.value})

    # ── Program Runner ──────────────────────────────────────

    def run_prg(self, path: str) -> None:
        """Load and auto-run a PRG from device filesystem. PUT /v1/runners:run_prg"""
        self._request("PUT", "/runners:run_prg", params={"file": path})

    def upload_and_run_prg(self, data: bytes, filename: str) -> None:
        """Upload and auto-run a PRG. POST /v1/runners:run_prg"""
        self._request("POST", "/runners:run_prg", files={"file": (filename, data)})

    # ── Configuration ───────────────────────────────────────

    def list_config_categories(self) -> list[str]:
        """List config categories. GET /v1/configs"""
        response = self._request("GET", "/configs")
        return response.json().get("categories", [])

    def get_config(self, category: str | None = None) -> dict:
        """Read device configuration. GET /v1/configs or GET /v1/configs/{category}"""
        if category:
            response = self._request("GET", f"/configs/{category}")
        else:
            response = self._request("GET", "/configs")
        return response.json()

    def set_config(self, category: str, item: str, value: str) -> None:
        """Set a device configuration value. PUT /v1/configs/{category}/{item}"""
        self._request("PUT", f"/configs/{category}/{item}", params={"value": value})

    def save_config(self) -> None:
        """Persist configuration to flash. PUT /v1/configs:save_to_flash"""
        self._request("PUT", "/configs:save_to_flash")
