"""Проверка VromfsInfo и FilesInfo."""

from pathlib import Path
import construct as ct
import pytest
from vromfs.constructor import VromfsInfo, FileInfo, FilesInfo

vromfs_bs_20 = bytes.fromhex(
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

info_20 = ct.Container(
    names_header=ct.Container(offset=0x20, count=2),
    data_header=ct.Container(offset=0x40, count=2),
    hash_header=None,
    names_info=[0x30, 0x36],
    names=[Path('hello'), Path('world')],
    data_info=[(0x60, 0x05), (0x70, 0x11)],
    hash_info=[None, None],
)

vromfs_bs_30 = bytes.fromhex(
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

info_30 = ct.Container(
    names_header=ct.Container(offset=0x30, count=2),
    data_header=ct.Container(offset=0x50, count=2),
    hash_header=ct.Container(end_offset=0x98, begin_offset=0x70),
    names_info=[0x40, 0x46],
    names=[Path('hello'), Path('world')],
    data_info=[(0xa0, 0x05), (0xb0, 0x11)],
    hash_info=[
        bytes.fromhex('12f403d3d7752b088ba121c5028eb5694570444c'),
        bytes.fromhex('2166625409f7beea3824440248056835a91a0ee8'),
    ],
)


@pytest.mark.parametrize(['vromfs_bs', 'info'], [
    pytest.param(vromfs_bs_20, info_20, id='20'),
    pytest.param(vromfs_bs_30, info_30, id='30'),
])
def test_vroms_info_parse(vromfs_bs, info):
    ns = VromfsInfo.parse(vromfs_bs)
    for name in info:
        assert ns[name] == info[name], name


files_info_20 = (
    FileInfo(name=Path('hello'), offset=0x60, size=0x05, sha1=None),
    FileInfo(name=Path('world'), offset=0x70, size=0x11, sha1=None),
)


files_info_30 = (
    FileInfo(name=Path('hello'), offset=0xa0, size=0x05,
             sha1=bytes.fromhex('12f403d3d7752b088ba121c5028eb5694570444c')),
    FileInfo(name=Path('world'), offset=0xb0, size=0x11,
             sha1=bytes.fromhex('2166625409f7beea3824440248056835a91a0ee8')),
)


@pytest.mark.parametrize(['vromfs_bs', 'files_info'], [
    pytest.param(vromfs_bs_20, files_info_20, id='20'),
    pytest.param(vromfs_bs_30, files_info_30, id='30'),
])
def test_files_info_parse(vromfs_bs, files_info):
    assert files_info == FilesInfo.parse(vromfs_bs)
