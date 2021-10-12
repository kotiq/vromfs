import io
import typing as t
import pytest
from vromfs.bin.constructor import PlatformType, PlatformTypeCon
from test_vromfs import _test_parse, _test_build


@pytest.mark.parametrize(['platform_type_istream', 'platform_type_bs', 'platform_type'], [
    pytest.param(io.BytesIO(b'\x00\x00PC'), b'\x00\x00PC', PlatformType.PC, id='PC'),
    pytest.param(io.BytesIO(b'\x00iOS'), b'\x00iOS', PlatformType.IOS, id='IOS'),
    pytest.param(io.BytesIO(b'\x00and'), b'\x00and', PlatformType.ANDROID, id='ANDROID'),
])
def test_platform_type_parse(platform_type_istream: t.BinaryIO, platform_type_bs: bytes, platform_type: PlatformType):
    _test_parse(PlatformTypeCon, platform_type_istream, platform_type_bs, platform_type)


@pytest.mark.parametrize(['platform_type', 'platform_type_bs'], [
    pytest.param(PlatformType.PC, b'\x00\x00PC', id='PC'),
    pytest.param(PlatformType.IOS, b'\x00iOS', id='IOS'),
    pytest.param(PlatformType.ANDROID, b'\x00and', id='ANDROID'),
])
def test_platform_type_build(platform_type: PlatformType, platform_type_bs: bytes, ostream: io.BytesIO):
    _test_build(PlatformTypeCon, platform_type, platform_type_bs, ostream)
