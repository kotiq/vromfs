import itertools as itt
import typing as t
import construct as ct
from construct import this
from vromfs.reader import RangedReader
from .common import File, NamesData
from .error import VromfsUnpackError


Image = ct.Struct(
    'names_header' / ct.Aligned(16, ct.Struct(
        'offset' / ct.Int32ul,
        'count' / ct.Int32ul,
        )),

    'data_header' / ct.Aligned(16, ct.Struct(
        'offset' / ct.Int32ul,
        'count' / ct.Int32ul,
        )),

    'hashes_header' / ct.If(this.names_header.offset == 0x30, ct.Aligned(16, ct.Struct(
        'end' / ct.Int64ul,
        'begin' / ct.Int16ul,
        ))),

    ct.Check(lambda ctx: ctx.names_header.offset == ctx._io.tell()),
    'names_info' / ct.Aligned(16, ct.Int64ul[this.names_header.count]),
    'names_data' / ct.Aligned(16, NamesData(this.names_info)),

    ct.Check(lambda ctx: ctx.data_header.offset == ctx._io.tell()),
    'data_info' / ct.Aligned(16, ct.Aligned(16, ct.Struct(
        'offset' / ct.Int32ul,
        'size' / ct.Int32ul,
        ))[this.data_header.count]),

    ct.If(lambda ctx: ctx.hashes_header and ctx.hashes_header.begin,
          ct.Check(lambda ctx: this.hashes_header.begin == ctx._io.tell())),
    'hashes_data' / ct.If(lambda ctx: ctx.hashes_header and ctx.hashes_header.begin,
                          ct.Aligned(16, ct.Bytes(20)[this.data_header.count])),

    ct.If(lambda ctx: ctx.hashes_header and not ctx.hashes_header.begin,
          ct.Check(lambda ctx: ctx.hashes_header.end == ctx._io.tell())),
)


def unpack(istream: t.BinaryIO) -> t.Sequence[File]:
    """
    Распаковка образа.

    :param istream: входной поток образа
    :return: результат распаковки
    """

    try:
        image = Image.parse_stream(istream)
        paths = image.names_data
        hashes = image.hashes_data if image.hashes_data else itt.repeat(None)
        data_info = image.data_info
        offsets = [di['offset'] for di in data_info]
        sizes = [di['size'] for di in data_info]
        return [File(p, RangedReader(istream, o, o + s), s, h) for p, o, s, h in zip(paths, offsets, sizes, hashes)]
    except ct.ConstructError as e:
        raise VromfsUnpackError from e
