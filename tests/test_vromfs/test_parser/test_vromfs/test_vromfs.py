"""Проверка VromfsInfo и FilesInfo."""

import pytest
from vromfs.parser import VromfsInfo, FilesInfo
from .data import vromfs_bs_20, vromfs_bs_30, info_20, info_30, files_info_20, files_info_30


@pytest.mark.parametrize(['vromfs_bs', 'info'], [
    pytest.param(vromfs_bs_20, info_20, id='20'),
    pytest.param(vromfs_bs_30, info_30, id='30'),
])
def test_vroms_info_parse(vromfs_bs, info):
    ns = VromfsInfo.parse(vromfs_bs)
    for name in info:
        assert ns[name] == info[name], name


@pytest.mark.parametrize(['vromfs_bs', 'files_info'], [
    pytest.param(vromfs_bs_20, files_info_20, id='20'),
    pytest.param(vromfs_bs_30, files_info_30, id='30'),
])
def test_files_info_parse(vromfs_bs, files_info):
    assert files_info == FilesInfo.parse(vromfs_bs)
