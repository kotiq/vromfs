"""Извлечение файлов "как есть" из vromfs образа"""

import logging
from pathlib import Path
import typing as t
import construct as ct
import pytest
from vromfs.vromfs.constructor import File
from vromfs.vromfs.constructor.lazy import unpack
from vromfs.vromfs.constructor.error import VromfsUnpackError
from helpers import make_logger, make_outpath

outpath = make_outpath(__name__)
logger = make_logger(__name__)


def ubpack_path(src: Path, dst: Path, decompress: bool, logger: logging.Logger):
    if decompress:
        raise NotImplementedError('Извлечение сжатых файлов не реализовано.')

    with open(src, 'rb') as istream:
        files: t.Sequence[File] = unpack(istream)
        for file in files:
            path = dst / file.path
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                data: bytes = ct.stream_read(file.stream, file.size)
                with open(path, 'wb') as ostream:
                    ct.stream_write(ostream, data, file.size)
                logger.info(f'[OK] {src}::{file.path} => {path}')
                if file.path.suffix == '.blk':
                    if data.startswith(b'\x00BBF'):
                        type_ = 'bbf'
                    elif data.startswith(b'\x00BBz'):
                        type_ = 'bbz'
                    elif data.startswith(b'\x01'):
                        type_ = 'fat'
                    elif data.startswith(b'\x02'):
                        type_ = 'fat_zst'
                    elif data.startswith(b'\x03'):
                        type_ = 'slim'
                    elif data.startswith(b'\x04'):
                        type_ = 'slim_zst'
                    elif data.startswith(b'\x05'):
                        type_ = 'slim_zst_dict'
                    else:
                        type_ = 'unknown'
                    logger.info(f'[INFO] {path}: {type_}')
            except ct.ConstructError as e:
                logger.info(f'[FAIL] {path}: {type(e)} {e}')


@pytest.fixture(scope='module')
def filespath(binrespath: Path):
    return binrespath / 'files'


def test_unvromfs(imagespath: Path, filespath: Path, outpath: Path, logger: logging.Logger):
    for imagepath in imagespath.rglob('*.vromfs'):
        rel_vromfspath = imagepath.relative_to(imagespath).with_suffix('')
        image_filespath = filespath / rel_vromfspath
        try:
            ubpack_path(imagepath, image_filespath, decompress=False, logger=logger)
            logger.info(f'[OK] {imagepath} => {image_filespath}')
        except VromfsUnpackError as e:
            cause = e.__cause__
            if cause:
                message = f'[FAIL] {imagepath}: {type(cause)} {cause}'
            else:
                message = f'[FAIL] {imagepath}: {e}'
            logger.info(message)

