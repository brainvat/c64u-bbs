"""Tests for the BBS catalog registry."""

from __future__ import annotations

from c64u_bbs.bbs.catalog import CATALOG, BBSPackage, DiskImage, get_package, list_packages
from c64u_bbs.models.drives import DriveMode


class TestCatalogEntries:
    def test_imagebbs_exists(self):
        assert "imagebbs" in CATALOG

    def test_imagebbs_fields(self):
        pkg = CATALOG["imagebbs"]
        assert pkg.name == "imagebbs"
        assert pkg.version == "3.0"
        assert pkg.license == "Public Domain"
        assert pkg.boot_device == 8

    def test_imagebbs_has_two_disks(self):
        pkg = CATALOG["imagebbs"]
        assert len(pkg.disks) == 2
        assert all(isinstance(d, DiskImage) for d in pkg.disks)
        assert pkg.disks[0].drive == "a"
        assert pkg.disks[1].drive == "b"
        assert pkg.disks[0].drive_mode == DriveMode.D1581
        assert pkg.disks[1].drive_mode == DriveMode.D1581

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
        pkg = get_package("imagebbs")
        assert pkg.name == "imagebbs"

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
