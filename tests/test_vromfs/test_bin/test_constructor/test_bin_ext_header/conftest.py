import io
import typing as t
import pytest


@pytest.fixture(scope='module')
def ext_header_bs() -> bytes:
    return bytes.fromhex(
        '0800'
        '0000'
        '26000902'
    )


@pytest.fixture(scope='module')
def ext_header() -> dict:
    return dict(
        size=0x0008,
        flags=0x0000,
        version=(0x02, 0x09, 0x00, 0x26),
    )


@pytest.fixture(scope='module')
def ext_header_istream(ext_header_bs: bytes) -> t.BinaryIO:
    return io.BytesIO(ext_header_bs)
