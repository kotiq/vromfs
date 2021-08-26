"""Проверка Vromfs и VromfsWrapped."""

import io
from pathlib import Path
import construct as ct
from vromfs.constructor import Vromfs, VromfsWrapped, FileInfo, RangedReader

vromfs_offset = 0x10

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


vromfs_20_bin_bs = b'\xfe' * vromfs_offset + vromfs_bs_20 + b'\xff' * 16


files_info_20 = (
    FileInfo(name=Path('hello'), offset=0x60, size=0x05, sha1=None),
    FileInfo(name=Path('world'), offset=0x70, size=0x11, sha1=None),
)


def test_vromfs_parse():
    size = len(vromfs_bs_20)
    istream = io.BytesIO(vromfs_20_bin_bs)
    ns = Vromfs(vromfs_offset, size).parse_stream(istream)
    assert ns.files_info == files_info_20
    assert isinstance(ns.stream, RangedReader)


def test_vromfs_wrapped_parse():
    istream = io.BytesIO(vromfs_bs_20)
    ns = VromfsWrapped(ct.Bytes(len(vromfs_bs_20))).parse_stream(istream)
    assert ns.files_info == files_info_20
    assert isinstance(ns.stream, io.BytesIO)
