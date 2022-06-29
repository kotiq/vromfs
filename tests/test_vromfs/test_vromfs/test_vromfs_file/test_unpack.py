import hashlib
import logging
from pathlib import Path
import pytest
from pytest import param as _
from pytest_lazyfixture import lazy_fixture
from blk import Format
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
    for result in vromfsfile_.unpack_gen(out_path, out_format=out_format):
        if result.error is not None:
            failed += 1
            logger.error(f'[FAIL] {str(in_path)!r}::{str(result.path)!r}: {result.error}')
        else:
            successful += 1

    for path, info in vromfsfile_.info_map.items():
        target = out_path / path
        assert target.exists()
        if out_format is Format.RAW:
            assert info.size == target.stat().st_size

    if vromfsfile_.checked:
        for path, info in vromfsfile_.info_map.items():
            target = out_path / path
            m = hashlib.sha1()
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
    for result in vromfsfile.unpack_gen(out_path, infos, Format.STRICT_BLK):
        if result.error is not None:
            failed += 1
            logger.error(f'[FAIL] {str(in_path)!r}::{str(result.path)!r}: {result.error}')
        else:
            successful += 1

    for info in infos:
        target = out_path / info.path
        assert target.exists()

    logger.info(f'Успешно распаковано: {successful}/{successful+failed}.')

    if failed:
        pytest.fail('Ошибка при обработке файлов.')
