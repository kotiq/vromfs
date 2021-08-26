from pathlib import Path
import pytest
from vromfs import VromfsBinFile


@pytest.fixture(params=['char.vromfs.bin'], scope='module')
def checked_compressed_file(binrespath: Path, request) -> VromfsBinFile:
    path = binrespath / request.param
    return VromfsBinFile(path)


@pytest.fixture(params=['grp_hdr.vromfs.bin'], scope='module')
def not_checked_compressed_file(binrespath: Path, request) -> VromfsBinFile:
    path = binrespath / request.param
    return VromfsBinFile(path)


@pytest.fixture(params=['fonts.vromfs.bin'], scope='module')
def checked_not_compressed_file(binrespath: Path, request) -> VromfsBinFile:
    path = binrespath / request.param
    return VromfsBinFile(path)


def _test_checked_file(file: VromfsBinFile):
    result = file.check(inner=True)
    assert result.status, result.failed


def _test_not_checked_file(file: VromfsBinFile):
    result = file.check()
    assert result.status is None


def test_compressed_file(checked_compressed_file: VromfsBinFile):
    _test_checked_file(checked_compressed_file)


def test_not_compressed_file(checked_not_compressed_file: VromfsBinFile):
    _test_checked_file(checked_not_compressed_file)


def test_not_checked_compressed_file(not_checked_compressed_file: VromfsBinFile):
    _test_not_checked_file(not_checked_compressed_file)
