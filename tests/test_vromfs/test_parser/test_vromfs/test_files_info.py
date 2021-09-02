"""Проверка BinContainer.info"""

import io
from pathlib import Path
import typing as t
import pytest
from helpers import make_outpath
from vromfs.parser import BinContainer, RangedReader, FileInfo

outpath = make_outpath(__name__)


def dump_files_info(files_info: t.Sequence[FileInfo], stream: t.TextIO):
    for i, info in enumerate(files_info):
        print(f'{i:3} {info.name} {info.offset:#010x} {info.size:#010x}', file=stream)


@pytest.mark.parametrize('rpath', [
    'fonts.vromfs.bin',
])
def test_ident_files_info(binrespath: Path, outpath: Path, rpath: str,):
    """Построение карт несжатых vromfs."""

    ipath = binrespath / rpath
    with open(ipath, 'rb') as istream:
        bin_container = BinContainer.parse_stream(istream)
        info = bin_container.info
        assert isinstance(info.stream, RangedReader)

    opath = (outpath / rpath).with_suffix('.txt')
    with open(opath, 'w') as ostream:
        dump_files_info(info.files_info, ostream)


@pytest.mark.parametrize('rpath', [
    'char.vromfs.bin',
    'grp_hdr.vromfs.bin',
])
def test_compressed_files_info(binrespath: Path, outpath: Path, rpath: str):
    """Построение карт сжатых vromfs."""

    ipath = binrespath / rpath
    with open(ipath, 'rb') as istream:
        bin_container = BinContainer.parse_stream(istream)
        info = bin_container.info
        assert isinstance(info.stream, io.BytesIO)

    opath = (outpath / rpath).with_suffix('.txt')
    with open(opath, 'w') as ostream:
        dump_files_info(info.files_info, ostream)
