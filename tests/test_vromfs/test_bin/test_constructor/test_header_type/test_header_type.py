import io
import typing as t
import pytest
from vromfs.bin.constructor import HeaderType, HeaderTypeCon
from test_vromfs import _test_parse, _test_build


@pytest.mark.parametrize(['header_type_istream', 'header_type_bs', 'header_type'], [
    pytest.param(io.BytesIO(b'VRFx'), b'VRFx', HeaderType.VRFX, id='VRFX'),
    pytest.param(io.BytesIO(b'VRFs'), b'VRFs', HeaderType.VRFS, id='VRFS'),
])
def test_header_type_parse(header_type_istream: t.BinaryIO, header_type_bs: bytes, header_type: HeaderType):
    _test_parse(HeaderTypeCon, header_type_istream, header_type_bs, header_type)


@pytest.mark.parametrize(['header_type', 'header_type_bs'], [
    pytest.param(HeaderType.VRFX, b'VRFx', id='VRFX'),
    pytest.param(HeaderType.VRFS, b'VRFs', id='VRFS'),
])
def test_header_type_build(header_type: HeaderType, header_type_bs: bytes, ostream: io.BytesIO):
    _test_build(HeaderTypeCon, header_type, header_type_bs, ostream)
