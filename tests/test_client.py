"""Tests for the C64U REST API client."""

from __future__ import annotations

import httpx
import pytest

from c64u_bbs.client.c64u import (
    C64UAPIError,
    C64UAuthError,
    C64UClient,
    C64UConnectionError,
)
from c64u_bbs.models.device import DeviceInfo
from tests.conftest import mock_transport


class TestGetInfo:
    def test_returns_device_info(self, mock_client: C64UClient, sample_info: dict):
        info = mock_client.get_info()
        assert isinstance(info, DeviceInfo)
        assert info.product == "C64 Ultimate"
        assert info.firmware_version == "3.14"
        assert info.fpga_version == "121"
        assert info.core_version == "1.47"
        assert info.hostname == "C64U-Bean-Thad"
        assert info.unique_id == "25FF7F"

    def test_auth_header_sent(self, sample_info: dict):
        """Client with password sends X-Password header."""
        received_headers = {}

        def handler(request: httpx.Request) -> httpx.Response:
            received_headers.update(dict(request.headers))
            return httpx.Response(200, json=sample_info)

        transport = httpx.MockTransport(handler)
        client = C64UClient.__new__(C64UClient)
        client.host = "192.168.1.64"
        client.port = 80
        client.base_url = "http://192.168.1.64:80/v1"
        client._client = httpx.Client(
            base_url=client.base_url,
            headers={"X-Password": "secret123"},
            transport=transport,
        )

        client.get_info()
        assert received_headers.get("x-password") == "secret123"

    def test_no_auth_header_without_password(self, sample_info: dict):
        """Client without password does not send X-Password header."""
        received_headers = {}

        def handler(request: httpx.Request) -> httpx.Response:
            received_headers.update(dict(request.headers))
            return httpx.Response(200, json=sample_info)

        transport = httpx.MockTransport(handler)
        client = C64UClient.__new__(C64UClient)
        client.host = "192.168.1.64"
        client.port = 80
        client.base_url = "http://192.168.1.64:80/v1"
        client._client = httpx.Client(
            base_url=client.base_url,
            transport=transport,
        )

        client.get_info()
        assert "x-password" not in received_headers

    def test_auth_error_on_403(self):
        transport = mock_transport({"/info": (403, "Forbidden")})
        client = C64UClient.__new__(C64UClient)
        client.host = "192.168.1.64"
        client.port = 80
        client.base_url = "http://192.168.1.64:80/v1"
        client._client = httpx.Client(base_url=client.base_url, transport=transport)

        with pytest.raises(C64UAuthError, match="Authentication failed"):
            client.get_info()

    def test_api_error_on_500(self):
        transport = mock_transport({
            "/info": (500, {"errors": ["Internal error"]}),
        })
        client = C64UClient.__new__(C64UClient)
        client.host = "192.168.1.64"
        client.port = 80
        client.base_url = "http://192.168.1.64:80/v1"
        client._client = httpx.Client(base_url=client.base_url, transport=transport)

        with pytest.raises(C64UAPIError) as exc_info:
            client.get_info()
        assert exc_info.value.status_code == 500
        assert "Internal error" in exc_info.value.detail

    def test_connection_error(self):
        """ConnectError is wrapped in C64UConnectionError."""

        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("Connection refused")

        transport = httpx.MockTransport(handler)
        client = C64UClient.__new__(C64UClient)
        client.host = "192.168.1.64"
        client.port = 80
        client.base_url = "http://192.168.1.64:80/v1"
        client._client = httpx.Client(base_url=client.base_url, transport=transport)

        with pytest.raises(C64UConnectionError, match="Cannot connect"):
            client.get_info()


class TestDeviceInfoFromAPI:
    def test_parses_full_response(self, sample_info: dict):
        info = DeviceInfo.from_api(sample_info)
        assert info.product == "C64 Ultimate"
        assert info.firmware_version == "3.14"

    def test_handles_missing_fields(self):
        info = DeviceInfo.from_api({"product": "Ultimate-II+"})
        assert info.product == "Ultimate-II+"
        assert info.firmware_version == ""
        assert info.core_version == ""
