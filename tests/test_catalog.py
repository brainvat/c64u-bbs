"""Tests for the BBS catalog registry."""

from __future__ import annotations

from c64u_bbs.bbs.catalog import CATALOG, BBSPackage, DiskImage, get_package, list_packages
from c64u_bbs.models.drives import DriveMode


class TestCatalogEntries:
    def test_cbase_exists(self):
        assert "cbase" in CATALOG

    def test_cbase_fields(self):
        pkg = CATALOG["cbase"]
        assert pkg.name == "cbase"
        assert pkg.version == "3.3.7"
        assert pkg.license == "GPL-2.0+"
        assert pkg.boot_file == "c/boot 1.59"
        assert pkg.boot_device == 8

    def test_cbase_has_disks(self):
        pkg = CATALOG["cbase"]
        assert len(pkg.disks) >= 1
        assert all(isinstance(d, DiskImage) for d in pkg.disks)

    def test_disk_images_have_valid_drives(self):
        for pkg in CATALOG.values():
            for disk in pkg.disks:
                assert disk.drive in ("a", "b", "softiec")
                assert isinstance(disk.drive_mode, DriveMode)

    def test_all_entries_are_bbs_packages(self):
        for pkg in CATALOG.values():
            assert isinstance(pkg, BBSPackage)


class TestGetPackage:
    def test_known_package(self):
        pkg = get_package("cbase")
        assert pkg.name == "cbase"

    def test_unknown_package_raises(self):
        try:
            get_package("nonexistent")
            assert False, "Should have raised KeyError"
        except KeyError:
            pass


class TestListPackages:
    def test_returns_all(self):
        packages = list_packages()
        assert len(packages) == len(CATALOG)
        assert all(isinstance(p, BBSPackage) for p in packages)
