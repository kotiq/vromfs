from pathlib import Path
import pytest


@pytest.fixture(scope='module')
def image_with_hashes():
    return dict(
        names_header=dict(offset=0x30, count=0x02),
        data_header=dict(offset=0x50, count=0x02),
        hashes_header=dict(end=0x98, begin=0x70),
        names_info=[0x40, 0x47],
        names_data=[Path('answer'), Path('greeting')],
        data_info=[dict(offset=0xa0, size=0x02), dict(offset=0xb0, size=0x0c)],
        hashes_data=[
            bytes.fromhex('92cfceb39d57d914ed8b14d0e37643de0797ae56'),
            bytes.fromhex('22596363b3de40b06f981fb85d82312e8c0ed511'),
        ],
        data=[b'42', b'hello world\n'],
    )


@pytest.fixture(scope='module')
def image_with_hash_header_null_begin():
    return dict(
        names_header=dict(offset=0x30, count=0x02),
        data_header=dict(offset=0x50, count=0x02),
        hashes_header=dict(end=0x70, begin=0x00),
        names_info=[0x40, 0x47],
        names_data=[Path('answer'), Path('greeting')],
        data_info=[dict(offset=0x70, size=0x02), dict(offset=0x80, size=0x0c)],
        hashes_data=None,
        data=[b'42', b'hello world\n'],
    )


@pytest.fixture(scope='module')
def image_without_hashes():
    return dict(
        names_header=dict(offset=0x20, count=0x02),
        data_header=dict(offset=0x40, count=0x02),
        hashes_header=None,
        names_info=[0x30, 0x37],
        names_data=[Path('answer'), Path('greeting')],
        data_info=[dict(offset=0x60, size=0x02), dict(offset=0x70, size=0x0c)],
        hashes_data=None,
        data=[b'42', b'hello world\n'],
    )


