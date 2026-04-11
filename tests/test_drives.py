"""Tests for drive management."""

from __future__ import annotations

import httpx
import pytest

from c64u_bbs.client.c64u import C64UClient
from c64u_bbs.models.device import DriveInfo
from c64u_bbs.models.drives import DriveMode, MountMode
from tests.conftest import load_fixture, mock_transport


@pytest.fixture
def drives_client(sample_info: dict, sample_drives: dict) -> C64UClient:
    """Client with mocked drive endpoints."""
    received = {}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        received["last_path"] = path
        received["last_method"] = request.method
        received["last_params"] = dict(request.url.params)

        if path.endswith("/drives") and request.method == "GET":
            return httpx.Response(200, json=sample_drives)
        if ":mount" in path and request.method == "PUT":
            return httpx.Response(200, json={"errors": []})
        if ":mount" in path and request.method == "POST":
            return httpx.Response(200, json={"errors": []})
        if ":remove" in path:
            return httpx.Response(200, json={"errors": []})
        if ":set_mode" in path:
            return httpx.Response(200, json={"errors": []})
        if ":reset" in path:
            return httpx.Response(200, json={"errors": []})
        if path.endswith("/info"):
            return httpx.Response(200, json=sample_info)
        return httpx.Response(404, json={"errors": ["Not found"]})

    transport = httpx.MockTransport(handler)
    client = C64UClient.__new__(C64UClient)
    client.host = "192.168.1.64"
    client.port = 80
    client.base_url = "http://192.168.1.64:80/v1"
    client._client = httpx.Client(base_url=client.base_url, transport=transport)
    client._received = received
    return client


class TestListDrives:
    def test_returns_drive_list(self, drives_client: C64UClient):
        drives = drives_client.list_drives()
        assert len(drives) == 2
        assert all(isinstance(d, DriveInfo) for d in drives)

    def test_parses_drive_a(self, drives_client: C64UClient):
        drives = drives_client.list_drives()
        drive_a = next(d for d in drives if d.drive_id == "a")
        assert drive_a.enabled is True
        assert drive_a.bus_id == 8
        assert drive_a.drive_type == "1541"
        assert drive_a.mounted_image == "/usb0/games/test.d64"
        assert drive_a.rom_file == "1541.rom"

    def test_parses_drive_b(self, drives_client: C64UClient):
        drives = drives_client.list_drives()
        drive_b = next(d for d in drives if d.drive_id == "b")
        assert drive_b.enabled is False
        assert drive_b.bus_id == 9
        assert drive_b.drive_type == "1541"
        assert drive_b.mounted_image == ""


class TestMountDrive:
    def test_mount_with_device_path(self, drives_client: C64UClient):
        drives_client.mount_drive("a", "/usb0/disks/game.d64")
        assert drives_client._received["last_method"] == "PUT"
        assert drives_client._received["last_params"]["image"] == "/usb0/disks/game.d64"
        assert drives_client._received["last_params"]["mode"] == "readwrite"

    def test_mount_readonly(self, drives_client: C64UClient):
        drives_client.mount_drive("a", "/usb0/disks/game.d64", mode=MountMode.READONLY)
        assert drives_client._received["last_params"]["mode"] == "readonly"

    def test_unmount(self, drives_client: C64UClient):
        drives_client.unmount_drive("a")
        assert drives_client._received["last_method"] == "PUT"
        assert ":remove" in drives_client._received["last_path"]

    def test_set_drive_mode(self, drives_client: C64UClient):
        drives_client.set_drive_mode("a", DriveMode.D1581)
        assert drives_client._received["last_params"]["mode"] == "1581"
