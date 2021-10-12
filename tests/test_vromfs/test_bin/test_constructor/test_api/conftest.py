import io
import typing as t
import pytest
from vromfs.bin.constructor import UnpackResult, BinContainerInfo, PlatformType


@pytest.fixture(scope='module')
def vrfs_pc_plain_unpack_result(image: bytes, hash_: bytes) -> UnpackResult:
    return UnpackResult(
        stream=io.BytesIO(image),
        info=BinContainerInfo(
            unpacked_size=len(image),
            packed_size=None,
            hash=hash_,
            version=None,
            platform=PlatformType.PC,
        )
    )


@pytest.fixture(scope='module')
def vrfx_pc_zstd_obfs_unpack_result(image: bytes, obfuscated_compressed_image: bytes,
                                    version: t.Tuple[int, int, int, int], hash_: bytes) -> UnpackResult:
    return UnpackResult(
        stream=io.BytesIO(image),
        info=BinContainerInfo(
            unpacked_size=len(image),
            packed_size=len(obfuscated_compressed_image),
            hash=hash_,
            version=version,
            platform=PlatformType.PC
        )
    )
