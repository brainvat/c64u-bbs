"""Tests for BBS deployment orchestration."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from c64u_bbs.bbs.catalog import BBSPackage, DiskImage
from c64u_bbs.bbs.deployer import (
    DeployError,
    deploy_bbs,
    get_assets_dir,
    load_disk_image,
)
from c64u_bbs.models.drives import DriveMode


@pytest.fixture
def sample_package() -> BBSPackage:
    return BBSPackage(
        name="testbbs",
        display_name="Test BBS v1.0",
        version="1.0",
        license="Public Domain",
        boot_file="+BOOT",
        boot_device=8,
        disks=(
            DiskImage("test-sys.d64", "a", DriveMode.D1541, "System disk"),
            DiskImage("test-data.d64", "b", DriveMode.D1541, "Data disk"),
        ),
        description="Test BBS for unit tests.",
    )


class TestGetAssetsDir:
    def test_returns_path_under_assets(self):
        path = get_assets_dir("color64")
        assert path.name == "color64"
        assert "assets" in str(path)
        assert "bbs" in str(path)


class TestLoadDiskImage:
    def test_missing_file_raises(self, tmp_path):
        with patch("c64u_bbs.bbs.deployer._ASSETS_ROOT", tmp_path):
            with pytest.raises(DeployError, match="not found"):
                load_disk_image("fakebbs", "missing.d64")

    def test_empty_file_raises(self, tmp_path):
        pkg_dir = tmp_path / "fakebbs"
        pkg_dir.mkdir()
        (pkg_dir / "empty.d64").write_bytes(b"")
        with patch("c64u_bbs.bbs.deployer._ASSETS_ROOT", tmp_path):
            with pytest.raises(DeployError, match="empty"):
                load_disk_image("fakebbs", "empty.d64")

    def test_valid_file_returns_bytes(self, tmp_path):
        pkg_dir = tmp_path / "fakebbs"
        pkg_dir.mkdir()
        data = b"\x00" * 174848  # D64 size
        (pkg_dir / "disk.d64").write_bytes(data)
        with patch("c64u_bbs.bbs.deployer._ASSETS_ROOT", tmp_path):
            result = load_disk_image("fakebbs", "disk.d64")
        assert result == data


class TestDeployBBS:
    @patch("c64u_bbs.bbs.deployer.wait_for_modem_ready", return_value=True)
    @patch("c64u_bbs.bbs.deployer.load_disk_image")
    @patch("c64u_bbs.bbs.deployer.time")
    def test_calls_all_steps_in_order(
        self, mock_time, mock_load_image, mock_wait, sample_package
    ):
        mock_load_image.return_value = b"\x00" * 1000
        client = MagicMock()
        client.host = "192.168.1.64"

        steps = []
        deploy_bbs(
            client,
            sample_package,
            port=6400,
            on_step=lambda name, detail: steps.append(name),
        )

        # Verify step order
        assert steps == [
            "reset",
            "modem",
            "drive_mode", "mount",   # disk A
            "drive_mode", "mount",   # disk B
            "boot",
            "wait",
        ]

    @patch("c64u_bbs.bbs.deployer.wait_for_modem_ready", return_value=True)
    @patch("c64u_bbs.bbs.deployer.load_disk_image")
    @patch("c64u_bbs.bbs.deployer.time")
    def test_resets_c64(self, mock_time, mock_load_image, mock_wait, sample_package):
        mock_load_image.return_value = b"\x00" * 1000
        client = MagicMock()
        client.host = "192.168.1.64"

        deploy_bbs(client, sample_package)

        client.reset.assert_called_once()

    @patch("c64u_bbs.bbs.deployer.wait_for_modem_ready", return_value=True)
    @patch("c64u_bbs.bbs.deployer.load_disk_image")
    @patch("c64u_bbs.bbs.deployer.time")
    def test_mounts_all_disks(self, mock_time, mock_load_image, mock_wait, sample_package):
        mock_load_image.return_value = b"\x00" * 1000
        client = MagicMock()
        client.host = "192.168.1.64"

        deploy_bbs(client, sample_package)

        # Should set drive modes for both drives
        assert client.set_drive_mode.call_count == 2
        # Should upload and mount both disks
        assert client.upload_and_mount.call_count == 2

    @patch("c64u_bbs.bbs.deployer.wait_for_modem_ready", return_value=True)
    @patch("c64u_bbs.bbs.deployer.load_disk_image")
    @patch("c64u_bbs.bbs.deployer.time")
    def test_uploads_boot_loader(self, mock_time, mock_load_image, mock_wait, sample_package):
        mock_load_image.return_value = b"\x00" * 1000
        client = MagicMock()
        client.host = "192.168.1.64"

        deploy_bbs(client, sample_package)

        client.upload_and_run_prg.assert_called_once()
        call_args = client.upload_and_run_prg.call_args
        prg_data = call_args[0][0]
        filename = call_args[0][1]
        assert isinstance(prg_data, bytes)
        assert filename == "BBSBOOT.PRG"

    @patch("c64u_bbs.bbs.deployer.wait_for_modem_ready", return_value=False)
    @patch("c64u_bbs.bbs.deployer.load_disk_image")
    @patch("c64u_bbs.bbs.deployer.time")
    def test_raises_if_bbs_doesnt_start(
        self, mock_time, mock_load_image, mock_wait, sample_package
    ):
        mock_load_image.return_value = b"\x00" * 1000
        client = MagicMock()
        client.host = "192.168.1.64"

        with pytest.raises(DeployError, match="did not open modem port"):
            deploy_bbs(client, sample_package)
