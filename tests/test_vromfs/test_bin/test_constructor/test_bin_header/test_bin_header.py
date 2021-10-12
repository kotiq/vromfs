import typing as t
import pytest
from pytest_lazyfixture import lazy_fixture
from vromfs.bin.constructor import BinHeader
from test_vromfs import _test_parse, _test_build

vrfx_pc_compressed_header_bs = lazy_fixture('vrfx_pc_compressed_header_bs')
vrfx_pc_compressed_header = lazy_fixture('vrfx_pc_compressed_header')
vrfx_pc_compressed_header_istream = lazy_fixture('vrfx_pc_compressed_header_istream')


@pytest.mark.parametrize(['header_istream', 'header_bs', 'header'], [
    pytest.param(
        vrfx_pc_compressed_header_istream,
        vrfx_pc_compressed_header_bs,
        vrfx_pc_compressed_header,
        id='vrfx_pc_compressed'
    ),
])
def test_bin_header_parse(header_istream: t.BinaryIO, header_bs: bytes, header: dict):
    _test_parse(BinHeader, header_istream, header_bs, header)


@pytest.mark.parametrize(['header', 'header_bs'], [
    pytest.param(
        vrfx_pc_compressed_header,
        vrfx_pc_compressed_header_bs,
        id='vrfx_pc_compressed'
    ),
])
def test_bin_header_build(header: dict, header_bs: bytes, ostream: t.BinaryIO):
    _test_build(BinHeader, header, header_bs, ostream)
