import io
from pathlib import Path
import pytest


@pytest.fixture(scope='module')
def names():
    return [Path('rate'), Path('separate')]


@pytest.fixture(scope='module')
def separate_names_data_bs():
    return b'rate\x00separate\x00'


@pytest.fixture(scope='function')
def separate_names_data_istream(separate_names_data_bs):
    return io.BytesIO(separate_names_data_bs)


@pytest.fixture(scope='module')
def separate_offsets():
    return [0, 5]


@pytest.fixture(scope='module')
def reversed_separate_names_data_bs():
    return b'separate\x00rate\x00'


@pytest.fixture(scope='function')
def reversed_separate_names_data_istream(reversed_separate_names_data_bs: bytes):
    return io.BytesIO(reversed_separate_names_data_bs)


@pytest.fixture(scope='module')
def reversed_separate_offsets():
    return [9, 0]


@pytest.fixture(scope='module')
def overlapping_names_data_bs():
    return b'separate\x00'


@pytest.fixture(scope='function')
def overlapping_names_data_istream(overlapping_names_data_bs: bytes):
    return io.BytesIO(overlapping_names_data_bs)


@pytest.fixture(scope='module')
def overlapping_offsets():
    return [4, 0]
