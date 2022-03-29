import pytest
from vromfs.bin import HeaderType, PlatformType, PackType


@pytest.fixture(scope='module')
def vrfs_pc_plain_bin_container(data_digest):
    return {
        'header': {
            'type': HeaderType.VRFS,
            'platform': PlatformType.PC,
            'size': 0x01c1,
            'packed': {
                'type': PackType.PLAIN,
                'size': 0x0,
            },
        },
        'ext_header': None,
        'offset': 0x10,
        'digest': data_digest,
        'extra': b'',
    }


@pytest.fixture(scope='module')
def vrfx_pc_zstd_obfs_bin_container(data_digest):
    return {
        'header': {
            'type': HeaderType.VRFX,
            'platform': PlatformType.PC,
            'size': 0x01c1,
            'packed': {
                'type': PackType.ZSTD_OBFS,
                'size': 0x011b,
            },
        },
        'ext_header': {
            'size': 0x08,
            'flags': 0,
            'version': (1, 2, 3, 4)
        },
        'offset': 0x18,
        'digest': data_digest,
        'extra': b'',
    }


@pytest.fixture(scope='module')
def vrfs_pc_zstd_obfs_nocheck_bin_container(data_digest):
    return {
        'header': {
            'type': HeaderType.VRFS,
            'platform': PlatformType.PC,
            'size': 0x01c1,
            'packed': {
                'type': PackType.ZSTD_OBFS_NOCHECK,
                'size': 0x011b,
            },
        },
        'ext_header': None,
        'offset': 0x10,
        'digest': None,
        'extra': b'',
    }
