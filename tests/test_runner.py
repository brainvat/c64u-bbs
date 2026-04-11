"""Tests for the PRG runner."""

from __future__ import annotations

import httpx
import pytest

from c64u_bbs.client.c64u import C64UClient


@pytest.fixture
def runner_client(sample_info: dict) -> C64UClient:
    """Client with mocked runner endpoints."""
    received = {}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        received["last_path"] = path
        received["last_method"] = request.method
        received["last_params"] = dict(request.url.params)
        received["last_content_type"] = request.headers.get("content-type", "")

        if "run_prg" in path and request.method == "PUT":
            return httpx.Response(200, json={"errors": []})
        if "run_prg" in path and request.method == "POST":
            return httpx.Response(200, json={"errors": []})
        if "machine:reset" in path:
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


class TestRunPRG:
    def test_run_from_device_path(self, runner_client: C64UClient):
        runner_client.run_prg("/usb0/games/game.prg")
        assert runner_client._received["last_method"] == "PUT"
        assert runner_client._received["last_params"]["file"] == "/usb0/games/game.prg"

    def test_upload_and_run(self, runner_client: C64UClient):
        data = b"\x01\x08" + b"\x00" * 100  # fake PRG
        runner_client.upload_and_run_prg(data, "test.prg")
        assert runner_client._received["last_method"] == "POST"
        assert "multipart" in runner_client._received["last_content_type"]


class TestReset:
    def test_reset(self, runner_client: C64UClient):
        runner_client.reset()
        assert runner_client._received["last_method"] == "PUT"
        assert "machine:reset" in runner_client._received["last_path"]
