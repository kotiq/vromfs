from pathlib import Path
import typing as t
import pytest
from vromfs.vromfs import VromfsFile
from vromfs.bin import BinFile
from helpers import make_source, make_tmppath, fixtures_group

# char: no digests
# aces: no digests
# fonts: digests
# grp_hdr: no_digests


def inject_fixture(base, suffix, ctor):
    file_name = base + suffix
    fixture_name = file_name.replace('.', '_')
    globals()[fixture_name] = make_source(file_name, ctor)


for base in ('char', 'aces', 'grp_hdr', 'fonts'):
    inject_fixture(base, '.vromfs', VromfsFile)
    inject_fixture(base, '.vromfs.bin', lambda t: VromfsFile(BinFile(t)))


checked = fixtures_group('fonts_vromfs')
not_checked = fixtures_group('char_vromfs', 'aces_vromfs', 'grp_hdr_vromfs')
vromfsfile = fixtures_group('char_vromfs', 'aces_vromfs', 'grp_hdr_vromfs', 'fonts_vromfs')
vromfsbinfile = fixtures_group('char_vromfs_bin', 'aces_vromfs_bin', 'grp_hdr_vromfs_bin', 'fonts_vromfs_bin')


class VromfsNS(t.NamedTuple):
    checked: bool
    extended: bool


@pytest.fixture(scope='module')
def checked_vromfs_ns():
    return VromfsNS(checked=True, extended=True)


@pytest.fixture(scope='module')
def unchecked_vromfs_ns():
    return VromfsNS(checked=False, extended=False)


@pytest.fixture(scope='module')
def unchecked_ex_vromfs_ns():
    return VromfsNS(checked=False, extended=True)


source_path = make_tmppath('source')


@pytest.fixture(scope='module')
def source(source_path, paths, contents):
    for p, c in zip(paths, contents):
        q = source_path / p
        q.write_bytes(c)
    return source_path
