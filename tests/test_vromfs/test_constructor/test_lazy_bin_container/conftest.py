import typing as t
import pytest
from vromfs.constructor import HeaderType, PlatformType, PackType


@pytest.fixture(scope='module')
def vrfs_pc_plain_bin_container(image: bytes, hash_: bytes, tail: bytes) -> dict:
    return dict(
        header=dict(
            type=HeaderType.VRFS,
            platform=PlatformType.PC,
            size=len(image),
            packed=dict(type=PackType.PLAIN, size=0),
        ),
        ext_header=None,
        offset=0x10,
        hash=hash_,
        tail=tail,
    )


@pytest.fixture(scope='module')
def vrfx_pc_plain_bin_container(image: bytes, version: t.Tuple[int, int, int, int], hash_: bytes, tail: bytes) -> dict:
    return dict(
        header=dict(
            type=HeaderType.VRFX,
            platform=PlatformType.PC,
            size=len(image),
            packed=dict(type=PackType.PLAIN, size=0),
        ),
        ext_header=dict(
            size=8,
            flags=0,
            version=version,
        ),
        offset=0x18,
        hash=hash_,
        tail=tail,
    )


@pytest.fixture(scope='module')
def vrfx_pc_zstd_obfs_bin_container(image: bytes, version: t.Tuple[int, int, int, int], hash_: bytes,
                                    compressed_image: bytes, tail: bytes) -> dict:
    return dict(
        header=dict(
            type=HeaderType.VRFX,
            platform=PlatformType.PC,
            size=len(image),
            packed=dict(type=PackType.ZSTD_OBFS, size=len(compressed_image)),
        ),
        ext_header=dict(
            size=8,
            flags=0,
            version=version,
        ),
        offset=0x18,
        hash=hash_,
        tail=tail,
    )


@pytest.fixture(scope='module')
def vrfs_pc_zstd_obfs_nocheck_bin_container(image: bytes, compressed_image: bytes, tail: bytes) -> dict:
    return dict(
        header=dict(
            type=HeaderType.VRFS,
            platform=PlatformType.PC,
            size=len(image),
            packed=dict(type=PackType.ZSTD_OBFS_NOCHECK, size=len(compressed_image)),
        ),
        ext_header=None,
        offset=0x10,
        hash=None,
        tail=tail,
    )
