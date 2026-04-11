"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from c64u_bbs.client.c64u import C64UClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    """Load a JSON fixture file."""
    return json.loads((FIXTURES_DIR / name).read_text())


def mock_transport(responses: dict[str, tuple[int, dict | str]]) -> httpx.MockTransport:
    """Create a mock transport that maps URL paths to responses.

    Args:
        responses: dict mapping URL path suffixes to (status_code, body) tuples.
                   Body can be a dict (JSON) or str (text).
    """

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        for suffix, (status, body) in responses.items():
            if path.endswith(suffix):
                if isinstance(body, dict):
                    return httpx.Response(status, json=body)
                return httpx.Response(status, text=body)
        return httpx.Response(404, json={"errors": ["Not found"]})

    return httpx.MockTransport(handler)


@pytest.fixture
def sample_info() -> dict:
    return load_fixture("info.json")


@pytest.fixture
def sample_drives() -> dict:
    return load_fixture("drives.json")


@pytest.fixture
def mock_client(sample_info: dict) -> C64UClient:
    """A C64UClient with mocked HTTP transport returning fixture data."""
    transport = mock_transport({
        "/info": (200, sample_info),
    })
    client = C64UClient.__new__(C64UClient)
    client.host = "192.168.1.64"
    client.port = 80
    client.base_url = "http://192.168.1.64:80/v1"
    client._client = httpx.Client(
        base_url=client.base_url,
        transport=transport,
    )
    return client
