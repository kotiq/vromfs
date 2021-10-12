import io
import pytest


@pytest.fixture()
def ostream():
    return io.BytesIO()
