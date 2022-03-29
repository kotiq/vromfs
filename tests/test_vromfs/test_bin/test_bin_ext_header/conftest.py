import pytest


@pytest.fixture(scope='module')
def no_flags_ext_header_bytes():
    return bytes.fromhex(
        '0800'
        '0000'
        '26000902'
    )


@pytest.fixture(scope='module')
def no_flags_ext_header():
    return dict(
        size=0x0008,
        flags=0x0000,
        version=(0x02, 0x09, 0x00, 0x26),
    )
