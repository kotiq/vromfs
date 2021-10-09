"""Извлечение vromfs из bin контейнера"""

import logging
import typing as t
from pathlib import Path
from vromfs.bin.constructor.error import UnpackError, DecompressionError
from vromfs.bin.constructor.eager import unpack
from helpers import make_outpath

outpath = make_outpath(__name__)


def unpack_path(src: Path, dst: Path, decompress: bool = True):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, 'rb') as istream:
        result = unpack(istream, decompress)
        dst.write_bytes(result.stream.read())


def test_unbin(gamepaths: t.Iterable[Path], binrespath: Path, outpath: Path):
    for gamepath in gamepaths:
        gamename = gamepath.name
        for binpath in gamepath.rglob('*.vromfs.bin'):
            rel_vromfspath = gamename / binpath.relative_to(gamepath).with_suffix('')
            vromfspath = binrespath / rel_vromfspath
            try:
                unpack_path(binpath, vromfspath)
                logging.info(f'[OK] {binpath} => {vromfspath}')
            except DecompressionError as e:
                zstd_vromfspath = outpath / rel_vromfspath.with_suffix('.zst.err')
                unpack_path(binpath, zstd_vromfspath, False)
                cause = e.__cause__
                logging.info(f'[FAIL] {binpath}: Ошибка в архиве: {cause}')
                logging.info(f'[FAIL] {binpath} => {zstd_vromfspath}')
            except UnpackError as e:
                cause = e.__cause__
                logging.info(f'[FAIL] {binpath}: {type(cause)} {cause}')
