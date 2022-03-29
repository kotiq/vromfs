import io
import pytest
from pytest import param as _
from pytest_lazyfixture import lazy_fixture
from vromfs.bin import BinExtHeader
from test_vromfs import check_parse, check_build

no_flags_ext_header = lazy_fixture('no_flags_ext_header')
no_flags_ext_header_bytes = lazy_fixture('no_flags_ext_header_bytes')


@pytest.mark.parametrize(['ext_header_bytes', 'ext_header'], [
    _(no_flags_ext_header_bytes, no_flags_ext_header, id='no_flags')
])
def test_bin_ext_header_parse(ext_header_bytes, ext_header):
    ext_header_istream = io.BytesIO(ext_header_bytes)
    check_parse(BinExtHeader, ext_header_istream, 8, ext_header)


@pytest.mark.parametrize(['ext_header', 'ext_header_bytes'], [
    _(no_flags_ext_header, no_flags_ext_header_bytes, id='no_flags')
])
def test_bin_ext_header_build(ext_header, ext_header_bytes, ostream):
    check_build(BinExtHeader, ext_header, ext_header_bytes, ostream)
