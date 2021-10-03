import typing as t
from vromfs.constructor import VersionCon
from test_vromfs.test_constructor import _test_parse, _test_build


def test_version_parse(version_istream: t.BinaryIO, version_bs: bytes, version: t.Tuple[int, int, int, int]):
    _test_parse(VersionCon, version_istream, version_bs, version)


def test_version_build(version: t.Tuple[int, int, int, int], version_bs: bytes, ostream: t.BinaryIO):
    _test_build(VersionCon, version, version_bs, ostream)
