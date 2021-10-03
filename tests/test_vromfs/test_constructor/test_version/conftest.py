import io
import typing as t
import pytest
import construct as ct


@pytest.fixture(scope='module')
def version() -> t.Tuple[int, int, int, int]:
    return 1, 2, 3, 4


@pytest.fixture(scope='module')
def version_bs(version: t.Tuple[int, int, int, int]) -> bytes:
    return ct.Byte[4].build(tuple(reversed(version)))


@pytest.fixture(scope='module')
def version_istream(version_bs: bytes) -> t.BinaryIO:
    return io.BytesIO(version_bs)
