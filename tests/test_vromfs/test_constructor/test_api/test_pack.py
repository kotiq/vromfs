import typing as t
import pytest
from pytest_lazyfixture import lazy_fixture
from vromfs.constructor import PlatformType
from vromfs.constructor.eager import pack as eager_pack

version = lazy_fixture('version')
vrfs_pc_plain_bin_container_bs = lazy_fixture('vrfs_pc_plain_bin_container_bs')
vrfx_pc_plain_bin_container_bs = lazy_fixture('vrfx_pc_plain_bin_container_bs')
vrfx_pc_zstd_obfs_bin_container_bs = lazy_fixture('vrfx_pc_zstd_obfs_bin_container_bs')
vrfs_pc_zstd_obfs_nocheck_bin_container_bs = lazy_fixture('vrfs_pc_zstd_obfs_nocheck_bin_container_bs')


@pytest.mark.parametrize(['platform', 'version_', 'compress_', 'check', 'bin_container_bs'], [
    pytest.param(PlatformType.PC, None, False, True,
                 vrfs_pc_plain_bin_container_bs, id='vrfs_pc_plain'),
    pytest.param(PlatformType.PC, version, False, True,
                 vrfx_pc_plain_bin_container_bs, id='vrfx_pc_plain'),
    pytest.param(PlatformType.PC, version, True, True,
                 vrfx_pc_zstd_obfs_bin_container_bs, id='vrfx_pc_zstd_obfs'),
    pytest.param(PlatformType.PC, None, True, False,
                 vrfs_pc_zstd_obfs_nocheck_bin_container_bs, id='vrfs_pc_zstd_obfs_nocheck'),
])
@pytest.mark.parametrize('pack', [
    pytest.param(eager_pack, id='eager'),
])
def test_pack(pack, platform: PlatformType, version_: t.Tuple[int, int, int, int], compress_: bool, check: bool,
              bin_container_bs: bytes, image_istream: t.BinaryIO, ostream: t.BinaryIO, tail: bytes):
    pack(image_istream, ostream, platform, version_, compress_, check, tail)
    ostream.seek(0)
    built = ostream.read()
    assert built == bin_container_bs
