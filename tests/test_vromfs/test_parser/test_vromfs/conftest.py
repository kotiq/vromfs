from pathlib import Path
import construct as ct
import pytest
from vromfs.parser import FileInfo


@pytest.fixture(scope='session')
def vromfs_bs_20():
    return bytes.fromhex(
        '20000000 02000000 00000000 00000000'  # 00
        '40000000 02000000 00000000 00000000'  # 10
        '30000000 00000000 36000000 00000000'  # 20
        '68656c6c 6f00776f 726c6400 00000000'  # 30
        '60000000 05000000 00000000 00000000'  # 40
        '70000000 11000000 00000000 00000000'  # 50
        '11111111 11000000 00000000 00000000'  # 60
        '22222222 22222222 22222222 22222222'  # 70
        '22000000 00000000 00000000 00000000'  # 80
    )


@pytest.fixture(scope='session')
def info_20():
    return ct.Container(
        names_header=ct.Container(offset=0x20, count=2),
        data_header=ct.Container(offset=0x40, count=2),
        hash_header=None,
        names_info=[0x30, 0x36],
        names_data=bytes.fromhex('68656c6c 6f00776f 726c6400 00000000'),
        data_info=[(0x60, 0x05), (0x70, 0x11)],
        hash_info=[None, None],
    )


@pytest.fixture(scope='session')
def files_info_20():
    return (
        FileInfo(path=Path('hello'), offset=0x60, size=0x05, sha1=None),
        FileInfo(path=Path('world'), offset=0x70, size=0x11, sha1=None),
    )


@pytest.fixture(scope='session')
def vromfs_bs_30():
    return bytes.fromhex(
        '30000000 02000000 00000000 00000000'  # 00
        '50000000 02000000 00000000 00000000'  # 10
        '98000000 00000000 70000000 00000000'  # 20
        '40000000 00000000 46000000 00000000'  # 30    
        '68656c6c 6f00776f 726c6400 00000000'  # 40
        'a0000000 05000000 00000000 00000000'  # 50
        'b0000000 11000000 00000000 00000000'  # 60
        '12f403d3 d7752b08 8ba121c5 028eb569'  # 70
        '4570444c 21666254 09f7beea 38244402'  # 80
        '48056835 a91a0ee8 00000000 00000000'  # 90
        '11111111 11000000 00000000 00000000'  # a0    
        '22222222 22222222 22222222 22222222'  # b0
        '22000000 00000000 00000000 00000000'  # c0
    )


@pytest.fixture(scope='session')
def info_30():
    return ct.Container(
        names_header=ct.Container(offset=0x30, count=2),
        data_header=ct.Container(offset=0x50, count=2),
        hash_header=ct.Container(end_offset=0x98, begin_offset=0x70),
        names_info=[0x40, 0x46],
        names_data=bytes.fromhex('68656c6c 6f00776f 726c6400 00000000'),
        data_info=[(0xa0, 0x05), (0xb0, 0x11)],
        hash_info=[
            bytes.fromhex('12f403d3d7752b088ba121c5028eb5694570444c'),
            bytes.fromhex('2166625409f7beea3824440248056835a91a0ee8'),
        ],
    )


@pytest.fixture(scope='session')
def files_info_30():
    return (
        FileInfo(path=Path('hello'), offset=0xa0, size=0x05,
                 sha1=bytes.fromhex('12f403d3d7752b088ba121c5028eb5694570444c')),
        FileInfo(path=Path('world'), offset=0xb0, size=0x11,
                 sha1=bytes.fromhex('2166625409f7beea3824440248056835a91a0ee8')),
    )


@pytest.fixture(scope='session')
def vromfs_offset():
    return 0x10


@pytest.fixture(scope='session')
def vromfs_20_bin_bs(vromfs_offset, vromfs_bs_20):
    return b'\xfe' * vromfs_offset + vromfs_bs_20 + b'\xff' * 16
