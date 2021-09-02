from pathlib import Path
import pytest

# 6.2
# pytest_plugins = "pytester"


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
def binrespath(pytestconfig):
    return Path(pytestconfig.getini('binrespath'))


@pytest.fixture(scope='session')
def buildpath(pytestconfig):
    return Path(pytestconfig.getini('buildpath'))


@pytest.fixture(scope='session')
def cdkpath(pytestconfig):
    return Path(pytestconfig.getini('cdkpath'))


@pytest.fixture(scope='session')
def gamepaths(pytestconfig):
    return tuple(map(Path, pytestconfig.getini('gamepaths')))
