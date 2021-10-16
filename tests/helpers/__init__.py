from datetime import datetime
import logging
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


def make_logger(name):
    @pytest.fixture(scope='module')
    def logger(outpath: Path):
        formatter = logging.Formatter('%(asctime)s %(message)s')
        logger_ = logging.getLogger(name)
        logger_.level = logging.INFO

        file_name = datetime.now().strftime('%Y_%m_%d_%H_%M_%S')
        file_handler = logging.FileHandler((outpath / file_name).with_suffix('.log'))
        file_handler.setFormatter(formatter)
        logger_.addHandler(file_handler)

        return logger_

    return logger
