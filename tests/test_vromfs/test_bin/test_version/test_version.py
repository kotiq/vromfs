import io
import pytest
from pytest import param as _
from vromfs.bin import VersionCon
from test_vromfs import check_parse, check_build

params = [
    _(b'\x04\x03\x02\x01', (1, 2, 3, 4), id='1.2.3.4'),
]


@pytest.mark.parametrize(['bytes_', 'value'], params)
def test_version_parse(bytes_, value):
    istream = io.BytesIO(bytes_)
    check_parse(VersionCon, istream, 4, value)


@pytest.mark.parametrize(['bytes_', 'value', ], params)
def test_version_build(value, bytes_, ostream):
    check_build(VersionCon, value, bytes_, ostream)
