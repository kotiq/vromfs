from pathlib import Path
import filecmp
import pytest
from vromfs.parser import FileInfo
from vromfs import VromfsBinFile
from helpers import make_tmppath

tmppath = make_tmppath(__name__)


def test_extract(vromfs_bin_file: VromfsBinFile, tmppath: Path):
    info: FileInfo = vromfs_bin_file.info_list()[-1]
    name = info.name
    out_parent = tmppath / vromfs_bin_file.path.stem
    path = vromfs_bin_file.extract(name, out_parent)
    assert path == out_parent / name
    assert path.stat().st_size == info.size


@pytest.fixture(scope='module')
def unpacked_vromfs_bin_file(vromfs_bin_file: VromfsBinFile, tmppath: Path):
    out_parent = tmppath / (vromfs_bin_file.path.stem + '_all_by_one')
    for info in vromfs_bin_file.info_list():
        vromfs_bin_file.extract(info, out_parent)

    return out_parent


def diff_files(dcmp: filecmp.dircmp):
    for name in dcmp.diff_files:
        yield name, dcmp.left, dcmp.right
    for sub_dcmp in dcmp.subdirs.values():
        yield from diff_files(sub_dcmp)


def test_extract_all(unpacked_vromfs_bin_file: Path, vromfs_bin_file: VromfsBinFile, tmppath: Path):
    out_parent = tmppath / (vromfs_bin_file.path.stem + '_all')
    vromfs_bin_file.extract_all(out_parent)
    dcmp = filecmp.dircmp(unpacked_vromfs_bin_file, out_parent)
    for name, left, right in diff_files(dcmp):
        pytest.fail("Директории различны: {}, {}, {}".format(name, left, right))
