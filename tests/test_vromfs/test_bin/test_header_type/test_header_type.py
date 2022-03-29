import io
import pytest
from pytest import param as _
from vromfs.bin import HeaderType, HeaderTypeCon
from test_vromfs import check_parse, check_build

params = [
    _(b'VRFx', HeaderType.VRFX, id='VRFX'),
    _(b'VRFs', HeaderType.VRFS, id='VRFS'),
]


@pytest.mark.parametrize(['bytes_', 'value'], params)
def test_header_type_parse(bytes_, value):
    istream = io.BytesIO(bytes_)
    check_parse(HeaderTypeCon, istream, 4, value)


@pytest.mark.parametrize(['bytes_', 'value'], params)
def test_header_type_build(value, bytes_, ostream):
    check_build(HeaderTypeCon, value, bytes_, ostream)
