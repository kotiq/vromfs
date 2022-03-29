import io
import pytest
from vromfs.ranged_reader import RangedReader


@pytest.fixture()
def ranged_reader():
    """
    pos  01234
    data 23456
    """

    reader = io.BytesIO(b'0123456789')
    return RangedReader(reader, 2, 5)


@pytest.mark.parametrize('target', [0, 2, 4, 6])
def test_seek_set(ranged_reader: RangedReader, target):
    assert ranged_reader.seek(target, io.SEEK_SET) == target


def test_seek_set_neg_raises_value_error(ranged_reader: RangedReader):
    with pytest.raises(ValueError):
        ranged_reader.seek(-1, io.SEEK_SET)


@pytest.mark.parametrize(['target', 'expected'], [
    (0, 2), (-1, 1), (-3, 0), (1, 3), (4, 6)
])
def test_seek_cur(ranged_reader: RangedReader, target, expected):
    ranged_reader.seek(2, io.SEEK_SET)
    assert ranged_reader.seek(target, io.SEEK_CUR) == expected


@pytest.mark.parametrize(['target', 'expected'], [
    (0, 5), (1, 6), (-1, 4), (-5, 0), (-6, 0)
])
def test_seek_end(ranged_reader: RangedReader, target, expected):
    assert ranged_reader.seek(target, io.SEEK_END) == expected


def test_seek_invalid_whence_raises_value_error(ranged_reader: RangedReader):
    whence = 4
    assert whence not in (io.SEEK_SET, io.SEEK_CUR, io.SEEK_END)
    with pytest.raises(ValueError):
        ranged_reader.seek(0, whence)


@pytest.mark.parametrize(['pos', 'size', 'expected'], [
    (0, 0, b''),
    (0, 1, b'2'),
    (0, -1, b'23456'),
    (1, 4, b'3456'),
    (1, 5, b'3456'),
    (1, -1, b'3456'),
    (5, 1, b''),
])
def test_read(ranged_reader: RangedReader, pos, size, expected):
    ranged_reader.seek(pos, io.SEEK_SET)
    pos = ranged_reader.pos
    assert ranged_reader.read(size) == expected
    assert ranged_reader.pos == pos + len(expected)
