import typing as t
import pytest
from pytest_lazyfixture import lazy_fixture
from vromfs.constructor import unpack, UnpackResult

vrfs_pc_plain_unpack_result = lazy_fixture('vrfs_pc_plain_unpack_result')
vrfx_pc_zstd_obfs_unpack_result = lazy_fixture('vrfx_pc_zstd_obfs_unpack_result')
vrfs_pc_plain_bin_container_istream = lazy_fixture('vrfs_pc_plain_bin_container_istream')
vrfx_pc_zstd_obfs_bin_container_istream = lazy_fixture('vrfx_pc_zstd_obfs_bin_container_istream')


@pytest.mark.parametrize(['bin_container_istream', 'unpack_result'], [
    pytest.param(
        vrfs_pc_plain_bin_container_istream,
        vrfs_pc_plain_unpack_result,
        id='vrfs_pc_plain'
    ),
    pytest.param(
        vrfx_pc_zstd_obfs_bin_container_istream,
        vrfx_pc_zstd_obfs_unpack_result,
        id='vrfx_pc_zstd_obfs',
    )
])
def test_unpack(bin_container_istream: t.BinaryIO, unpack_result: UnpackResult, image: bytes):
    result = unpack(bin_container_istream)
    assert result.info == unpack_result.info
    bs = result.ostream.read()
    assert bs == image
