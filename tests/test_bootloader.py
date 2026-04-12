"""Tests for the BBS boot loader generator."""

from __future__ import annotations

from c64u_bbs.bbs.bootloader import generate_boot_loader


class TestGenerateBootLoader:
    def test_returns_bytes(self):
        prg = generate_boot_loader("+REBOOT")
        assert isinstance(prg, bytes)
        assert len(prg) > 0

    def test_starts_with_load_address(self):
        prg = generate_boot_loader("+REBOOT")
        # PRG load address should be $0801 (little-endian)
        assert prg[0] == 0x01
        assert prg[1] == 0x08

    def test_contains_load_token(self):
        prg = generate_boot_loader("+REBOOT")
        # LOAD token is 147 (0x93)
        assert 147 in prg

    def test_contains_filename(self):
        prg = generate_boot_loader("+REBOOT")
        # The filename should appear as ASCII between quotes
        # +REBOOT = bytes 43, 82, 69, 66, 79, 79, 84
        assert b"+REBOOT" in prg

    def test_device_number(self):
        prg = generate_boot_loader("+REBOOT", device=9)
        # Device 9 should appear as ASCII "9" (0x39)
        assert ord("9") in prg

    def test_default_device_is_8(self):
        prg = generate_boot_loader("+REBOOT")
        # Device 8 should appear as ASCII "8" (0x38)
        assert ord("8") in prg

    def test_line_number_is_zero(self):
        prg = generate_boot_loader("+REBOOT")
        # After the 2-byte load address and 2-byte next-line pointer,
        # the line number is 2 bytes little-endian: 0x00, 0x00
        assert prg[4] == 0  # line number low byte
        assert prg[5] == 0  # line number high byte

    def test_ends_with_program_terminator(self):
        prg = generate_boot_loader("+REBOOT")
        # PRG ends with 0x00 0x00 (end of program marker)
        assert prg[-2:] == b"\x00\x00"

    def test_different_filenames(self):
        prg_reboot = generate_boot_loader("+REBOOT")
        prg_bbs = generate_boot_loader("+BBS")
        assert prg_reboot != prg_bbs
        assert b"+BBS" in prg_bbs

    def test_image_bbs_filename(self):
        prg = generate_boot_loader("IMAGE 1.2B", device=8)
        assert b"IMAGE 1.2B" in prg
