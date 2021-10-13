from enum import Enum
import typing as t
import construct as ct

T = t.TypeVar('T')
VT = t.Union[T, t.Callable[[ct.Container], T]]


def getvalue(val: VT[T], context: ct.Container) -> T:
    return val(context) if callable(val) else val


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
    """Результат распаковки контейнера."""

    stream: t.BinaryIO
    """Поток образа."""

    info: BinContainerInfo
    """Сводка о контейнере."""


def not_implemented(obj: t.Any, context: ct.Container) -> t.NoReturn:
    raise NotImplementedError


VersionCon = ct.ExprSymmetricAdapter(ct.Byte[4],
                                     lambda obj, ctx: tuple(reversed(obj)))


class enum(ct.Adapter):
    def __init__(self, subcon: ct.Subconstruct, enum_: t.Type[Enum]):
        self.enum = enum_
        super().__init__(ct.Enum(subcon, enum_))

    def _decode(self, obj: str, context: ct.Container, path: str) -> Enum:
        try:
            return self.enum[obj]
        except KeyError:
            raise ct.MappingError("Неизвестное имя для {}: {}".format(self.enum.__name__, obj))

    def _encode(self, obj: Enum, context: ct.Container, path: str) -> t.Any:
        try:
            return obj.name
        except AttributeError:
            raise ct.MappingError("Объект не содержит атрибута name: {}".format(type(obj)))


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
