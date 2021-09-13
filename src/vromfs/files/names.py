import io
from collections import OrderedDict
from pathlib import Path
import typing as t
import construct as ct
from construct import len_, this
import zstandard as zstd
from blk.types import Name, Str
from vromfs.parser import getvalue, VT
from .ng_common import Names
from .errors import *


def not_implemented(obj: t.Any, context: ct.Container) -> t.NoReturn:
    raise NotImplementedError


MAX_OUTPUT_SIZE = 5 * 2 ** 20
NO_DICT = '00' * 32


# todo: передавать контексты
class ZstdCompressed(ct.Tunnel):
    def __init__(self, subcon,
                 max_output_size: VT[int] = 0,
                 dict_data: VT[t.Optional[zstd.ZstdCompressionDict]] = None,
                 level: VT[int] = 3
                 ):
        super().__init__(subcon)
        self.level = level
        self.max_output_size = max_output_size
        self.dict_data = dict_data

    def _decode(self, data, context, path):
        dict_data = getvalue(self.dict_data, context)
        dict_data = zstd.ZstdCompressionDict(b'') if dict_data is None else dict_data
        max_output_size = getvalue(self.max_output_size, context)
        dctx = zstd.ZstdDecompressor(dict_data=dict_data)
        return dctx.decompress(data, max_output_size=max_output_size)

    def _encode(self, data, context, path):
        dict_data = getvalue(self.dict_data, context)
        dict_data = zstd.ZstdCompressionDict(b'') if dict_data is None else dict_data
        level = getvalue(self.level, context)
        cctx = zstd.ZstdCompressor(level=level, dict_data=dict_data)
        return cctx.compress(data)


NameLike = t.Union[Name, Str]


class NamesMap(OrderedDict):
    """Отображение Name => int"""

    def append(self, name: NameLike):
        if name not in self:
            self[name] = len(self)

    def extend(self, names: t.Iterable[NameLike]):
        for name in names:
            self.append(name)

    @classmethod
    def of(cls, names: t.Iterable[NameLike]):
        inst = NamesMap()
        inst.extend(names)
        return inst


def create_dict(context: ct.Container) -> zstd.ZstdCompressionDict:
    dict_path = context.dict_path
    if dict_path is None:
        dict_data = b''
    else:
        fs = context._.fs
        dict_data = fs.bytes(dict_path)
        assert dict_data
    return zstd.ZstdCompressionDict(dict_data)


def get_dict_path(context: ct.Container) -> t.Optional[Path]:
    return context._.dict_path


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
    'dict_path' / ct.Rebuild(DictPath(ct.Bytes(32)), get_dict_path),
    'names_bs' / ZstdCompressed(ct.GreedyBytes, max_output_size=MAX_OUTPUT_SIZE, dict_data=create_dict),
)


class FS:
    def bytes(self, path: Path) -> bytes:
        raise NotImplementedError


def decompress_shared_names(istream: io.BufferedIOBase, fs: FS):
    try:
        return CompressedSharedNames.parse_stream(istream, fs=fs)
    except ct.ConstructError as e:
        raise ComposeError(str(e))


def compose_names(istream: io.BufferedIOBase, fs: FS) -> NamesMap:
    try:
        names_bs = CompressedSharedNames.parse_stream(istream, fs=fs)
        names = Names.parse(names_bs)
        return NamesMap.of(names)
    except (TypeError, ValueError, ct.ConstructError) as e:
        raise ComposeError(str(e))


def serialize_names(names_map: NamesMap, dict_path: t.Optional[Path], fs: FS, ostream: io.BufferedIOBase):
    try:
        names_bs = Names.build(names_map)
        CompressedSharedNames.build_stream(names_bs, ostream, dict_path=dict_path, fs=fs)
    except (TypeError, ValueError, ct.ConstructError) as e:
        raise SerializeError(str(e))
