import io
from operator import attrgetter
import pytest
from pytest import param as _
from pytest_lazyfixture import lazy_fixture
from vromfs.bin import BinFile


params = [_(lazy_fixture(f'{base}_bin_bytes'), lazy_fixture(f'{base}_bin_ns'), id=base) for base in
          ('vrfs_pc_plain', 'vrfx_pc_zstd_obfs', 'vrfs_pc_zstd_obfs_nocheck')]


@pytest.mark.parametrize(['bytes_', 'ns'], params)
def test_unpack(bytes_, ns, data):
    istream = io.BytesIO(bytes_)
    file = BinFile(istream)
    for name in ns._fields:
        value, expected = map(attrgetter(name), (file, ns))
        assert value == expected
    assert istream.tell() == len(bytes_)
    assert file.stream.read() == data


@pytest.mark.parametrize(['bytes_', 'ns'], params)
def test_pack_into(bytes_, ns, data, ostream):
    istream = io.BytesIO(data)
    kwargs = ns._asdict()
    BinFile.pack_into(istream, ostream, **kwargs)
    assert ostream.tell() == len(bytes_)
    ostream.seek(0)
    assert ostream.read() == bytes_
