import io
import pytest
from pytest import param as _
from pytest_lazyfixture import lazy_fixture
from vromfs.vromfs import Image
from test_vromfs import check_parse

params = [_(lazy_fixture(f'{base}_vromfs_bytes'), lazy_fixture(f'{base}_vromfs_container'), id=base) for base in
          ('checked', 'unchecked', 'unchecked_ex')]


@pytest.mark.parametrize(['bytes_', 'value'], params)
def test_vromfs_container_parse(bytes_, value):
    istream = io.BytesIO(bytes_)
    pos = value['offset']
    check_parse(Image, istream, pos, value)
