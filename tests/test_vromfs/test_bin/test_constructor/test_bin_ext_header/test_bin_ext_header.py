import typing as t
from vromfs.bin.constructor import BinExtHeader
from test_vromfs.test_bin.test_constructor import _test_parse, _test_build


def test_bin_ext_header_parse(ext_header_istream: t.BinaryIO, ext_header_bs: bytes, ext_header: dict):
    _test_parse(BinExtHeader, ext_header_istream, ext_header_bs, ext_header)


def test_bin_ext_header_build(ext_header: dict, ext_header_bs: bytes, ostream: t.BinaryIO):
    _test_build(BinExtHeader, ext_header, ext_header_bs, ostream)
