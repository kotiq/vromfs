"""Извлечение vromfs из bin контейнера"""

import logging
from pathlib import Path
import typing as t
import construct as ct
from vromfs.bin.constructor.error import BinUnpackError, BinDecompressionError
from vromfs.bin.constructor import UnpackResult
from vromfs.bin.constructor.eager import unpack
from helpers import make_logger, make_outpath

outpath = make_outpath(__name__)
logger = make_logger(__name__)


def unpack_path(src: Path, dst: Path, decompress: bool, logger: logging.Logger):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, 'rb') as istream:
        result: UnpackResult = unpack(istream, decompress)
        size = result.info.unpacked_size
        try:
            data = ct.stream_read(result.stream, size)
            with open(dst, 'wb') as ostream:
                ct.stream_write(ostream, data, size)
        except ct.ConstructError as e:
            logger.info(f'[FAIL] {dst}: {type(e)} {e}')


def test_unbin(gamepaths: t.Iterable[Path], imagespath: Path, outpath: Path, logger: logging.Logger):
    for gamepath in gamepaths:
        gamename = gamepath.name
        for binpath in gamepath.rglob('*.vromfs.bin'):
            rel_vromfspath = gamename / binpath.relative_to(gamepath).with_suffix('')
            vromfspath = imagespath / rel_vromfspath
            try:
                unpack_path(binpath, vromfspath, decompress=True, logger=logger)
                logger.info(f'[OK] {binpath} => {vromfspath}')
            except BinDecompressionError as e:
                zstd_vromfspath = outpath / rel_vromfspath.with_suffix('.zst.err')
                unpack_path(binpath, zstd_vromfspath, decompress=False, logger=logger)
                cause = e.__cause__
                logger.info(f'[FAIL] {binpath}: Ошибка в архиве: {cause}')
                logger.info(f'[FAIL] {binpath} => {zstd_vromfspath}')
            except BinUnpackError as e:
                cause = e.__cause__
                if cause:
                    message = f'[FAIL] {binpath}: {type(cause)} {cause}'
                else:
                    message = f'[FAIL] {binpath}: {e}'
                logger.info(message)
