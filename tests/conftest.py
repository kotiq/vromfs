from pathlib import Path
import pytest


def pytest_addoption(parser):
    binrespath = {
        'name': 'binrespath',
        'help': 'Директория с образцами двоичных blk.',
    }
    buildpath = {
        'name': 'buildpath',
        'help': 'Директория для построения тестами.'
    }
    cdkpath = {
        'name': 'cdkpath',
        'help': 'Директория WarThunderCDK.'
    }
    gamepath = {
        'name': 'gamepaths',
        'type': 'pathlist',
        'help': 'Директории WarThunder, Enlisted'
    }

    for m in binrespath, buildpath, cdkpath, gamepath:
        parser.addini(**m)


@pytest.fixture(scope='session')
def binrespath(request):
    return Path(request.config.getini('binrespath'))


@pytest.fixture(scope='session')
def buildpath(request):
    return Path(request.config.getini('buildpath'))


@pytest.fixture(scope='session')
def cdkpath(request):
    return Path(request.config.getini('cdkpath'))


@pytest.fixture(scope='session')
def gamepaths(request):
    return tuple(map(Path, request.config.getini('gamepaths')))
