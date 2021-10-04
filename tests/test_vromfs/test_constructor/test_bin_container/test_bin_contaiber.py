import typing as t
import pytest
from pytest_lazyfixture import lazy_fixture
from vromfs.constructor import BinContainer
from test_vromfs.test_constructor import _test_parse, _test_build

vrfs_pc_plain_bin_container_istream = lazy_fixture('vrfs_pc_plain_bin_container_istream')
vrfs_pc_plain_bin_container_bs = lazy_fixture('vrfs_pc_plain_bin_container_bs')
vrfs_pc_plain_bin_container = lazy_fixture('vrfs_pc_plain_bin_container')

vrfx_pc_plain_bin_container_istream = lazy_fixture('vrfx_pc_plain_bin_container_istream')
vrfx_pc_plain_bin_container_bs = lazy_fixture('vrfx_pc_plain_bin_container_bs')
vrfx_pc_plain_bin_container = lazy_fixture('vrfx_pc_plain_bin_container')

vrfx_pc_zstd_obfs_bin_container_istream = lazy_fixture('vrfx_pc_zstd_obfs_bin_container_istream')
vrfx_pc_zstd_obfs_bin_container_bs = lazy_fixture('vrfx_pc_zstd_obfs_bin_container_bs')
vrfx_pc_zstd_obfs_bin_container = lazy_fixture('vrfx_pc_zstd_obfs_bin_container')

vrfs_pc_zstd_obfs_nocheck_bin_container_istream = lazy_fixture('vrfs_pc_zstd_obfs_nocheck_bin_container_istream')
vrfs_pc_zstd_obfs_nocheck_bin_container_bs = lazy_fixture('vrfs_pc_zstd_obfs_nocheck_bin_container_bs')
vrfs_pc_zstd_obfs_nocheck_bin_container = lazy_fixture('vrfs_pc_zstd_obfs_nocheck_bin_container')


@pytest.mark.parametrize(['bin_container_istream', 'bin_container_bs', 'bin_container'], [
    pytest.param(
        vrfs_pc_plain_bin_container_istream,
        vrfs_pc_plain_bin_container_bs,
        vrfs_pc_plain_bin_container,
        id='vrfs_pc_plain'
    ),
    pytest.param(
        vrfx_pc_plain_bin_container_istream,
        vrfx_pc_plain_bin_container_bs,
        vrfx_pc_plain_bin_container,
        id='vrfx_pc_plain'
    ),
    pytest.param(
        vrfx_pc_zstd_obfs_bin_container_istream,
        vrfx_pc_zstd_obfs_bin_container_bs,
        vrfx_pc_zstd_obfs_bin_container,
        id='vrfx_pc_zstd_obfs'
    ),
    pytest.param(
        vrfs_pc_zstd_obfs_nocheck_bin_container_istream,
        vrfs_pc_zstd_obfs_nocheck_bin_container_bs,
        vrfs_pc_zstd_obfs_nocheck_bin_container,
        id='vrfs_pc_zstd_obfs_nocheck'
    ),
])
def test_bin_container_parse(bin_container_istream: t.BinaryIO, bin_container_bs: bytes, bin_container: dict):
    _test_parse(BinContainer, bin_container_istream, bin_container_bs, bin_container)
