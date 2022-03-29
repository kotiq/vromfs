import io
import pytest
from vromfs.bin import PackType, PlatformType, HeaderType


@pytest.fixture(scope='module')
def vrfx_pc_compressed_header_bytes():
    return bytes.fromhex(
        '56524678'
        '00005043'
        '906e0900'
        '584109c0'
    )


@pytest.fixture(scope='module')
def vrfx_pc_compressed_header():
    return dict(
        type=HeaderType.VRFX,
        platform=PlatformType.PC,
        size=0x096e90,
        packed=dict(
            type=PackType.ZSTD_OBFS,
            size=0x094158,
        )
    )
