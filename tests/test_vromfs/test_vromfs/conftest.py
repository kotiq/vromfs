import hashlib
import io
import itertools as itt
from pathlib import Path
import typing as t
import pytest
from vromfs.vromfs.constructor import File


def hash_(bs: bytes) -> bytes:
    return hashlib.sha1(bs).digest()


@pytest.fixture(scope='session')
def contents():
    return [
        b'42',
        b'hello world\n',
    ]


@pytest.fixture(scope='session')
def hashes(contents):
    return [hash_(bs) for bs in contents]


@pytest.fixture(scope='session')
def paths():
    return [
        Path('answer'),
        Path('greeting'),
    ]


@pytest.fixture(scope='session')
def image_with_hashes_bs():
    return bytes.fromhex(
        '30000000 02000000 00000000 00000000'  # 00h names_header: offset=0x30, count=2
        '50000000 02000000 00000000 00000000'  # 10h data_header: offset=0x50, count=2
        '98000000 00000000 70000000 00000000'  # 20h hashes_header: end=0x98, begin=0x70
        '40000000 00000000 47000000 00000000'  # 30h names_info: 0x40, 0x47
        '616E7377 65720067 72656574 696E6700'  # 40h names_data: 'answer', 'greeting'
        'A0000000 02000000 00000000 00000000'  # 50h datum_info: offset=0xa0, size=2
        'B0000000 0C000000 00000000 00000000'  # 60h datum_info: offset=0xb0, size=0xc
        '92CFCEB3 9D57D914 ED8B14D0 E37643DE'  # 70h hash=b'92cfceb39d57d914ed8b14d0e37643de0797ae56'
        '0797AE56 22596363 B3DE40B0 6F981FB8'  # 80h hash=b'22596363b3de40b06f981fb85d82312e8c0ed511'
        '5D82312E 8C0ED511 00000000 00000000'  # 90h
        '34320000 00000000 00000000 00000000'  # a0h datum=b'42'
        '68656C6C 6F20776F 726C640A 00000000'  # b0h datum=b'hello world\n'
    )


@pytest.fixture(scope='function')
def image_with_hashes_istream(image_with_hashes_bs: bytes):
    return io.BytesIO(image_with_hashes_bs)


@pytest.fixture(scope='session')
def image_with_hash_header_null_begin_bs():
    return bytes.fromhex(
        '30000000 02000000 00000000 00000000'  # 00h names_header: offset=0x30, count=2
        '50000000 02000000 00000000 00000000'  # 10h data_header: offset=0x50, count=2
        '70000000 00000000 00000000 00000000'  # 20h hashes_header: end=0x70, begin=0x00
        '40000000 00000000 47000000 00000000'  # 30h names_info: 0x40, 0x47
        '616E7377 65720067 72656574 696E6700'  # 40h names_data: 'answer', 'greeting'
        '70000000 02000000 00000000 00000000'  # 50h datum_info: offset=0x70, size=2
        '80000000 0c000000 00000000 00000000'  # 60h datum_info: offset=0x80, size=0xc
        '34320000 00000000 00000000 00000000'  # 70h datum=b'42'
        '68656c6c 6f20776f 726c640a 00000000'  # 80h datum=b'hello world\n'
    )


@pytest.fixture(scope='function')
def image_with_hash_header_null_begin_istream(image_with_hash_header_null_begin_bs: bytes):
    return io.BytesIO(image_with_hash_header_null_begin_bs)


@pytest.fixture(scope='session')
def image_without_hashes_bs():
    return bytes.fromhex(
        '20000000 02000000 00000000 00000000'  # 00h names_header: offset=0x20, count=2
        '40000000 02000000 00000000 00000000'  # 10h data_header: offset=0x40, count=2
        '30000000 00000000 37000000 00000000'  # 20h names_info: 0x30, 0x37
        '616E7377 65720067 72656574 696E6700'  # 30h names_data: 'answer', 'greeting'
        '60000000 02000000 00000000 00000000'  # 40h datum_info: offset=0x60, size=2
        '70000000 0c000000 00000000 00000000'  # 50h datum_info: offset=0x70, size=0xc
        '34320000 00000000 00000000 00000000'  # 60h datum=b'42'
        '68656c6c 6f20776f 726c640a 00000000'  # 70h datum=b'hello world\n'
    )


@pytest.fixture(scope='function')
def image_without_hashes_istream(image_without_hashes_bs: bytes):
    return io.BytesIO(image_without_hashes_bs)


@pytest.fixture(scope='function')
def image_with_hashes_files(paths: t.Sequence[Path], contents: t.Sequence[bytes], hashes: t.Sequence[bytes]):
    return [File(p, io.BytesIO(d), len(d), h) for p, d, h in zip(paths, contents, hashes)]


@pytest.fixture(scope='function')
def image_with_hash_header_null_begin_files(paths: t.Sequence[Path], contents: t.Sequence[bytes]):
    hashes = itt.repeat(None)
    return [File(p, io.BytesIO(d), len(d), h) for p, d, h in zip(paths, contents, hashes)]


@pytest.fixture(scope='function')
def image_without_hashes_files(paths: t.Sequence[Path], contents: t.Sequence[bytes]):
    hashes = itt.repeat(None)
    return [File(p, io.BytesIO(d), len(d), h) for p, d, h in zip(paths, contents, hashes)]
