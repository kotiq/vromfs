import io
import pytest
from pytest import param as _
from pytest_lazyfixture import lazy_fixture
from vromfs.bin import BinHeader
from test_vromfs import check_parse, check_build

vrfx_pc_compressed_header = lazy_fixture('vrfx_pc_compressed_header')
vrfx_pc_compressed_header_bytes = lazy_fixture('vrfx_pc_compressed_header_bytes')


@pytest.mark.parametrize(['header_bytes', 'header'], [
    _(vrfx_pc_compressed_header_bytes, vrfx_pc_compressed_header, id='vrfx_pc_compressed'),
])
def test_bin_header_parse(header_bytes, header):
    header_istream = io.BytesIO(header_bytes)
    check_parse(BinHeader, header_istream, 16, header)


@pytest.mark.parametrize(['header', 'header_bytes'], [
    _(vrfx_pc_compressed_header, vrfx_pc_compressed_header_bytes, id='vrfx_pc_compressed'),
])
def test_bin_header_build(header, header_bytes, ostream):
    check_build(BinHeader, header, header_bytes, ostream)
