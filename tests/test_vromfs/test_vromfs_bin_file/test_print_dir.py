from pathlib import Path
import pytest
from vromfs import VromfsBinFile


@pytest.fixture(scope='module', params=[
    'char.vromfs.bin',
    'fonts.vromfs.bin',
])
def bin_file(binrespath: Path, request):
    path = binrespath / request.param
    return VromfsBinFile(path)


def test_print_dir(bin_file: VromfsBinFile):
    print()
    bin_file.print_dir()
