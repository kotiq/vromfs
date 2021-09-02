"""Проверка Vromfs и VromfsWrapped."""

import io
import construct as ct
from vromfs.parser import Vromfs, VromfsWrapped, RangedReader
from .data import vromfs_bs_20, files_info_20

vromfs_offset = 0x10
vromfs_20_bin_bs = b'\xfe' * vromfs_offset + vromfs_bs_20 + b'\xff' * 16


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
