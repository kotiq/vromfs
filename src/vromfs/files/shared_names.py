import io
from collections import OrderedDict
from pathlib import Path
import typing as t
import construct as ct
from construct import len_, this
import zstandard as zstd
from blk.types import Name, Str
from vromfs.parser import getvalue, VT
from blk.binary.constructor import Names
from .errors import *


def not_implemented(obj: t.Any, context: ct.Container) -> t.NoReturn:
    raise NotImplementedError


MAX_OUTPUT_SIZE = 5 * 2 ** 20
NO_DICT = '00' * 32


class ZstdCompressed(ct.Tunnel):
    def __init__(self, subcon,
                 dctx: VT[zstd.ZstdDecompressor], cctx: VT[zstd.ZstdCompressor], max_output_size: VT[int]):
        super().__init__(subcon)
        self.dctx = dctx
        self.cctx = cctx
        self.max_output_size = max_output_size

    def _decode(self, data: bytes, context: ct.Container, path: str):
        dctx = getvalue(self.dctx, context)
        max_output_size = getvalue(self.max_output_size, context)
        return dctx.decompress(data, max_output_size=max_output_size)

    def _encode(self, data: bytes, context: ct.Container, path: str) -> bytes:
        cctx = getvalue(self.cctx, context)
        return cctx.compress(data)


NameLike = t.Union[Name, Str]


class InvNamesMap(OrderedDict):
    """Отображение Name => int"""

    def append(self, name: NameLike):
        if name not in self:
            self[name] = len(self)

    def extend(self, names: t.Iterable[NameLike]):
        for name in names:
            self.append(name)

    @classmethod
    def of(cls, names: t.Iterable[NameLike]):
        inst = InvNamesMap()
        inst.extend(names)
        return inst


class DictPath(ct.Adapter):
    def _decode(self, obj: bytes, context: ct.Container, path: Path) -> t.Optional[Path]:
        stem = obj.hex()
        return None if stem == NO_DICT else Path(f'{stem}.dict')

    def _encode(self, obj: t.Optional[Path], context: ct.Container, path: Path) -> bytes:
        if obj is None:
            stem = NO_DICT
        else:
            stem = obj.stem
        return bytes.fromhex(stem)


CompressedSharedNames = ct.FocusedSeq(
    'names_bs',
    'hash' / ct.Rebuild(ct.Int64ul, 0x6873616868736168),  # как формируется хеш?
    'dict_path' / ct.Rebuild(DictPath(ct.Bytes(32)), this._.dict_path),  # как формируется хеш?
    'names_bs' / ZstdCompressed(ct.GreedyBytes, this._.dctx, this._.cctx, MAX_OUTPUT_SIZE),
)


def decompress_shared_names(istream: t.BinaryIO, dctx: zstd.ZstdDecompressor) -> bytes:
    try:
        return CompressedSharedNames.parse_stream(istream, dctx=dctx)
    except (ct.ConstructError, zstd.ZstdError) as e:
        raise ComposeError(str(e))


def compress_shared_names(names_bs: bytes, ostream: t.BinaryIO,
                          cctx: zstd.ZstdCompressor, dict_path: t.Optional[Path]):
    try:
        CompressedSharedNames.build_stream(names_bs, ostream, cctx=cctx, dict_path=dict_path)
    except (ct.ConstructError, zstd.ZstdError) as e:
        raise SerializeError(str(e))


def compose_shared_names(istream: t.BinaryIO, dctx: zstd.ZstdDecompressor) -> InvNamesMap:
    try:
        shared_names_bs = CompressedSharedNames.parse_stream(istream, dctx=dctx)
        names = Names.parse(shared_names_bs)
        return InvNamesMap.of(names)
    except (TypeError, ValueError, ct.ConstructError, zstd.ZstdError) as e:
        raise ComposeError(str(e))


def serialize_shared_names(inv_names_map: InvNamesMap, ostream: t.BinaryIO,
                           cctx: zstd.ZstdCompressor, dict_path: t.Optional[Path]):
    try:
        shared_names_bs = Names.build(inv_names_map)
        CompressedSharedNames.build_stream(shared_names_bs, ostream, cctx=cctx, dict_path=dict_path)
    except (TypeError, ValueError, ct.ConstructError, zstd.ZstdError) as e:
        raise SerializeError(str(e))
