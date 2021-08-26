import io
import os
import hashlib
import typing as t
import typing_extensions as te
from pathlib import Path
import zstandard
import construct as ct  # type: ignore
from construct import this
from .reader import RangedReader

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


def not_implemented(obj, ctx) -> t.NoReturn:
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


class ZstdCompressed(ct.Adapter):
    def __init__(self, subcon, max_output_size: VT[int]):
        super().__init__(subcon)
        self.max_output_size = max_output_size

    def _decode(self, obj: bytes, context, path) -> bytes:
        max_output_size = getvalue(self.max_output_size, context)
        return zstandard.decompress(obj, max_output_size)


def inplace_xor(buffer: bytearray, from_: int, sz: int, key: t.Iterable[int]):
    it = iter(key)
    for i in range(from_, from_ + sz):
        buffer[i] ^= next(it)


class Obfuscated(ct.Adapter):
    ks = [bytes.fromhex(s) for s in ('55aa55aa', '0ff00ff0', '55aa55aa', '48124812')]

    def _decode(self, obj: bytes, context, path):
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


class DatumInfoT(t.NamedTuple):
    offset: int
    size: int


DatumInfo = ct.ExprAdapter(ct.Int32ul[2],
                           lambda obj, ctx: DatumInfoT(*obj),
                           not_implemented)


def parse_name(offset, ctx):
    stream: io.BytesIO = ctx._io
    names = ctx.names
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


class VromfsInfoStruct(ct.Struct):
    def __init__(self, *subcons, **subconskw):
        self.names = []
        names = 'names' / ct.Computed(self.names)
        subcons_ = [names]
        subcons_.extend(subcons)
        super().__init__(*subcons_, **subconskw)

    def _parse(self, stream, context, path):
        self.names.clear()
        return super()._parse(stream, context, path)

    def _emitparse(self, code):
        raise NotImplementedError


VromfsInfo = VromfsInfoStruct(
    'names_header' / ct.Aligned(16, NamesDataHeader),
    'data_header' / ct.Aligned(16, NamesDataHeader),
    'hash_header' / ct.If(this.names_header.offset == 0x30, ct.Aligned(16, HashHeader)),

    ct.Seek(this.names_header.offset),
    'names_info' / (NameInfo * parse_name)[this.names_header.count],

    ct.Seek(this.data_header.offset),
    'data_info' / ct.Aligned(16, ct.Aligned(16, DatumInfo)[this.data_header.count]),

    ct.If(this.hash_header, ct.Seek(this.hash_header.begin_offset)),
    'hash_info' / ct.IfThenElse(
        this.hash_header,
        ct.Aligned(16, ct.Bytes(20)[this.names_header.count]),
        ct.Computed(lambda c: [None]*c.names_header.count),
    ),
)


class VromfsInfoT(te.Protocol):
    names_header: t.Sequence[int]
    data_header: t.Sequence[int]
    hash_header: t.Optional[t.Sequence[int]]
    names_info: t.Sequence[int]
    names: t.Sequence[Path]
    data_info: t.Sequence[DatumInfoT]
    hash_info: t.Sequence[t.Optional[bytes]]


class FileInfo(t.NamedTuple):
    name: Path
    offset: int
    size: int
    sha1: t.Optional[bytes]


class FilesInfoAdapter(ct.Adapter):
    def _decode(self, obj: VromfsInfoT, context, path) -> t.Sequence[FileInfo]:
        return tuple(FileInfo(name, data_offset, data_size, sha1)
                     for name, (data_offset, data_size), sha1
                     in zip(obj.names, obj.data_info, obj.hash_info))


FilesInfo = FilesInfoAdapter(VromfsInfo)


def _parse_files_info(stream, context, path) -> ct.Container:
    files_info = FilesInfo._parsereport(stream, context, path)
    return ct.Container(files_info=files_info, stream=stream)


class Vromfs(ct.Construct):
    def __init__(self, vromfs_offset: VT[int], size: VT[int]):
        super().__init__()
        self.vromfs_offset = vromfs_offset
        self.size = size

    def _parse(self, stream, context, path) -> ct.Container:
        vromfs_offset = getvalue(self.vromfs_offset, context)
        size = getvalue(self.size, context)
        vromfs_stream = RangedReader(stream, vromfs_offset, vromfs_offset + size)
        return _parse_files_info(vromfs_stream, context, path)


class VromfsWrapped(ct.Subconstruct):
    def _parse(self, stream, context, path) -> ct.Container:
        vromfs_bs = self.subcon._parsereport(stream, context, path)
        vromfs_stream = io.BytesIO(vromfs_bs)
        return _parse_files_info(vromfs_stream, context, path)


class Raise(ct.Construct):
    def __init__(self, cls: type, *args: VT[T], **kwargs: VT[T]):
        super().__init__()
        self.cls = cls
        self.args = args
        self.kwargs = kwargs

    def _parse(self, stream, context, path):
        args = [getvalue(arg, context) for arg in self.args]
        kwargs = {k: getvalue(v, context) for k, v in self.kwargs.items()}
        raise self.cls(*args, **kwargs)


class UnpackNotImplemented(Exception):
    def __str__(self):
        type_ = self.args[0]
        return 'The construct for the given packed type={:#x} is not implemented yet.'.format(type_)


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
