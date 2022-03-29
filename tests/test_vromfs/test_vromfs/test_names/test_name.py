import io
from pathlib import Path
import pytest
from pytest import param as _
from vromfs.vromfs import Name
from test_vromfs import check_parse, check_build

bijective_params = [
    _(b'name\x00', 'name', id='simple'),
    _(b'pre/fix/name\x00', 'pre/fix/name', id='compound'),
    _(b'\xff\x3fnm\x00', 'nm', id='special'),
]


@pytest.mark.parametrize(['bytes_', 'value'], bijective_params + [_(b'/version\x00', 'version', id='absolute')])
def test_name_parse(bytes_, value):
    istream = io.BytesIO(bytes_)
    bytes_len = len(bytes_)
    name = Path(value)
    check_parse(Name, istream, bytes_len, name)


@pytest.mark.parametrize('bytes_', [
    _(b'\x00', id='empty'),
    _(b'/\x00', id='root1'),
    _(b'//\x00', id='root2'),
])
def test_empty_or_root_name_parse_raises_value_error(bytes_):
    istream = io.BytesIO(bytes_)
    with pytest.raises(ValueError, match='Пустое имя'):
        Name.parse_stream(istream)
    assert istream.tell() == len(bytes_)


@pytest.mark.parametrize(['bytes_', 'value'], bijective_params)
def test_name_build(value, bytes_, ostream):
    name = Path(value)
    check_build(Name, name, bytes_, ostream)


@pytest.fixture(scope='module')
def absolute_name():
    return Path('/version')


def test_absolute_name_build_raises_value_error(absolute_name: Path, ostream):
    with pytest.raises(ValueError, match='Ожидался относительный путь:'):
        Name.build_stream(absolute_name, ostream)
