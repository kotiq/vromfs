import hashlib
import io
import typing as t
import construct as ct
import pytest
import zstandard as zstd
from vromfs.constructor import HeaderType, PlatformType, PackType


@pytest.fixture(scope='session')
def image() -> bytes:
    return b' '.join([b'hello beautiful world']*2)  # len = 43


@pytest.fixture(scope='session')
def hash_(image: bytes) -> bytes:
    return hashlib.md5(image).digest()


@pytest.fixture(scope='session')
def version() -> t.Tuple[int, int, int, int]:
    return 1, 2, 3, 4


@pytest.fixture(scope='session')
def compressed_image(image: bytes) -> bytes:
    return zstd.compress(image)  # len = 37


@pytest.fixture(scope='session')
def obfuscated_compressed_image(compressed_image: bytes) -> bytes:
    hk = bytes.fromhex('55aa55aa0ff00ff055aa55aa48124812')
    fk = bytes.fromhex('4812481255aa55aa0ff00ff055aa55aa')
    assert len(hk) == len(fk) == 16

    sz = len(compressed_image)
    if sz < 16:
        out = compressed_image
    else:
        untouched_pos = 16
        header = bytes(x ^ y for x, y in zip(compressed_image[:untouched_pos], hk))
        if sz < 32:
            untouched = compressed_image[untouched_pos:]
            out = header + untouched
        else:
            tail_pos = sz & 0x03ff_fffc
            footer_pos = tail_pos - 16
            untouched = compressed_image[untouched_pos:footer_pos]
            footer = bytes(x ^ y for x, y in zip(compressed_image[footer_pos:tail_pos], fk))
            tail = compressed_image[tail_pos:]
            out = header + untouched + footer + tail

    return out


@pytest.fixture(scope='session')
def tail() -> bytes:
    return b'\xff'*0x100


@pytest.fixture(scope='session')
def vrfs_pc_plain_bin_container_bs(image: bytes, hash_: bytes, tail: bytes) -> bytes:
    ostream = io.BytesIO()
    ct.stream_write(ostream, HeaderType.VRFS.value, 4)
    ct.stream_write(ostream, PlatformType.PC.value, 4)
    ct.Int32ul.build_stream(len(image), ostream)
    packed_size = 0 & 0x03ff_ffff
    ct.Int32ul.build_stream(packed_size | PackType.PLAIN.value << 26, ostream)
    ct.stream_write(ostream, image, len(image))
    ct.stream_write(ostream, hash_, len(hash_))
    ct.stream_write(ostream, tail, len(tail))

    return ostream.getvalue()


@pytest.fixture(scope='session')
def vrfx_pc_plain_bin_container_bs(image: bytes, version: t.Tuple[int, int, int, int], hash_: bytes,
                                   tail: bytes) -> bytes:
    ostream = io.BytesIO()
    ct.stream_write(ostream, HeaderType.VRFX.value, 4)
    ct.stream_write(ostream, PlatformType.PC.value, 4)
    ct.Int32ul.build_stream(len(image), ostream)
    packed_size = 0 & 0x03ff_ffff
    ct.Int32ul.build_stream(packed_size | PackType.PLAIN.value << 26, ostream)
    ct.Int16ul.build_stream(8, ostream)
    ct.Int16ul.build_stream(0, ostream)
    ct.Byte[4].build_stream(tuple(reversed(version)), ostream)
    ct.stream_write(ostream, image, len(image))
    ct.stream_write(ostream, hash_, len(hash_))
    ct.stream_write(ostream, tail, len(tail))

    return ostream.getvalue()


@pytest.fixture(scope='session')
def vrfx_pc_zstd_obfs_bin_container_bs(image: bytes, version: t.Tuple[int, int, int, int], hash_: bytes,
                                       obfuscated_compressed_image: bytes, tail: bytes) -> bytes:
    ostream = io.BytesIO()
    ct.stream_write(ostream, HeaderType.VRFX.value, 4)
    ct.stream_write(ostream, PlatformType.PC.value, 4)
    ct.Int32ul.build_stream(len(image), ostream)
    packed_size = len(obfuscated_compressed_image) & 0x03ff_ffff
    ct.Int32ul.build_stream(packed_size | PackType.ZSTD_OBFS.value << 26, ostream)
    ct.Int16ul.build_stream(8, ostream)
    ct.Int16ul.build_stream(0, ostream)
    ct.Byte[4].build_stream(tuple(reversed(version)), ostream)
    ct.stream_write(ostream, obfuscated_compressed_image, len(obfuscated_compressed_image))
    ct.stream_write(ostream, hash_, len(hash_))
    ct.stream_write(ostream, tail, len(tail))

    return ostream.getvalue()


@pytest.fixture(scope='session')
def vrfs_pc_zstd_obfs_nocheck_bin_container_bs(image: bytes, obfuscated_compressed_image: bytes, tail: bytes) -> bytes:
    ostream = io.BytesIO()
    ct.stream_write(ostream, HeaderType.VRFS.value, 4)
    ct.stream_write(ostream, PlatformType.PC.value, 4)
    ct.Int32ul.build_stream(len(image), ostream)
    packed_size = len(obfuscated_compressed_image) & 0x03ff_ffff
    ct.Int32ul.build_stream(packed_size | PackType.ZSTD_OBFS_NOCHECK.value << 26, ostream)
    ct.stream_write(ostream, obfuscated_compressed_image, len(obfuscated_compressed_image))
    ct.stream_write(ostream, tail, len(tail))

    return ostream.getvalue()


@pytest.fixture(scope='session')
def vrfs_pc_plain_bin_container_istream(vrfs_pc_plain_bin_container_bs: bytes) -> io.BytesIO:
    return io.BytesIO(vrfs_pc_plain_bin_container_bs)


@pytest.fixture(scope='session')
def vrfx_pc_plain_bin_container_istream(vrfx_pc_plain_bin_container_bs: bytes) -> io.BytesIO:
    return io.BytesIO(vrfx_pc_plain_bin_container_bs)


@pytest.fixture(scope='session')
def vrfx_pc_zstd_obfs_bin_container_istream(vrfx_pc_zstd_obfs_bin_container_bs: bytes) -> io.BytesIO:
    return io.BytesIO(vrfx_pc_zstd_obfs_bin_container_bs)


@pytest.fixture(scope='session')
def vrfs_pc_zstd_obfs_nocheck_bin_container_istream(vrfs_pc_zstd_obfs_nocheck_bin_container_bs: bytes) -> io.BytesIO:
    return io.BytesIO(vrfs_pc_zstd_obfs_nocheck_bin_container_bs)


@pytest.fixture(scope='session')
def vrfs_pc_plain_bin_container(image: bytes, hash_: bytes, tail: bytes) -> dict:
    return dict(
        header=dict(
            type=HeaderType.VRFS,
            platform=PlatformType.PC,
            size=len(image),
            packed=dict(type=PackType.PLAIN, size=0),
        ),
        ext_header=None,
        offset=0x10,
        hash=hash_,
        tail=tail,
    )


@pytest.fixture(scope='session')
def vrfx_pc_plain_bin_container(image: bytes, version: t.Tuple[int, int, int, int], hash_: bytes, tail: bytes) -> dict:
    return dict(
        header=dict(
            type=HeaderType.VRFX,
            platform=PlatformType.PC,
            size=len(image),
            packed=dict(type=PackType.PLAIN, size=0),
        ),
        ext_header=dict(
            size=8,
            flags=0,
            version=version,
        ),
        offset=0x18,
        hash=hash_,
        tail=tail,
    )


@pytest.fixture(scope='session')
def vrfx_pc_zstd_obfs_bin_container(image: bytes, version: t.Tuple[int, int, int, int], hash_: bytes,
                                    compressed_image: bytes, tail: bytes) -> dict:
    return dict(
        header=dict(
            type=HeaderType.VRFX,
            platform=PlatformType.PC,
            size=len(image),
            packed=dict(type=PackType.ZSTD_OBFS, size=len(compressed_image)),
        ),
        ext_header=dict(
            size=8,
            flags=0,
            version=version,
        ),
        offset=0x18,
        hash=hash_,
        tail=tail,
    )


@pytest.fixture(scope='session')
def vrfs_pc_zstd_obfs_nocheck_bin_container(image: bytes, compressed_image: bytes, tail: bytes) -> dict:
    return dict(
        header=dict(
            type=HeaderType.VRFS,
            platform=PlatformType.PC,
            size=len(image),
            packed=dict(type=PackType.ZSTD_OBFS_NOCHECK, size=len(compressed_image)),
        ),
        ext_header=None,
        offset=0x10,
        hash=None,
        tail=tail,
    )


@pytest.fixture()
def ostream():
    return io.BytesIO()
