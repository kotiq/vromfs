import io
import typing as t
import pytest
from vromfs.constructor import PackType, PlatformType, HeaderType


@pytest.fixture(scope='module')
def vrfx_pc_compressed_header_bs() -> bytes:
    return bytes.fromhex(
        '56524678'
        '00005043'
        '906e0900'
        '584109c0'
    )


@pytest.fixture(scope='module')
def vrfx_pc_compressed_header() -> dict:
    return dict(
        type=HeaderType.VRFX,
        platform=PlatformType.PC,
        size=0x096e90,
        packed=dict(
            type=PackType.ZSTD_OBFS,
            size=0x094158,
        )
    )


@pytest.fixture(scope='module')
def vrfx_pc_compressed_header_istream(vrfx_pc_compressed_header_bs: bytes) -> t.BinaryIO:
    return io.BytesIO(vrfx_pc_compressed_header_bs)
