import io
from pathlib import Path
import typing as t
import construct as ct
from construct import this
import zstandard as zstd
from vromfs.parser import getvalue, VT


def not_implemented(obj: t.Any, context: ct.Container) -> t.NoReturn:
    raise NotImplementedError


# todo: передавать контексты
class ZstdCompressed(ct.Tunnel):
    def __init__(self, subcon,
                 max_output_size: VT[int] = 0,
                 dict_data: VT[t.Optional[zstd.ZstdCompressionDict]] = None,
                 level: VT[int] = 3, ):
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


SharedNames = ct.Struct(
    'hash' / ct.Rebuild(ct.Int64ul, 0x3f3f3f3f3f3f3f3f),  # как формируется хеш?
    'dict_stem' / ct.ExprAdapter(
        ct.Bytes(32),
        lambda o, _: o.hex(),
        lambda o, _: bytes.fromhex(o)),
    'names' / ZstdCompressed(
            ct.GreedyBytes,
            dict_data=lambda ctx: zstd.ZstdCompressionDict(
                b'' if ctx.dict_stem == NO_DICT else ctx._.fs.bytes(Path(f'{ctx.dict_stem}.dict'))
            ),
        ),
    )


class FS:
    def bytes(self, path: Path) -> bytes:
        raise NotImplementedError


MAX_OUTPUT_SIZE = 5*2**20
NO_DICT = '00' * 32


def decompress_shared_names(istream: io.BufferedIOBase, fs: FS):
    ns = SharedNames.parse_stream(istream, fs=fs)
    return ns.names
