from pathlib import Path
import typing as t
from vromfs.parser import FileInfo
from vromfs import VromfsBinFile
from helpers import make_outpath

outpath = make_outpath(__name__)


def test_extract(vromfs_bin_file: VromfsBinFile, outpath: Path):
    info: FileInfo = vromfs_bin_file.info_list()[-1]
    name = info.name
    out_parent = outpath / vromfs_bin_file.path.stem
    paths: t.Sequence[Path] = vromfs_bin_file.extract(name, out_parent)
    assert paths[0] == out_parent / name
    assert paths[0].stat().st_size == info.size


def test_extract_all(vromfs_bin_file: VromfsBinFile, outpath):
    out_parent = outpath / (vromfs_bin_file.path.stem + '_all')
    paths = vromfs_bin_file.extract_all(out_parent)
    assert paths == [out_parent / name for name in vromfs_bin_file.name_list()]
    for path, info in zip(paths, vromfs_bin_file.info_list()):
        assert path.stat().st_size == info.size
