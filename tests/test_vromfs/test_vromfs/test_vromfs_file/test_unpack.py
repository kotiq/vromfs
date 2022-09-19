from io import BytesIO
from itertools import chain
from hashlib import sha1
import logging
from pathlib import Path
from pprint import pprint
from typing import MutableMapping, Optional, Tuple, cast
import pytest
from pytest import param as _
from pytest_lazyfixture import lazy_fixture
from blk import Format
from vromfs.bin import BinFile, Version
from vromfs.vromfs import VromfsFile
from helpers import make_tmppath, make_logger, make_outpath

logger = make_logger(__name__)
outpath = make_outpath(__name__)
tmppath = make_tmppath(__name__)


@pytest.mark.parametrize('out_format', [
    _(Format.RAW, id='raw'),
    _(Format.STRICT_BLK, id='strict_blk'),
])
@pytest.mark.parametrize('vromfsfile_', [
    lazy_fixture('vromfsfile'),
    lazy_fixture('vromfsbinfile'),
])
def test_unpack_all_check_digests(vromfsfile_: VromfsFile, out_format: Format, tmppath: Path, logger: logging.Logger):
    in_path = Path(vromfsfile_.name)
    out_path = tmppath / in_path.stem
    failed = successful = 0

    logger.info(f'Начало распаковки {str(in_path)!r}')
    for result in vromfsfile_.unpack_iter(path=out_path, out_format=out_format):
        if result.error is not None:
            failed += 1
            logger.error(f'[FAIL] {str(in_path)!r}::{str(result.path)!r}: {result.error}')
        else:
            successful += 1
    logger.info(f'Конец распаковки {str(in_path)!r}')

    for path, info in vromfsfile_.info_map.items():
        target = out_path / path
        assert target.exists()
        if out_format is Format.RAW:
            assert info.size == target.stat().st_size

    if vromfsfile_.checked:
        for path, info in vromfsfile_.info_map.items():
            target = out_path / path
            m = sha1()
            size = 2**20
            with open(target, 'rb') as istream:
                for chunk in iter(lambda: istream.read(size), b''):
                    m.update(chunk)
            assert info.digest == m.digest()

    logger.info(f'Успешно распаковано: {successful}/{successful+failed}.')

    if failed:
        pytest.fail('Ошибка при обработке файлов.')


def test_unpack_all_blk_strict_blk(vromfsbinfile: VromfsFile, tmppath: Path, logger: logging.Logger):
    vromfsfile = vromfsbinfile
    in_path = Path(vromfsfile.name)
    out_path = tmppath / in_path.stem
    failed = successful = 0
    infos = tuple(filter(lambda i: i.path.suffix == '.blk', vromfsfile.info_map.values()))
    logger.info(f'Начало распаковки {str(in_path)!r}')
    for result in vromfsfile.unpack_iter(infos, out_path, Format.STRICT_BLK):
        if result.error is not None:
            failed += 1
            logger.error(f'[FAIL] {str(in_path)!r}::{str(result.path)!r}: {result.error}')
        else:
            successful += 1
    logger.info(f'Конец распаковки {str(in_path)!r}')

    for info in infos:
        target = out_path / info.path
        assert target.exists()

    logger.info(f'Успешно распаковано: {successful}/{successful+failed}.')

    if failed:
        pytest.fail('Ошибка при обработке файлов.')


def sha1_digest(path: Path, chunk_size: int = 2**20) -> Optional[bytes]:
    m = sha1()
    file_size = path.stat().st_size
    n, r = divmod(file_size, chunk_size)
    try:
        with open(path, 'rb') as istream:
            for _ in range(n):
                chunk = istream.read(chunk_size)
                if len(chunk) != chunk_size:
                    return None
                else:
                    m.update(chunk)
            rem = istream.read(r)
            if len(rem) != r:
                return None
            else:
                m.update(rem)
    except OSError:
        return None
    else:
        return m.digest()


@pytest.mark.parametrize('format_', [Format.RAW, Format.STRICT_BLK], ids=lambda e: e.name.lower())
@pytest.mark.parametrize('root', lazy_fixture(['wtpath', 'enpath']))
def test_unpack_all_files(root: Path, tmppath: Path, logger: logging.Logger, unpack_all: bool, format_: Format):
    if unpack_all:
        version_map: MutableMapping[Tuple[str, Version], Path] = {}
        digest_map: MutableMapping[Tuple[str, bytes], Path] = {}
        rep_paths = []
        err_paths = []
        for in_path in root.rglob('*.vromfs.bin'):
            with BinFile(in_path) as bin_file:
                version = bin_file.version
                if version is not None:
                    key = (in_path.name, version)
                    if key not in version_map:
                        version_map[key] = in_path
                    else:
                        rep_paths.append(in_path)
                else:
                    digest = sha1_digest(in_path)
                    if digest is not None:
                        key = (in_path.name, digest)
                        if key not in digest_map:
                            digest_map[key] = in_path
                        else:
                            rep_paths.append(in_path)
                    else:
                        err_paths.append(in_path)

        for in_path in chain(version_map.values(), digest_map.values()):
            out_path = tmppath / f'{root.name}-{format_.name}' / in_path.relative_to(root)
            failed = successful = 0

            logger.info(f'Начало распаковки {str(in_path)!r}')
            with VromfsFile(BinFile(in_path)) as vromfs:
                for result in vromfs.unpack_iter(path=out_path, out_format=format_):
                    if result.error is not None:
                        failed += 1
                        logger.error(f'[FAIL] {str(in_path)!r}::{str(result.path)!r}: {result.error}')
                    else:
                        successful += 1
            logger.info(f'Конец распаковки {str(in_path)!r}')

            logger.info(f'Успешно распаковано: {successful}/{successful+failed}.')

            if failed:
                pytest.fail('Ошибка при обработке файлов.')
    else:
        pytest.skip("'--unpack-all' cmdline argument")
