import hashlib
import io
from enum import Enum
from pathlib import Path
import typing as t
import construct as ct
import zstandard as zstd
from construct import this


class HeaderType(Enum):
    VRFS = b'VRFs'
    VRFX = b'VRFx'


class PlatformType(Enum):
    PC = b'\x00\x00PC'
    IOS = b'\x00iOS'
    ANDROID = b'\x00and'


# todo: разложить на флаги check, compress
class PackType(Enum):
    ZSTD_OBFS_NOCHECK = 0x10
    """check: 0, compress: 1"""

    PLAIN = 0x20
    """check: 1, compress: 0"""

    ZSTD_OBFS = 0x30
    """check: 1, compress: 1"""


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