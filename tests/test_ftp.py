"""Tests for the FTP client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from c64u_bbs.ftp.client import C64UFTP, C64UFTPError, FileEntry


class TestFileEntryParsing:
    def test_parse_directory(self):
        line = "drw-rw-rw-   1 user     ftp            0 Jan 01  1980 SD"
        entry = FileEntry.from_list_line(line)
        assert entry.name == "SD"
        assert entry.is_dir is True
        assert entry.size == 0

    def test_parse_file(self):
        line = "-rw-rw-rw-   1 user     ftp       174848 Apr 12 01:52 CONGOBON.D64"
        entry = FileEntry.from_list_line(line)
        assert entry.name == "CONGOBON.D64"
        assert entry.is_dir is False
        assert entry.size == 174848
        assert entry.modified == "Apr 12 01:52"

    def test_parse_small_file(self):
        line = "-rw-rw-rw-   1 user     ftp            2 Apr 11 23:44 temp0001"
        entry = FileEntry.from_list_line(line)
        assert entry.name == "temp0001"
        assert entry.size == 2


class TestC64UFTP:
    @patch("c64u_bbs.ftp.client.FTP")
    def test_context_manager(self, mock_ftp_class):
        mock_ftp = MagicMock()
        mock_ftp_class.return_value = mock_ftp

        with C64UFTP("192.168.1.64") as ftp:
            assert ftp.ftp is mock_ftp
            mock_ftp.connect.assert_called_once_with("192.168.1.64", 21, timeout=10.0)
            mock_ftp.login.assert_called_once()

        mock_ftp.quit.assert_called_once()

    @patch("c64u_bbs.ftp.client.FTP")
    def test_list_dir(self, mock_ftp_class):
        mock_ftp = MagicMock()
        mock_ftp_class.return_value = mock_ftp

        def fake_dir(path, callback):
            callback("drw-rw-rw-   1 user     ftp            0 Jan 01  1980 SD")
            callback("-rw-rw-rw-   1 user     ftp       174848 Apr 12 01:52 GAME.D64")

        mock_ftp.dir = fake_dir

        with C64UFTP("192.168.1.64") as ftp:
            entries = ftp.list_dir("/")

        assert len(entries) == 2
        assert entries[0].name == "SD"
        assert entries[0].is_dir is True
        assert entries[1].name == "GAME.D64"
        assert entries[1].size == 174848

    @patch("c64u_bbs.ftp.client.FTP")
    def test_upload(self, mock_ftp_class, tmp_path):
        mock_ftp = MagicMock()
        mock_ftp_class.return_value = mock_ftp

        test_file = tmp_path / "test.d64"
        test_file.write_bytes(b"\x00" * 100)

        with C64UFTP("192.168.1.64") as ftp:
            size = ftp.upload(str(test_file), "/SD/test.d64")

        assert size == 100
        mock_ftp.storbinary.assert_called_once()

    @patch("c64u_bbs.ftp.client.FTP")
    def test_download(self, mock_ftp_class, tmp_path):
        mock_ftp = MagicMock()
        mock_ftp_class.return_value = mock_ftp

        def fake_retrbinary(cmd, callback):
            callback(b"hello world")

        mock_ftp.retrbinary = fake_retrbinary
        dest = tmp_path / "downloaded.bin"

        with C64UFTP("192.168.1.64") as ftp:
            size = ftp.download("/Temp/file.bin", str(dest))

        assert size == 11
        assert dest.read_bytes() == b"hello world"

    def test_not_connected_error(self):
        ftp = C64UFTP("192.168.1.64")
        with pytest.raises(C64UFTPError, match="Not connected"):
            ftp.list_dir("/")
