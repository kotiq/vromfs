import io
import pytest
from pytest import param as _
from pytest_lazyfixture import lazy_fixture
from vromfs.bin import BinContainer
from test_vromfs import check_parse

params = [_(lazy_fixture(f'{base}_bin_bytes'), lazy_fixture(f'{base}_bin_container'), id=base) for base in
          ('vrfs_pc_plain', 'vrfx_pc_zstd_obfs', 'vrfs_pc_zstd_obfs_nocheck')]


@pytest.mark.parametrize(['bytes_', 'value'], params)
def test_bin_container_parse(bytes_, value):
    istream = io.BytesIO(bytes_)
    bytes_len = len(bytes_)
    check_parse(BinContainer, istream, bytes_len, value)
