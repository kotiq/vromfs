import io
import pytest
from pytest import param as _
from vromfs.bin import PlatformType, PlatformTypeCon
from test_vromfs import check_parse, check_build

params = [
    _(b'\x00\x00PC', PlatformType.PC, id='PC'),
    _(b'\x00iOS',  PlatformType.IOS, id='IOS'),
    _(b'\x00and',  PlatformType.ANDROID, id='ANDROID'),
]


@pytest.mark.parametrize(['bytes_', 'value'], params)
def test_platform_type_parse(bytes_, value):
    istream = io.BytesIO(bytes_)
    check_parse(PlatformTypeCon, istream, 4, value)


@pytest.mark.parametrize(['bytes', 'value'], params)
def test_platform_type_build(value, bytes, ostream):
    check_build(PlatformTypeCon, value, bytes, ostream)
