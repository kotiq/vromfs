from pathlib import Path
import pytest
from helpers import make_outpath
from vromfs import VromfsBinFile

outpath = make_outpath(__name__)


@pytest.fixture(scope='module')
def char(binrespath: Path):
    path = binrespath / 'char.vromfs.bin'
    return VromfsBinFile(path)


def test_extract(char: VromfsBinFile, outpath):
    name = 'nm'
    out_parent = outpath / 'char.vromfs'
    paths = char.extract(name, out_parent)
    assert paths[0] == out_parent / name


def test_extract_all(char: VromfsBinFile, outpath):
    out_parent = outpath / 'char_all.vromfs'
    paths = char.extract_all(out_parent)
    assert paths == [out_parent / name for name in char.name_list()]
