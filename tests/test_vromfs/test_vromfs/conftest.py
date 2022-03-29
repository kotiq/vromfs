import hashlib
from pathlib import Path
import pytest


def digest(bs):
    return hashlib.sha1(bs).digest()


@pytest.fixture(scope='session')
def contents():
    return [b'42', b'hello world\n']


@pytest.fixture(scope='session')
def digests(contents):
    return [digest(bs) for bs in contents]


@pytest.fixture(scope='session')
def paths():
    return [Path(name) for name in ('answer', 'greeting')]


@pytest.fixture(scope='session')
def data():
    return [
        bytes.fromhex(xs) for xs in (
            '34320000 00000000 00000000 00000000',  # datum=b'42'
            '68656C6C 6F20776F 726C640A 00000000'  # datum=b'hello world\n'
        )
    ]


@pytest.fixture(scope='session')
def data_block(data):
    return b''.join(data)


@pytest.fixture(scope='session')
def checked_vromfs_bytes(data_block):
    return bytes.fromhex(
        '30000000 02000000 00000000 00000000'  # 00h names_header: offset=0x30, count=2
        '50000000 02000000 00000000 00000000'  # 10h data_header: offset=0x50, count=2
        '98000000 00000000 70000000 00000000'  # 20h digests_header: end=0x98, begin=0x70
        '40000000 00000000 47000000 00000000'  # 30h names_info: 0x40, 0x47
        '616E7377 65720067 72656574 696E6700'  # 40h names_data: 'answer', 'greeting'
        'A0000000 02000000 00000000 00000000'  # 50h datum_info: offset=0xa0, size=2
        'B0000000 0C000000 00000000 00000000'  # 60h datum_info: offset=0xb0, size=0xc
        '92CFCEB3 9D57D914 ED8B14D0 E37643DE'  # 70h digest=b'92cfceb39d57d914ed8b14d0e37643de0797ae56'
        '0797AE56 22596363 B3DE40B0 6F981FB8'  # 80h digest=b'22596363b3de40b06f981fb85d82312e8c0ed511'
        '5D82312E 8C0ED511 00000000 00000000'  # 90h
    ) + data_block


@pytest.fixture(scope='session')
def unchecked_vromfs_bytes(data_block):
    return bytes.fromhex(
        '20000000 02000000 00000000 00000000'  # 00h names_header: offset=0x20, count=2
        '40000000 02000000 00000000 00000000'  # 10h data_header: offset=0x40, count=2
        '30000000 00000000 37000000 00000000'  # 20h names_info: 0x30, 0x37
        '616E7377 65720067 72656574 696E6700'  # 30h names_data: 'answer', 'greeting'
        '60000000 02000000 00000000 00000000'  # 40h datum_info: offset=0x60, size=2
        '70000000 0c000000 00000000 00000000'  # 50h datum_info: offset=0x70, size=0xc
    ) + data_block


@pytest.fixture(scope='session')
def unchecked_ex_vromfs_bytes(data_block):
    return bytes.fromhex(
        '30000000 02000000 00000000 00000000'  # 00h names_header: offset=0x30, count=2
        '50000000 02000000 00000000 00000000'  # 10h data_header: offset=0x50, count=2
        '70000000 00000000 00000000 00000000'  # 20h digests_header: end=0x70, begin=0x00
        '40000000 00000000 47000000 00000000'  # 30h names_info: 0x40, 0x47
        '616E7377 65720067 72656574 696E6700'  # 40h names_data: 'answer', 'greeting'
        '70000000 02000000 00000000 00000000'  # 50h datum_info: offset=0x70, size=2
        '80000000 0c000000 00000000 00000000'  # 60h datum_info: offset=0x80, size=0xc
    ) + data_block

