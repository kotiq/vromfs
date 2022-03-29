import io
import pytest
from pytest import param as _
from vromfs.obfs_reader import ObfsReader, deobfuscate, obfuscate


data = (
    # 0123456789abcdef
    b'abcdefghijklmnop'  # 00
    b'qrstuvwxyz012345'  # 01
    b'6789ABCDEFGHIJKL'  # 02
    b'MNOPQRSTUVWXYZ'    # 03
)


@pytest.fixture
def obfs_reader_big():
    """len > 32"""

    sample = obfuscate(data)
    # b"4\xc86\xcej\x96h\x98<\xc0>\xc6%|'b
    # qrstuvwxyz0123456789ABCDEFGH
    # \x01X\x03^\x18\xe4\x1a\xfa^\xa2\\\xa4\x00\xfc\x02\xf2
    # YZ"
    return ObfsReader(io.BytesIO(sample), len(sample))


@pytest.fixture
def obfs_reader_medium():
    """len > 16 & < 32"""

    sample = obfuscate(data[:24])
    return ObfsReader(io.BytesIO(sample), len(sample))


@pytest.fixture
def obfs_reader_little():
    """len < 16"""

    sample = obfuscate(data[:8])
    return ObfsReader(io.BytesIO(sample), len(sample))


def _test_read(reader: ObfsReader, offset: int, size: int, expected: bytes):
    reader.seek(offset)
    assert reader.read(size) == expected


@pytest.mark.parametrize(['offset', 'size', 'expected'], [
    _(0, -1, b'abcdefgh', id='readall'),
    _(1, -1, b'bcdefgh', id='readall-from-offset'),
    _(1, 3, b'bcd', id='read-from-offset'),
    _(8, 1, b'', id='out-of-range'),
    _(7, 2, b'h', id='large-size')
])
def test_read_little(obfs_reader_little: ObfsReader, offset: int, size: int, expected: bytes):
    _test_read(obfs_reader_little, offset, size, expected)


@pytest.mark.parametrize(['offset', 'size', 'expected'], [
    _(0, -1, b'abcdefghijklmnopqrstuvwx', id='readall'),
    _(8, 8, b'ijklmnop', id='offset-lt-16'),
    _(16, 8, b'qrstuvwx', id='offset-gt-16')
])
def test_read_medium(obfs_reader_medium: ObfsReader, offset: int, size: int, expected: bytes):
    _test_read(obfs_reader_medium, offset, size, expected)


@pytest.mark.parametrize(['offset', 'size', 'expected'], [
    _(0, 0x10, b'abcdefghijklmnop', id='head-full'),
    _(3, 0xa, b'defghijklm', id='head-partial'),
    _(0x10, 0x1c, b'qrstuvwxyz0123456789ABCDEFGH', id='body-full'),
    _(0x2c, 0x10, b'IJKLMNOPQRSTUVWX', id='tail-full'),
    _(0x2e, 0xa, b'KLMNOPQRST', id='tail-partial'),
    _(0x3c, 2, b'YZ', id='extra-full'),
    _(0xa, 0x10, b'klmnopqrstuvwxyz', id='head-body'),
    _(0xa, 0x28, b'klmnopqrstuvwxyz0123456789ABCDEFGHIJKLMN', id='head-tail'),
    _(0xa, 0x33, b'klmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXY', id='head-extra'),
    _(0x12, 0x20, b'stuvwxyz0123456789ABCDEFGHIJKLMN', id='body-tail'),
    _(0x32, 0x0b, b'OPQRSTUVWXY', id='tail-extra'),
    _(0, -1, b'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', id='readall'),
])
def test_read_big(obfs_reader_big: ObfsReader, offset: int, size: int, expected: bytes):
    _test_read(obfs_reader_big, offset, size, expected)
