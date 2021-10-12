import hashlib
import io
import itertools as itt
from pathlib import Path
import typing as t
import construct as ct
from construct import this
from .common import Name, getvalue, VT
from .error import VromfsUnpackError, VromfsPackError


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
    'names_info' / ct.Aligned(16, ct.Int64ul[this.names_header.count]),
    'names_data' / ct.Aligned(16, Name[this.names_header.count]),
    'data_info' / ct.Aligned(16, ct.Aligned(16, ct.Struct(
        'offset' / ct.Int32ul,
        'size' / ct.Int32ul,
    ))[this.data_header.count]),
    'hashes_data' / ct.If(lambda ctx: ctx.hashes_header and ctx.hashes_header.begin,
                          ct.Aligned(16, ct.Bytes(20)[this.data_header.count])),
    'data' / ct.Array(this.data_header.count, ct.Aligned(16, ct.Bytes(lambda ctx: ctx.data_info[ctx._index]['size']))),
)


class File(t.NamedTuple):
    path: Path
    data: bytes
    hash: t.Optional[bytes]


def unpack(istream: t.BinaryIO) -> t.Sequence[File]:
    """
    Распаковка образа.

    :param istream: входной поток образа
    :return: записи файлов
    """

    try:
        image = Image.parse_stream(istream)
        paths = image.names_data
        contents = image.data
        hashes = image.hashes_data if image.hashes_data else itt.repeat(None)
        return [File(p, d, h) for p, d, h in zip(paths, contents, hashes)]
    except ct.ConstructError as e:
        raise VromfsUnpackError from e


def pack(path: Path, ostream: t.BinaryIO, add_header: bool = False, check: bool = False) -> None:
    """
    Упаковка содержимого директории в образ.

    :param path: входная директория
    :param ostream: выходной поток образа
    :param add_header: добавить заголовок дайджестов
    :param check: добавить дайджесты для файлов
    """

    if check and not add_header:
        raise VromfsPackError('Наличие дайджестов предполагает дополнительный заголовок: add_header={}, check={}'
                              .format(add_header, check))

    rpaths = list(map(lambda p: p.relative_to(path), filter(Path.is_file, path.rglob('*'))))
    if not rpaths:
        return   # log: no paths to process
    rpaths.sort()

    count = len(rpaths)
    try:
        nm_i = rpaths.index(Path('nm'))
    except ValueError:
        pass
    else:
        if nm_i != count - 1:
            nm_path = rpaths.pop(nm_i)
            rpaths.append(nm_path)

    try:
        # names_header_offset = 0
        names_info_offset = 0x30 if add_header else 0x20
        names_header_con = ct.Aligned(16, ct.Struct(
            'offset' / ct.Int32ul,
            'count' / ct.Int32ul,
        ))
        names_header_con.build_stream(dict(offset=names_info_offset, count=count), ostream)

        data_header_offset = 0x10
        if add_header:
            hashes_header_offset = 0x20

        names_info_con = ct.Aligned(16, ct.Int64ul[count])
        names_data_offset = names_info_offset + names_info_con.sizeof()

        ct.stream_seek(ostream, names_data_offset)
        offsets = []
        for rp in rpaths:
            offsets.append(ct.stream_tell(ostream))
            Name.build_stream(rp, ostream)
        pad = -ct.stream_tell(ostream) % 16
        ct.stream_seek(ostream, pad, io.SEEK_CUR)
        data_info_offset = ct.stream_tell(ostream)

        ct.stream_seek(ostream, data_header_offset)
        data_header_con = ct.Aligned(16, ct.Struct(
            'offset' / ct.Int32ul,
            'count' / ct.Int32ul,
            ))
        data_header_con.build_stream(dict(offset=data_info_offset, count=count), ostream)

        ct.stream_seek(ostream, names_info_offset)
        names_info_con.build_stream(offsets, ostream)

        data_info_con = ct.Aligned(16, ct.Aligned(16, ct.Struct(
            'offset' / ct.Int32ul,
            'size' / ct.Int32ul,
        ))[count])
        if check:
            hash_size = 20
            hashes_data_con = ct.Aligned(16, ct.Bytes(hash_size)[count])
            hashes_data_offset = data_info_offset + data_info_con.sizeof()
            data_offset = hashes_data_offset + hashes_data_con.sizeof()
            hashes_data = []
        else:
            data_offset = data_info_offset + data_info_con.sizeof()

        ct.stream_seek(ostream, data_offset)
        data_info = []

        for rp in rpaths:
            p = path / rp
            size = p.stat().st_size
            data_info.append(dict(offset=ct.stream_tell(ostream), size=size))
            bs = p.read_bytes()
            if check:
                hashes_data.append(hashlib.sha1(bs).digest())
            datum_con = ct.Aligned(16, ct.Bytes(size))
            datum_con.build_stream(bs, ostream)

        ct.stream_seek(ostream, data_info_offset)
        data_info_con.build_stream(data_info, ostream)

        if check:
            ct.stream_seek(ostream, hashes_data_offset)
            hashes_data_con.build_stream(hashes_data, ostream)

        if add_header:
            (begin, end) = (hashes_data_offset, hashes_data_offset + hash_size*count) if check else (0, data_offset)
            ct.stream_seek(ostream, hashes_header_offset)
            hashes_header_con = ct.Aligned(16, ct.Struct(
                'end' / ct.Int64ul,
                'begin' / ct.Int16ul,
            ))
            hashes_header_con.build_stream(dict(end=end, begin=begin), ostream)
        ct.stream_seek(ostream, 0, io.SEEK_END)
    except ct.ConstructError as e:
        raise VromfsPackError from e
