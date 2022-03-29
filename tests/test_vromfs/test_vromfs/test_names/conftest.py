from pathlib import Path
import pytest


@pytest.fixture(scope='module')
def names():
    return [Path(name) for name in ('rate', 'separate')]


@pytest.fixture(scope='module')
def separate_bytes():
    return b'rate\x00separate\x00'


@pytest.fixture(scope='module')
def separate_offsets():
    return [0, 5]


@pytest.fixture(scope='module')
def reversed_separate_bytes():
    return b'separate\x00rate\x00'


@pytest.fixture(scope='module')
def reversed_separate_offsets():
    return [9, 0]


@pytest.fixture(scope='module')
def overlapping_bytes():
    return b'separate\x00'


@pytest.fixture(scope='module')
def overlapping_offsets():
    return [4, 0]
