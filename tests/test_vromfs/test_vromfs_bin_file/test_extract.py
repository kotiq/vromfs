from helpers import make_outpath

outpath = make_outpath(__name__)


def test_extract(vromfs_bin_file, outpath):
    info = vromfs_bin_file.info_list()[-1]
    name = info.name
    out_parent = outpath / vromfs_bin_file.path.stem
    paths = vromfs_bin_file.extract(name, out_parent)
    assert paths[0] == out_parent / name


def test_extract_all(vromfs_bin_file, outpath):
    out_parent = outpath / (vromfs_bin_file.path.stem + '_all')
    paths = vromfs_bin_file.extract_all(out_parent)
    assert paths == [out_parent / name for name in vromfs_bin_file.name_list()]
