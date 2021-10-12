import io
import typing as t
import construct as ct
import zstandard as zstd
from vromfs.reader import RangedReader
from .error import BinUnpackError
from .common import BinHeader, HeaderType, BinExtHeader, PackType, UnpackResult, BinContainerInfo

BinContainer = ct.Struct(
    'header' / BinHeader,
    'ext_header' / ct.If(lambda ctx: ctx.header.type is HeaderType.VRFX, BinExtHeader),
    'offset' / ct.Tell,
    ct.Seek(lambda ctx: ctx.header.size
            if ctx.header.packed.type is PackType.PLAIN
            else ctx.header.packed.size, io.SEEK_CUR),
    'hash' / ct.If(lambda ctx: ctx.header.packed.type is not PackType.ZSTD_OBFS_NOCHECK, ct.Bytes(16)),
    'tail' / ct.GreedyBytes,
    ct.Check(lambda ctx: len(ctx.tail) in (0, 0x100)),
)


def decompress(istream: t.BinaryIO) -> t.BinaryIO:
    """
    Извлечение образа из архива.

    :param istream: входной поток сжатого образа
    :return: выходной поток несжатого образа
    """

    dctx = zstd.ZstdDecompressor()
    return dctx.stream_reader(istream)


def inplace_xor(buffer: bytearray, from_: int, sz: int, key: t.Iterable[int]) -> None:
    it = iter(key)
    for i in range(from_, from_ + sz):
        buffer[i] ^= next(it)


obfs_ks: t.Sequence[bytes] = [bytes.fromhex(s) for s in ('55aa55aa', '0ff00ff0', '55aa55aa', '48124812')]


# todo: перестроить как ленивый FileReader
def deobfuscate(istream: t.BinaryIO, sz: int) -> t.BinaryIO:
    """
    Восстановление частей сжатого образа.

    :param istream: входной поток сжатого образа
    :param sz: размер сжатого образа
    :return: выходной поток сжатого образа с измененными частями
    """

    bs = istream.read()
    buffer = bytearray(bs)
    key_sz = sum(map(len, obfs_ks))
    if sz >= key_sz:
        pos = 0
        inplace_xor(buffer, pos, key_sz, b''.join(obfs_ks))
        if sz >= 2 * key_sz:
            pos = (sz & 0x03ff_fffc) - key_sz
            inplace_xor(buffer, pos, key_sz, b''.join(reversed(obfs_ks)))

    return io.BytesIO(buffer)


def unpack(istream: t.BinaryIO) -> UnpackResult:
    """
    Распаковка образа из bin контейнера.

    :param istream: входной поток контейнера
    :return: результат распаковки
    """

    try:
        bin_container = BinContainer.parse_stream(istream)
    except ct.ConstructError as e:
        raise BinUnpackError from e
    else:
        pack_type: PackType = bin_container.header.packed.type

        if pack_type not in (PackType.PLAIN, PackType.ZSTD_OBFS, pack_type.ZSTD_OBFS_NOCHECK):
            raise BinUnpackError("Unknown pack_type: {}".format(pack_type))

        offset = bin_container.offset
        size = bin_container.header.size
        platform = bin_container.header.platform

        header_type = bin_container.header.type
        version = None if header_type is HeaderType.VRFS else bin_container.ext_header.version
        packed_size = None if pack_type is PackType.PLAIN else bin_container.header.packed.size
        hash_ = None if pack_type is PackType.ZSTD_OBFS_NOCHECK else bin_container.hash

        ostream = (RangedReader(istream, offset, offset+size)
                   if pack_type is PackType.PLAIN
                   else decompress(deobfuscate(RangedReader(istream, offset, offset+packed_size), packed_size)))

        return UnpackResult(
            stream=ostream,
            info=BinContainerInfo(
                unpacked_size=size,
                packed_size=packed_size,
                hash=hash_,
                version=version,
                platform=platform
            )
        )
