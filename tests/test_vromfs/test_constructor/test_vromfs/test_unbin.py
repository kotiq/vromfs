"""Проверка распаковки контейнера."""

from pathlib import Path
import hashlib
import construct as ct
from construct import this
import pytest
from helpers import make_outpath
from vromfs.constructor import (BinHeader, VRFX, BinExtHeader, ZSTD_OBFS, ZSTD_OBFS_NOCHECK, ZstdCompressed, Obfuscated,
                                Raise, UnpackNotImplemented)

outpath = make_outpath(__name__)

BinContainer = ct.Struct(
    'header' / BinHeader,
    'ext_header' / ct.If(this.header.type == VRFX, BinExtHeader),
    'vromfs_offset' / ct.Tell,
    'vromfs' / ct.IfThenElse(
        this.header.packed.size == 0,
        ct.Bytes(this.header.size),
        ct.IfThenElse(this.header.packed.type in (ZSTD_OBFS, ZSTD_OBFS_NOCHECK),
                      ZstdCompressed(Obfuscated(ct.Bytes(this.header.packed.size)), this.header.size),
                      Raise(UnpackNotImplemented, this.header.packed.type)),
    ),
    'md5' / ct.If(this.header.packed.type != ZSTD_OBFS_NOCHECK,
                  ct.Checksum(ct.Bytes(16), lambda bs: hashlib.md5(bs).digest(), this.vromfs)),
    'tail' / ct.GreedyBytes,
    ct.Check(lambda c: len(c.tail) in (0, 0x100)),
)


@pytest.mark.parametrize(['rpath', 'fst'], [
    pytest.param('char.vromfs.bin', b'\x20', id='char'),
    pytest.param('fonts.vromfs.bin', b'\x30', id='fonts'),
    pytest.param('grp_hdr.vromfs.bin', b'\x20', id='grp_hdr'),
])
def test_unbin(binrespath: Path, outpath: Path, rpath: str, fst: bytes):
    """Извлечение vromfs из bin контейнера.
    Для несжатых проверка содержимого на этом этапе не проводится.
    """

    ipath = binrespath / rpath
    opath = (outpath / rpath).with_suffix('')
    bin_container = BinContainer.parse_file(ipath)
    with open(opath, 'wb') as ostream:
        ostream.write(bin_container.vromfs)
    assert opath.stat().st_size
    with open(opath, 'rb') as istream:
        assert istream.read(1) == fst
