"""Только распаковка."""

import io
import hashlib
import typing as t
from dataclasses import dataclass
from pathlib import Path
import zstandard
import construct as ct  # type: ignore
from construct import this
from .reader import RangedReader
from .typed_named_tuple import TypedNamedTuple

VRFS = b'VRFs'
VRFX = b'VRFx'

PC = b'\x00\x00PC'
IOS = b'\x00iOS'
ANDROID = b'\x00and'

ZSTD_OBFS_NOCHECK = 0x10
IDENT = 0x20
ZSTD_OBFS = 0x30


T = t.TypeVar('T')
VT = t.Union[T, t.Callable[[ct.Container], T]]


def getvalue(val: VT[T], context: ct.Container) -> T:
    return val(context) if callable(val) else val


def not_implemented(obj: t.Any, context: ct.Container) -> t.NoReturn:
    raise NotImplementedError


Version = ct.ExprAdapter(ct.Bytes(4),
                         lambda obj, ctx: tuple(reversed(obj)),
                         not_implemented)

BinExtHeader = ct.Struct(
    'ctrl' / ct.Int16ul,
    'flags' / ct.Int16ul,
    'version' / Version,
)

BinHeader = ct.Struct(
    'type' / ct.Bytes(4),
    'platform' / ct.Bytes(4),
    'size' / ct.Int32ul,

    'packed' / ct.ByteSwapped(ct.BitStruct(
        'type' / ct.BitsInteger(6),
        'size' / ct.BitsInteger(26),
    )),
)


class ZstdCompressed(ct.Adapter):  # type: ignore
    def __init__(self, subcon: ct.Construct, max_output_size: VT[int]):
        super().__init__(subcon)
        self.max_output_size = max_output_size

    def _decode(self, obj: t.ByteString, context: ct.Container, path: str) -> bytes:
        max_output_size = getvalue(self.max_output_size, context)
        return zstandard.decompress(obj, max_output_size)


def inplace_xor(buffer: bytearray, from_: int, sz: int, key: t.Iterable[int]) -> None:
    it = iter(key)
    for i in range(from_, from_ + sz):
        buffer[i] ^= next(it)


class Obfuscated(ct.Adapter):  # type: ignore
    ks: t.ClassVar[t.Sequence[bytes]] = [bytes.fromhex(s) for s in ('55aa55aa', '0ff00ff0', '55aa55aa', '48124812')]

    def _decode(self, obj: bytes, context: ct.Container, path: str) -> bytearray:
        buffer = bytearray(obj)
        size = len(obj)  # 'int26ul' mask 0x03ff_ffff
        key_sz = sum(map(len, self.ks))
        if size >= key_sz:
            pos = 0
            inplace_xor(buffer, pos, key_sz, b''.join(self.ks))
            if size >= 2 * key_sz:
                pos = (size & 0x03ff_fffc) - key_sz
                inplace_xor(buffer, pos, key_sz, b''.join(reversed(self.ks)))

        return buffer


RawCString = ct.NullTerminated(ct.GreedyBytes)

NamesDataHeader = ct.Struct(
    'offset' / ct.Int32ul,
    'count' / ct.Int32ul,
)

HashHeader = ct.Struct(
    'end_offset' / ct.Int64ul,
    'begin_offset' / ct.Int64ul,
)


NameInfo = ct.Int64ul


class DatumInfo(t.NamedTuple):
    offset: int
    size: int


DatumInfoCon = TypedNamedTuple(
    DatumInfo,
    ct.Sequence(
        'offset' / ct.Int32ul,
        'size' / ct.Int32ul,
    )
)


@dataclass
class VromfsInfoData:
    _io: t.BinaryIO
    names_header: t.Sequence[int]
    data_header: t.Sequence[int]
    hash_header: t.Optional[t.Sequence[int]]
    names_info: t.Sequence[int]
    names: t.List[Path]
    data_info: t.Sequence[DatumInfo]
    hash_info: t.Sequence[t.Optional[bytes]]


def parse_name(offset: int, context: VromfsInfoData) -> None:
    stream = context._io
    names = context.names
    pos = stream.tell()
    stream.seek(offset)
    try:
        raw_name: bytes = RawCString.parse_stream(stream)
        if raw_name.startswith(b'\xff\x3f'):
            raw_name = raw_name[2:]
        name = raw_name.decode()
        names.append(Path(name))
    finally:
        stream.seek(pos)


VromfsInfo = ct.Struct(
    'names_header' / ct.Aligned(16, NamesDataHeader),
    'data_header' / ct.Aligned(16, NamesDataHeader),
    'hash_header' / ct.If(this.names_header.offset == 0x30, ct.Aligned(16, HashHeader)),

    'names' / ct.Computed([]),
    ct.Computed(lambda c: c.names.clear()),

    ct.Seek(this.names_header.offset),
    'names_info' / (NameInfo * parse_name)[this.names_header.count],

    ct.Seek(this.data_header.offset),
    'data_info' / ct.Aligned(16, ct.Aligned(16, DatumInfoCon)[this.data_header.count]),

    ct.If(this.hash_header, ct.Seek(this.hash_header.begin_offset)),
    'hash_info' / ct.IfThenElse(
        this.hash_header,
        ct.Aligned(16, ct.Bytes(20)[this.names_header.count]),
        ct.Computed(lambda c: [None]*c.names_header.count),
    ),
)


class FileInfo(t.NamedTuple):
    path: Path
    offset: int
    size: int
    sha1: t.Optional[bytes]


class FilesInfoAdapter(ct.Adapter):  # type: ignore
    def _decode(self, obj: VromfsInfoData, context: ct.Container, path: str) -> t.Sequence[FileInfo]:
        return tuple(FileInfo(name, data_offset, data_size, sha1)
                     for name, (data_offset, data_size), sha1
                     in zip(obj.names, obj.data_info, obj.hash_info))


FilesInfo = FilesInfoAdapter(VromfsInfo)


class FilesInfoData(t.NamedTuple):
    files_info: t.Sequence[FileInfo]
    stream: t.Union[RangedReader, io.BufferedIOBase]


def _parse_files_info(stream: t.Union[RangedReader, io.BufferedIOBase],
                      context: ct.Container, path: str) -> FilesInfoData:
    files_info = FilesInfo._parsereport(stream, context, path)
    return FilesInfoData(files_info=files_info, stream=stream)


class Vromfs(ct.Construct):  # type: ignore
    def __init__(self, vromfs_offset: VT[int], size: VT[int]):
        super().__init__()
        self.vromfs_offset = vromfs_offset
        self.size = size

    def _parse(self, stream: io.BufferedIOBase, context: ct.Container, path: str) -> FilesInfoData:
        vromfs_offset = getvalue(self.vromfs_offset, context)
        size = getvalue(self.size, context)
        vromfs_stream = RangedReader(stream, vromfs_offset, vromfs_offset + size)
        return _parse_files_info(vromfs_stream, context, path)


class VromfsWrapped(ct.Subconstruct):  # type: ignore
    def _parse(self, stream: io.BufferedIOBase, context: ct.Container, path: str) -> FilesInfoData:
        vromfs_bs = self.subcon._parsereport(stream, context, path)
        vromfs_stream = io.BytesIO(vromfs_bs)
        return _parse_files_info(vromfs_stream, context, path)


class Raise(ct.Construct):  # type: ignore
    def __init__(self, cls: t.Type[Exception], *args: t.Any):
        super().__init__()
        self.cls = cls
        self.args = args

    def _parse(self, stream: t.Any, context: ct.Container, path: str) -> t.NoReturn:
        args = [getvalue(arg, context) for arg in self.args]
        raise self.cls(*args)


class UnpackNotImplemented(Exception):
    def __str__(self) -> str:
        type_ = self.args[0]
        return 'The construct for the given packed type={:#x} is not implemented yet.'.format(type_)

@dataclass
class BinContailerData:
    info: FilesInfoData
    md5: t.Optional[bytes]


BinContainer = ct.Struct(
    'header' / BinHeader,
    'ext_header' / ct.If(this.header.type == VRFX, BinExtHeader),

    'vromfs_offset' / ct.Tell,
    'info' / ct.IfThenElse(
        this.header.packed.size == 0,
        Vromfs(this.vromfs_offset, this.header.size),
        VromfsWrapped(ct.IfThenElse(this.header.packed.type in (ZSTD_OBFS, ZSTD_OBFS_NOCHECK),
                                    ZstdCompressed(Obfuscated(ct.Bytes(this.header.packed.size)), this.header.size),
                                    Raise(UnpackNotImplemented, this.header.packed.type)))),

    ct.If(this.header.packed.size == 0, ct.Seek(this.vromfs_offset + this.header.size)),
    'md5' / ct.If(this.header.packed.type != ZSTD_OBFS_NOCHECK, ct.Bytes(16)),
    'tail' / ct.GreedyBytes,
    ct.Check(lambda c: len(c.tail) in (0, 0x100)),

    ct.Computed(lambda c: c.info.stream.seek(0))
)


MaybeCompressedRawBinContainer = ct.Struct(
    'header' / BinHeader,
    'ext_header' / ct.If(this.header.type == VRFX, BinExtHeader),

    'vromfs_offset' / ct.Tell,
    'vromfs' / ct.IfThenElse(
        this.header.packed.size == 0,
        ct.Bytes(this.header.size),
        ct.IfThenElse(this.header.packed.type in (ZSTD_OBFS, ZSTD_OBFS_NOCHECK),
                      Obfuscated(ct.Bytes(this.header.packed.size)),
                      Raise(UnpackNotImplemented, this.header.packed.type)),
        ),
    'md5' / ct.If(this.header.packed.type != ZSTD_OBFS_NOCHECK, ct.Bytes(16)),
    'tail' / ct.GreedyBytes,
    ct.Check(lambda c: len(c.tail) in (0, 0x100)),
    )


RawBinContainer = ct.Struct(
    'header' / BinHeader,
    'ext_header' / ct.If(this.header.type == VRFX, BinExtHeader),

    'vromfs_offset' / ct.Tell,
    'vromfs' / ct.IfThenElse(
        this.header.packed.size == 0,
        ct.Bytes(this.header.size),
        ct.IfThenElse(this.header.packed.type in (ZSTD_OBFS, ZSTD_OBFS_NOCHECK),
                      ZstdCompressed(Obfuscated(ct.Bytes(this.header.packed.size)), this.header.size),
                      Raise(UnpackNotImplemented, this.header.packed.type)),
        ),
    'md5' / ct.If(this.header.packed.type != ZSTD_OBFS_NOCHECK,
                  ct.Checksum(ct.Bytes(16), lambda bs: hashlib.md5(bs).digest(), this.vromfs)),
    'tail' / ct.GreedyBytes,
    ct.Check(lambda c: len(c.tail) in (0, 0x100)),
    )
