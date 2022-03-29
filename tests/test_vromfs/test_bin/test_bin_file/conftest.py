import typing as t
import pytest
from vromfs.bin import BinFile, PlatformType, Version
from helpers import make_source, fixtures_group


# char: checked, compressed 0x30 = 0b11_0000
# grp_hdr: not checked, compressed 0x10 = 01_0000
# fonts: checked, not compressed 0x20 = 10_0000


for base in ('char', 'aces', 'grp_hdr', 'fonts'):
    suffix = '.vromfs.bin'
    file_name = base + suffix
    fixture_name = file_name.replace('.', '_')
    globals()[fixture_name] = make_source(file_name, BinFile)


checked = fixtures_group('char_vromfs_bin', 'fonts_vromfs_bin')
not_checked = fixtures_group('grp_hdr_vromfs_bin', )
compressed = fixtures_group('char_vromfs_bin', 'grp_hdr_vromfs_bin')
not_compressed = fixtures_group('fonts_vromfs_bin', )
binfile = fixtures_group('char_vromfs_bin', 'grp_hdr_vromfs_bin', 'fonts_vromfs_bin')


class BinNS(t.NamedTuple):
    size: int
    platform: PlatformType
    compressed: bool
    checked: bool
    version: t.Optional[Version]


@pytest.fixture(scope='module')
def vrfs_pc_plain_bin_ns(data, data_digest):
    return BinNS(
        size=len(data),
        platform=PlatformType.PC,
        compressed=False,
        checked=True,
        version=None,
    )


@pytest.fixture(scope='module')
def vrfx_pc_zstd_obfs_bin_ns(data, data_digest):
    return BinNS(
        size=len(data),
        platform=PlatformType.PC,
        compressed=True,
        checked=True,
        version=(1, 2, 3, 4),
    )


@pytest.fixture(scope='module')
def vrfs_pc_zstd_obfs_nocheck_bin_ns(data):
    return BinNS(
        size=len(data),
        platform=PlatformType.PC,
        compressed=True,
        checked=False,
        version=None,
    )
