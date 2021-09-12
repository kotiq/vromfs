from pathlib import Path
import pytest


def _outdir_rpath(name):
    return Path('tests', *name.split('.'))


def make_outpath(name):
    @pytest.fixture(scope='module')
    def outpath(buildpath):
        path = buildpath / _outdir_rpath(name)
        path.mkdir(parents=True, exist_ok=True)
        return path

    return outpath


def make_tmppath(name):
    @pytest.fixture(scope='module')
    def tmppath(tmp_path_factory):
        return tmp_path_factory.mktemp(name)

    return tmppath


def create_text(path):
    return open(path, 'w', newline='', encoding='utf8')

