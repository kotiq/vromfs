import io
from enum import Enum
from pathlib import Path
import typing as t
import construct as ct
import zstandard as zstd
from construct import this
from .reader import RangedReader


class HeaderType(Enum):
    VRFS = b'VRFs'
    VRFX = b'VRFx'


class PlatformType(Enum):
    PC = b'\x00\x00PC'
    IOS = b'\x00iOS'
    ANDROID = b'\x00and'


class PackType(Enum):
    ZSTD_OBFS_NOCHECK = 0x10
    PLAIN = 0x20
    ZSTD_OBFS = 0x30


class ConstructError(Exception):
    pass


class UnpackError(ConstructError):
    pass


class PackError(ConstructError):
    pass


class BinContainerInfo(t.NamedTuple):
    """Сводка о контейнере"""

    unpacked_size: int
    """Размер неупакованного образа"""

    packed_size: t.Optional[int]
    """Размер упакованного образа. None для PackType.PLAIN"""

    hash: t.Optional[bytes]
    """MD5 хэш распакованного образа. None для PackType.ZSTD_OBFS_NOCHECK"""

    version: t.Optional[t.Tuple[int, int, int, int]]
    """Версия контейнера. None для HeaderType.VRFS"""

    platform: PlatformType
    """Целевая платформа"""


class UnpackResult(t.NamedTuple):
    """Результат распаковки."""

    ostream: t.BinaryIO
    """Выходной поток образа"""

    info: BinContainerInfo
    """Сводка о контейнере"""


def not_implemented(obj: t.Any, context: ct.Container) -> t.NoReturn:
    raise NotImplementedError


VersionCon = ct.ExprSymmetricAdapter(ct.Byte[4],
                                     lambda obj, ctx: tuple(reversed(obj)))


def enum(subcon: ct.Subconstruct, enum_: t.Type[Enum]):
    return ct.ExprAdapter(ct.Enum(subcon, enum_),
                          lambda obj, ctx: enum_[obj],
                          lambda obj, ctx: obj.name)


HeaderTypeCon = enum(ct.Bytes(4), HeaderType)
PlatformTypeCon = enum(ct.Bytes(4), PlatformType)
PackTypeCon = enum(ct.BitsInteger(6), PackType)

BinExtHeader = ct.Struct(
    'size' / ct.Rebuild(ct.Int16ul, lambda ctx: sum(map(lambda sc: sc.sizeof(), BinExtHeader.subcons))),
    'flags' / ct.Int16ul,
    'version' / VersionCon,
)

BinHeader = ct.Struct(
    'type' / HeaderTypeCon,
    'platform' / PlatformTypeCon,
    'size' / ct.Int32ul,

    'packed' / ct.ByteSwapped(ct.BitStruct(
        'type' / PackTypeCon,
        'size' / ct.BitsInteger(26),
    )),
)

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
    Декомпрессия сжатого образа

    :param istream: входной поток сжатого образа
    :return: выходной поток несжатого образа
    """

    dctx = zstd.ZstdDecompressor()
    return dctx.stream_reader(istream)


def compress(istream: t.BinaryIO) -> t.BinaryIO:
    """
    Сжатие образа

    :param istream: входной поток несжатого образа
    :return: выходной поток сжатого образа
    """

    raise NotImplementedError


def inplace_xor(buffer: bytearray, from_: int, sz: int, key: t.Iterable[int]) -> None:
    it = iter(key)
    for i in range(from_, from_ + sz):
        buffer[i] ^= next(it)


obfs_ks: t.Sequence[bytes] = [bytes.fromhex(s) for s in ('55aa55aa', '0ff00ff0', '55aa55aa', '48124812')]


# todo: перестроить как ленивый FileReader
def deobfuscate(istream: t.BinaryIO, sz: int) -> t.BinaryIO:
    """
    Восстановление заголовка и окончания

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


def obfuscate(istream: t.BinaryIO, sz: int) -> t.BinaryIO:
    """
    Сокрытие заголовка и окончания

    :param istream: входной поток сжатого образа с измененными частями
    :param sz: размер сжатого образа
    :return: выходной поток сжатого образа
    """

    return deobfuscate(istream, sz)


def unpack(istream: t.BinaryIO) -> UnpackResult:
    """
    Распаковка образа из bin контейнера: image.bin -> image

    :param istream: входной поток контейнера
    :return: результат распаковки
    """

    try:
        bin_container = BinContainer.parse_stream(istream)
    except ct.ConstructError as e:
        raise UnpackError(e)
    else:
        pack_type: PackType = bin_container.header.packed.type

        if pack_type not in (PackType.PLAIN, PackType.ZSTD_OBFS, pack_type.ZSTD_OBFS_NOCHECK):
            raise UnpackError("Unknown pack_type: {}".format(pack_type))

        offset = bin_container.offset
        size = bin_container.header.size
        platform = bin_container.header.platform

        header_type: HeaderType = bin_container.header.type
        version = None if header_type is HeaderType.VRFS else bin_container.ext_header.version
        packed_size = None if pack_type is PackType.PLAIN else bin_container.header.packed.size
        hash_ = None if pack_type is PackType.ZSTD_OBFS_NOCHECK else bin_container.hash
        ostream = (RangedReader(istream, offset, offset+size)
                   if pack_type is PackType.PLAIN
                   else decompress(deobfuscate(RangedReader(istream, offset, offset+packed_size), packed_size)))

        return UnpackResult(
            ostream=ostream,
            info=BinContainerInfo(
                unpacked_size=size,
                packed_size=packed_size,
                hash=hash_,
                version=version,
                platform=platform
            )
        )


def pack(istream: t.BinaryIO,
         type: HeaderType, platform: PlatformType, compress: bool, check: bool) -> t.BinaryIO:
    """
    Упаковка образа в bin контейнер: image -> image.bin

    :param istream: входной поток образа
    :param type: тип заголовка
    :param platform: целевая платформа
    :param compress: сжимать ли образ
    :param check: есть ли контрольная сумма
    :return: выходной поток контейнера
    """

    raise NotImplementedError
