from pathlib import Path
import pytest
from pytest_lazyfixture import lazy_fixture
from vromfs import VromfsBinFile


@pytest.fixture(params=['char.vromfs.bin'], scope='session')
def checked_compressed_file(binrespath: Path, request) -> VromfsBinFile:
    path = binrespath / request.param
    file_obj = VromfsBinFile(path)
    file_obj.path = path
    return file_obj


@pytest.fixture(params=['grp_hdr.vromfs.bin'], scope='session')
def not_checked_compressed_file(binrespath: Path, request) -> VromfsBinFile:
    path = binrespath / request.param
    file_obj = VromfsBinFile(path)
    file_obj.path = path
    return file_obj


@pytest.fixture(params=['fonts.vromfs.bin'], scope='session')
def checked_not_compressed_file(binrespath: Path, request) -> VromfsBinFile:
    path = binrespath / request.param
    file_obj = VromfsBinFile(path)
    file_obj.path = path
    return file_obj


@pytest.fixture(scope='session', params=[
    lazy_fixture('checked_compressed_file'),
    lazy_fixture('checked_not_compressed_file'),
    lazy_fixture('not_checked_compressed_file'),
])
def vromfs_bin_file(binrespath: Path, request):
    return request.param
