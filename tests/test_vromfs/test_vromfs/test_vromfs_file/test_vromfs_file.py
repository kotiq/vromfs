import io
from operator import attrgetter
import pytest
from pytest import param as _
from pytest_lazyfixture import lazy_fixture
from vromfs.vromfs import VromfsFile


params = [_(lazy_fixture(f'{base}_vromfs_bytes'), lazy_fixture(f'{base}_vromfs_ns'), id=base) for base in
          ('checked', 'unchecked', 'unchecked_ex')]


@pytest.mark.parametrize(['bytes_', 'ns'], params)
def test_unpack(bytes_, ns, data):
    istream = io.BytesIO(bytes_)
    file = VromfsFile(istream)
    for name in ns._fields:
        value, expected = map(attrgetter(name), (file, ns))
        assert value == expected
    assert istream.tell() == file.meta.offset
    # опирается на структуру метаданных
    ps = sorted(zip(file.meta.data_info, data), key=lambda p: p[0]['offset'])
    for ((di, block), info) in zip(ps, file.info_list):
        ostream = file.unpack_into(info)
        expected = block[:di['size']]
        ostream.seek(0)
        assert ostream.read() == expected


@pytest.mark.parametrize(['bytes_', 'ns'], params)
def test_pack_into(bytes_, ns, source, ostream):
    kwargs = ns._asdict()
    VromfsFile.pack_into(source, ostream, **kwargs)
    assert ostream.tell() == len(bytes_)
    ostream.seek(0)
    assert ostream.read() == bytes_
