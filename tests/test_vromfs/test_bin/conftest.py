import hashlib
import io
import textwrap
import pytest
import zstandard as zstd
from vromfs.obfs_reader import obfuscate


@pytest.fixture(scope='session')
def data():
    return textwrap.dedent("""\
    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna 
    aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. 
    Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur 
    sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.
    """).encode()


@pytest.fixture(scope='session')
def data_zstd_bin(data):
    stream = io.BytesIO()
    with zstd.ZstdCompressor().stream_writer(stream, closefd=False) as writer:
        writer.write(data)
    return obfuscate(stream.getvalue())


@pytest.fixture(scope='session')
def data_digest(data):
    return hashlib.md5(data).digest()


@pytest.fixture(scope='session')
def vrfs_pc_plain_bin_bytes(data, data_digest):
    return bytes.fromhex('56524673 00005043 c1010000 00000080') + data + data_digest


@pytest.fixture(scope='session')
def vrfx_pc_zstd_obfs_bin_bytes(data_zstd_bin, data_digest):
    return bytes.fromhex(
        '56524678 00005043 c1010000 1b0100c0'
        '08000000 04030201'
    ) + data_zstd_bin + data_digest


@pytest.fixture(scope='session')
def vrfs_pc_zstd_obfs_nocheck_bin_bytes(data_zstd_bin):
    return bytes.fromhex('56524673 00005043 c1010000 1b010040') + data_zstd_bin

