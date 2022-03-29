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
    wtpath = {
        'name': 'wtpath',
        'help': 'Директория WarThunder.'
    }
    enpath = {
        'name': 'enpath',
        'help': 'Директория Enlisted.'
    }
    for m in binrespath, buildpath, cdkpath, wtpath, enpath:
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
def wtpath(pytestconfig):
    return Path(pytestconfig.getini('wtpath'))


@pytest.fixture(scope='session')
def enpath(pytestconfig):
    return Path(pytestconfig.getini('enpath'))


@pytest.fixture(scope='session')
def imagespath(binrespath: Path):
    return binrespath / 'images'
