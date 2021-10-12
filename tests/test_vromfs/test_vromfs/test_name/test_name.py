import io
from pathlib import Path
import typing as t
import pytest
from vromfs.vromfs.constructor import Name
from test_vromfs import _test_parse, _test_build


@pytest.mark.parametrize(['name_istream', 'name_bs', 'name'], [
    pytest.param(io.BytesIO(b'name\x00'), b'name\x00', Path('name'), id='simple'),
    pytest.param(io.BytesIO(b'pre/fix/name\x00'), b'pre/fix/name\x00', Path('pre/fix/name'), id='compound'),
    pytest.param(io.BytesIO(b'/version\x00'), b'/version\x00', Path('version'), id='absolute'),
    pytest.param(io.BytesIO(b'\xff\x3fnm\x00'), b'\xff\x3fnm\x00', Path('nm'), id='special'),
])
def test_name_parse(name_istream: t.BinaryIO, name_bs, name: Path):
    _test_parse(Name, name_istream, name_bs, name)


@pytest.fixture(scope='module', params=[0, 1, 2])
def empty_or_root_bs(request):
    n = request.param
    return b'/'*n + b'\x00'


@pytest.fixture(scope='module')
def empty_or_root_istream(empty_or_root_bs):
    return io.BytesIO(empty_or_root_bs)


def test_empty_or_root_name_parse_raises_value_error(empty_or_root_istream, empty_or_root_bs):
    with pytest.raises(ValueError, match='Пустое имя'):
        Name.parse_stream(empty_or_root_istream)
    assert empty_or_root_istream.tell() == len(empty_or_root_bs)


@pytest.mark.parametrize(['name', 'name_bs'], [
    pytest.param(Path('name'), b'name\x00', id='simple'),
    pytest.param(Path('pre/fix/name'), b'pre/fix/name\x00', id='compound'),
    pytest.param(Path('nm'), b'\xff\x3fnm\x00', id='special'),
])
def test_name_build(name: Path, name_bs: bytes, ostream: t.BinaryIO):
    _test_build(Name, name, name_bs, ostream)


@pytest.fixture(scope='module')
def absolute_name():
    return Path('/version')


def test_absolute_name_build_raises_value_error(absolute_name: Path, ostream: t.BinaryIO):
    with pytest.raises(ValueError, match='Ожидался относительный путь:'):
        Name.build_stream(absolute_name, ostream)
