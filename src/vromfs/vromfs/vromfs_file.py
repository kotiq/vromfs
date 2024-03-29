from collections import OrderedDict
from hashlib import sha1
from io import BytesIO, IOBase, SEEK_END
from itertools import chain, repeat
import logging
import os
from pathlib import Path
from typing import (Any, BinaryIO, Iterable, Iterator, Mapping, MutableSequence, NamedTuple, Optional,
                    OrderedDict as ODict, Sequence, TextIO, Union)
import construct as ct
from construct import this
from zstandard import DICT_TYPE_AUTO, FORMAT_ZSTD1, ZstdCompressionDict, ZstdDecompressor
import blk.text as txt
import blk.json as jsn
from blk import Format, Section
from blk.binary import (BlkType, ComposeError, compose_names, compose_partial_fat_zst, compose_partial_bbf,
                        compose_partial_bbf_zlib, compose_partial_fat, compose_partial_slim, compose_partial_slim_zst)
from vromfs.common import file_apply
from vromfs.ranged_reader import RangedReader
from .common import FileInfo, NamesData
from .error import VromfsPackError, VromfsUnpackError

__all__ = [
    'Image',
    'VromfsFile',
]

logger = logging.getLogger(__name__)
Item = Union[os.PathLike, FileInfo]


class ExtractResult(NamedTuple):
    path: Path
    error: Optional[Exception]


Image = ct.Struct(
    'names_header' / ct.Aligned(16, ct.Struct(
        'offset' / ct.Int32ul,
        'count' / ct.Int32ul,
    )),

    'data_header' / ct.Aligned(16, ct.Struct(
        'offset' / ct.Int32ul,
        'count' / ct.Int32ul,
    )),

    'digests_header' / ct.If(this.names_header.offset == 0x30, ct.Aligned(16, ct.Struct(
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

    ct.If(lambda ctx: ctx.digests_header and ctx.digests_header.begin,
          ct.Check(lambda ctx: this.digests_header.begin == ctx._io.tell())),
    'digests_data' / ct.If(lambda ctx: ctx.digests_header and ctx.digests_header.begin,
                           ct.Aligned(16, ct.Bytes(20)[this.data_header.count])),

    'offset' / ct.Tell,

    ct.If(lambda ctx: ctx.digests_header and not ctx.digests_header.begin,
          ct.Check(lambda ctx: ctx.digests_header.end == ctx._io.tell())),
)


def serialize_text(root: Section, ostream: TextIO, out_format: Format, is_sorted: bool, is_minified: bool) -> None:
    if out_format is Format.STRICT_BLK:
        txt.serialize(root, ostream, dialect=txt.StrictDialect)
    elif out_format in (Format.JSON, Format.JSON_2, Format.JSON_3):
        jsn.serialize(root, ostream, out_format, is_sorted, is_minified)


def is_text(bs: Iterable[bytes]) -> bool:
    restricted = bytes.fromhex('00 01 02 03 04 05 06 07 08 0b 0c 0e 0f 10 11 12 14 13 15 16 17 18 19')
    return not any(b in restricted for b in bs)


def create_text(path: os.PathLike) -> TextIO:
    return open(path, 'w', newline='', encoding='utf8')


class VromfsFile(IOBase):
    """
    Класс для работы с VROMFS образом.
    """

    def __init__(self, source: Union[os.PathLike, IOBase]) -> None:
        """
        :param source: Входной файл или путь к файлу образа.
        :raises TypeError: Неверный тип source.
        :raises EnvironmentError: Ошибка доступа к source.
        """

        if isinstance(source, os.PathLike):
            self._vromfs_stream = open(source, 'rb')
            self._owner = True
            self._name = os.fspath(source)
        elif isinstance(source, IOBase) and source.readable():
            self._vromfs_stream = source
            self._owner = False
            maybe_name = getattr(source, 'name', None)
            if isinstance(maybe_name, str):
                self._name = maybe_name
            else:
                self._name = None
        else:
            raise TypeError('source: ожидалось PathLike | Binary Reader: {}'.format(type(source)))

        self._meta = None
        self._info_map = None
        self._nm = None
        self._dctx = None

    def close(self) -> None:
        if self._owner:
            self._vromfs_stream.close()

    @property
    def name(self) -> Optional[str]:
        """
        Имя файла. None, если объект на основе потока.
        """

        return self._name

    # todo: обернуть в пространство имен с известными членами
    @property
    def meta(self) -> Any:
        """
        Вспомогательное пространство имен метаданных образа VROMFS.

        :raises VromfsUnpackError: Ошибка чтения или построения пространства имен.
        """

        if self._meta is None:
            try:
                self._meta = Image.parse_stream(self._vromfs_stream)
            except ct.ConstructError as e:
                raise VromfsUnpackError('Ошибка при построении метаданных образа VROMFS.') from e

        return self._meta

    @property
    def checked(self) -> bool:
        """
        Содержит ли образ таблицы SHA1 дайджестов?

        :raises VromfsUnpackError: Ошибка при построении пространства имен.
        """

        meta = self.meta
        return bool(meta.digests_header and meta.digests_header.begin)

    @property
    def extended(self) -> bool:
        """
        Содержит ли образ заголовок со ссылкой на таблицу SHA1 дайджестов?

        :raises VromfsUnpackError: Ошибка при построении пространства имен.:
        """

        return self.meta.names_header.offset == 0x30

    @property
    def info_map(self) -> ODict[Path, FileInfo]:
        """
        Упорядоченное отображение ``{внутренний путь файла => метаданные файла}``
        в порядке возрастания смещений файлов.

        :raises VromfsUnpackError: Ошибка при построении пространства имен.
        """

        if self._info_map is None:
            meta = self.meta
            paths = meta.names_data
            digests = meta.digests_data if meta.digests_data else repeat(None)
            data_info = meta.data_info
            offsets = [di['offset'] for di in data_info]
            sizes = [di['size'] for di in data_info]
            infos = [FileInfo(p, o, s, d) for p, o, s, d in zip(paths, offsets, sizes, digests)]
            infos.sort(key=lambda info: info.offset)
            self._info_map = OrderedDict((info.path, info) for info in infos)

        return self._info_map

    def get_info(self, path: os.PathLike) -> FileInfo:
        """
        Метаданные файла по внутреннему пути path.

        :raises TypeError: Неверный тип path.
        :raises KeyError: Рath отсутствует в карте имен.
        :raises VromfsUnpackError: Ошибка при построении пространства имен.
        """

        if isinstance(path, Path):
            pass
        elif isinstance(path, os.PathLike):
            path = Path(path)
        else:
            raise TypeError('path: ожидалось Path | PathLike: {}'.format(type(path)))

        try:
            info = self.info_map[path]
        except KeyError:
            raise KeyError('path: нет FileInfo, содержащего путь {!r}'.format(str(path)))

        return info

    @property
    def name_list(self) -> Sequence[Path]:
        """
        Последовательность внутренних имен файлов в образе VROMFS в порядке возрастания смещений файлов.

        :raises VromfsUnpackError: Ошибка при построении пространства имен.
        """

        return tuple(self.info_map.keys())

    @property
    def info_list(self) -> Sequence[FileInfo]:
        """
        Последовательность метаданных файлов в образе VROMFS в порядке возрастания смещений файлов.

        :raises VromfsUnpackError: Ошибка при построении пространства имен.
        """

        return tuple(self.info_map.values())

    @property
    def nm(self) -> Optional[Sequence[str]]:
        """
        Общая таблица имен. None, если образ не содержит таблицы.

        :raises VromfsUnpackError: Ошибка при построении пространства имен. Ошибка при построении таблицы имен.
        """

        if self._nm is None:
            try:
                info = self.get_info(Path('nm'))
            except KeyError:
                pass
            else:
                full_stream = RangedReader(self._vromfs_stream, info.offset, info.size)
                try:
                    ns = compose_names(full_stream, self.dctx)
                    self._nm = ns.names
                    logger.debug(f'Разделяемая карта имен {ns.table_digest.hex()}')
                except ComposeError as e:
                    raise VromfsUnpackError('Ошибка при распаковке таблицы имен.') from e

        return self._nm

    @property
    def dctx(self) -> Optional[ZstdDecompressor]:
        """
        Объект декомпрессора, используемый при распаковке. None, если образ не содержит словарь.

        :raises VromfsUnpackError: Ошибка при построении пространства имен.
        :raises ct.ConstructError: Ошибка при чтении потока. Ошибка при записи потока.
        """

        if self._dctx is None:
            info = None
            for p, i in self.info_map.items():
                if p.suffix == '.dict':
                    info = i
                    break
            format_ = FORMAT_ZSTD1
            if info is None:
                self._dctx = ZstdDecompressor(format=format_)
            else:
                stream = BytesIO()
                self._unpack_info_into_raw(info, stream)
                data = stream.getvalue()
                dict_ = ZstdCompressionDict(data, dict_type=DICT_TYPE_AUTO)
                self._dctx = ZstdDecompressor(dict_data=dict_, format=format_)

        return self._dctx

    def _unpack_info_into_raw(self, info: FileInfo, ostream: BinaryIO):
        """
        Распаковка файла как есть в двоичный поток, открытый для записи.

        :param info: Объект файла в образе.
        :raises ct.ConstructError: Ошибка при чтении потока. Ошибка при записи потока.
        """

        reader = RangedReader(self._vromfs_stream, info.offset, info.size)
        file_apply(reader, lambda c: ct.stream_write(ostream, c), info.size)

    def _unpack_info_into_blk(self, info: FileInfo, ostream: TextIO,
                              out_format: Format, is_sorted: bool, is_minified: bool) -> None:
        """
        Распаковка файла с преобразованием двоичных blk в текстовый поток, открытый для записи.
        Текстовые файлы копируются как есть как есть.

        :param info: Объект файла в образе.
        :param ostream: Выходной поток.
        :param out_format: Формат выходных данных.
        :param is_sorted: Сортировать ключи для JSON.
        :param is_minified: Минифицировать JSON.
        :raises ct.ConstructError: Ошибка при чтении потока. Ошибка при записи потока.
        :raises zstd.ZstdError: Ошибка при распаковке ZSTD контейнера.
        :raises blk.ComposeError: Ошибка при формировании блока.
        :raises EnvironmentError: Ошибка при записи блока.
        """

        istream = RangedReader(self._vromfs_stream, info.offset, info.size)
        fst = istream.read(1)
        if not fst:
            logger.debug(f'{str(info.path)!r}: EMPTY')
            return
        blk_type = BlkType.from_byte(fst)
        try:
            head = b''
            if blk_type is BlkType.FAT:
                section = compose_partial_fat(istream)
            elif blk_type is BlkType.FAT_ZST:
                section = compose_partial_fat_zst(istream, self.dctx)
            elif blk_type is BlkType.SLIM:
                section = compose_partial_slim(self.nm, istream)
            elif blk_type in (BlkType.SLIM_ZST, BlkType.SLIM_ZST_DICT):
                section = compose_partial_slim_zst(self.nm, istream, self.dctx)
            elif blk_type is BlkType.BBF:
                triple = istream.read(3)
                if triple == b'BBF':
                    section = compose_partial_bbf(istream)
                elif triple == b'BBz':
                    section = compose_partial_bbf_zlib(istream)
                else:
                    section = None
                    head = fst + triple
            else:
                section = None
                head = fst

            if section is None:
                bs = istream.read()
                ostream.flush()
                if head:
                    ostream.buffer.write(head)
                ostream.buffer.write(bs)
                out_format_name = 'TEXT' if is_text(chain(head, bs)) else 'UNKNOWN'
            else:
                serialize_text(section, ostream, out_format, is_sorted, is_minified)
                out_format_name = out_format.name
            logger.debug(f'{str(info.path)!r}: {blk_type.name} => {out_format_name}')
        except Exception:
            logger.debug(f'{str(info.path)!r}: {blk_type.name}')
            raise

    def _unpack_item(self, item: Item, path: Path, out_format: Format, is_sorted: bool, is_minified: bool) -> Path:
        """
        Распаковка одного файла с заданным типом результата.
        В случае ошибки распаковки частичный результат доступен как ``target~``.

        :param item: Объект файла в образе.
        :param path: Путь выходной директории.
        :param out_format: Формат выходных данных.
        :param is_sorted: Сортировать ключи для JSON.
        :param is_minified: Минифицировать JSON.
        :return: Путь распакованного файла.
        :raises EnvironmentError: Ошибка при создании директории.
        Ошибка при инициализации выходного потока.
        Ошибка при перемещении файла.
        :raises ct.ConstructError: Ошибка при чтении потока. Ошибка при записи потока.
        :raises zstd.ZstdError: Ошибка при распаковке ZSTD контейнера.
        :raises blk.ComposeError: Ошибка при формировании блока.
        :raises EnvironmentError: Ошибка при записи блока.
        """

        if not isinstance(item, FileInfo):
            item = self.get_info(item)
        target = path / item.path
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + '~')

        if out_format is not Format.RAW and item.path.suffix == '.blk':
            with create_text(tmp) as ostream:
                try:
                    self._unpack_info_into_blk(item, ostream, out_format, is_sorted, is_minified)
                    ostream.close()
                    tmp.replace(target)
                except Exception:
                    raise
        else:
            with open(tmp, 'wb') as ostream:
                try:
                    self._unpack_info_into_raw(item, ostream)
                    logger.debug(f'{str(item.path)!r}')
                    ostream.close()
                    tmp.replace(target)
                except Exception:
                    raise

        return target

    def unpack_into(self, item: Item, ostream: Optional[IOBase] = None
                    ) -> IOBase:
        """
        Распаковка одного файла в поток как есть в двоичный поток, открытый для записи.
        Ostream будет создан в памяти, если задан как None.

        :param item: Объект файла в образе.
        :param ostream: Выходной поток.
        :raises TypeError: Неверный тип ostream.
        :raises ct.ConstructError: Ошибка при чтении потока. Ошибка при записи потока.
        :raises blk.ComposeError: Ошибка при формировании блока.
        :raises EnvironmentError: Ошибка при записи блока.
        """

        if ostream is None:
            ostream = BytesIO()
        elif not isinstance(ostream, IOBase) or not ostream.writable():
            raise TypeError('ostream: ожидалось None | Binary Writer: {}'.format(type(ostream)))

        if not isinstance(item, FileInfo):
            item = self.get_info(item)

        try:
            self._unpack_info_into_raw(item, ostream)
        except Exception as e:
            raise VromfsUnpackError('Ошибка при распаковке файла в поток как есть.') from e

        return ostream

    @staticmethod
    def _validated_path(path: Optional[os.PathLike]) -> Path:
        """
        Проверка имени директории. Текущая директория, если задана как None.

        :param path: Имя директории.
        :return: Имя директории.
        :raises TypeError: Неверный тип path.
        """

        if path is None:
            path = Path.cwd()
        elif isinstance(path, Path):
            pass
        elif isinstance(path, os.PathLike):
            path = Path(path)
        else:
            raise TypeError('path: ожидалось None | PathLike: {}'.format(type(path)))

        return path

    def _sorted_infos(self, items: Optional[Iterable[Item]], absent: Optional[MutableSequence[Path]] = None
                      ) -> Iterable[FileInfo]:
        """
        Объекты файлов в образе в порядке возрастания смещений.
        Если items задан как None, принимаются все объекты файлов в образе.

        :param items: Объекты файлов для распаковки.
        :param absent: Объекты файлов из items, отсутствующие в образе.
        :return: Объекты файлов из items, присутствующие в образе.
        :raises VromfsUnpackError: Ошибка при построении пространства имен.
        """

        if items is None:
            infos = self.info_map.values()
        else:
            infos_ = []
            for item in items:
                if isinstance(item, FileInfo):
                    item = item.path
                try:
                    info = self.get_info(item)
                except KeyError:
                    if absent is not None:
                        absent.append(item)
                else:
                    infos_.append(info)

            names_ = set(map(lambda i: i.path, infos_))
            infos = map(self.info_map.__getitem__, filter(names_.__contains__, self.info_map))

        return infos

    def unpack_iter(self, items: Optional[Iterable[Item]] = None, path: Optional[os.PathLike] = None,
                    out_format: Format = Format.RAW, is_sorted: bool = False, is_minified: bool = False
                    ) -> Iterator[ExtractResult]:
        """
        Распаковка группы файлов с заданным типом результата.
        Если path задан как None, принимается путь текущей директории.
        Если item задан как None, принимаются все объекты файлов в образе.

        :param path: Путь выходной директории.
        :param items: Объекты файлов для распаковки.
        :param out_format: Формат выходных данных.
        :param is_sorted: Сортировать ключи для JSON.
        :param is_minified: Минифицировать JSON.
        :returns: Итератор ExtractResult, результат преобразования.
        :raises VromfsUnpackError: Ошибка при построении пространства имен.
        :raises TypeError: Неверный тип path.
        :raises KeyError: Внутренний путь отсутствует в карте имен.
        """

        path = self._validated_path(path)
        absent = []
        infos = self._sorted_infos(items, absent)

        for p in absent:
            yield ExtractResult(p, KeyError('Нет FileInfo, содержащего путь {!r}'.format(str(p))))

        for info in infos:
            try:
                self._unpack_item(info, path, out_format, is_sorted, is_minified)
            except Exception as e:
                yield ExtractResult(info.path, e)
            else:
                yield ExtractResult(info.path, None)

    def unpack(self, item: Item, path: Optional[os.PathLike] = None, out_format: Format = Format.RAW
               ) -> ExtractResult:
        """
        Распаковка одного файла с заданным типом результата.
        Если path задан как None, принимается путь текущей директории.

        :param path: Путь выходной директории.
        :param item: Объект файла для распаковки.
        :param out_format: Формат выходных данных.
        :returns: ExtractResult, результат преобразования.
        :raises VromfsUnpackError: Ошибка при построении пространства имен.
        :raises TypeError: Неверный тип path.
        :raises KeyError: Внутренний путь отсутствует в карте имен.
        """

        return next(self.unpack_iter([item], path, out_format))

    def check(self) -> Optional[Sequence[Path]]:
        """
        Проверка содержимого по дайджестам из блока SHA1. Bool для образа с блоком SHA1, иначе None.

        :raises VromfsUnpackError: Ошибка при построении пространства имен.
        """

        if self.checked:
            failed = []

            for info in self.info_map.values():
                if info.digest is None:
                    return None
                else:
                    m = sha1()
                    reader = RangedReader(self._vromfs_stream, info.offset, info.size)
                    file_apply(reader, m.update, info.size)
                    if m.digest != info.digest:
                        failed.append(info.path)

            return tuple(failed)

        return None

    def digests_table(self, items: Optional[Iterable[Item]] = None,
                      absent: MutableSequence[Path] = None) -> Mapping[Path, bytes]:
        """
        Таблица ``{внутреннее имя файла => SHA1 дайджест содержимого}``.

        :raises VromfsUnpackError: Ошибка при построении пространства имен.
        :raises ct.ConstructError: Ошибка при чтении блока данных файла.
        """

        table = {}
        for info in self._sorted_infos(items, absent):
            if info.digest is None:
                m = sha1()
                reader = RangedReader(self._vromfs_stream, info.offset, info.size)
                file_apply(reader, m.update, info.size)
                digest = m.digest()
            else:
                digest = info.digest

            table[info.path] = digest

        return table

    @classmethod
    def pack_into(cls, source: os.PathLike, ostream: Optional[IOBase] = None,
                  extended: bool = False, checked: bool = False) -> IOBase:
        """
        **Для подготовки тестовых данных.**

        Упаковка дерева, заданного путем директории source в двоичный поток ostream, открытый для записи.

        :param source: Путь входной директории.
        :param ostream: Выходной поток.
        :param extended: Образ содержит заголовок с указателем на таблицу дайджестов.
        :param checked: Содержимое доступно для проверки.
        :return:
        :raises TypeError: Неверный тип source. Неверный тип ostream. Checked и не extended.
        :raises VromfsPackError: Ошибка при записи.
        """

        if not isinstance(source, os.PathLike):
            raise TypeError('root: ожидался PathLike: {}'.format(type(source)))
        if not isinstance(source, Path):
            source = Path(source)

        try:
            rpaths = list(map(lambda p: p.relative_to(source), filter(Path.is_file, source.rglob('*'))))
        except NotADirectoryError:
            raise TypeError('source: ожидалась директория.')

        if ostream is None:
            ostream = BytesIO()
        elif not (isinstance(ostream, IOBase) or not ostream.writable()):
            raise TypeError('ostream: ожидалось None | Binary Writer: {}'.format(type(ostream)))

        if checked and not extended:
            raise TypeError('Наличие дайджестов предполагает дополнительный заголовок.')

        rpaths.sort()

        count = len(rpaths)
        try:
            i = rpaths.index(Path('nm'))
        except ValueError:
            pass
        else:
            if i != count - 1:
                rpaths.append(rpaths.pop(i))

        try:
            names_info_offset = 0x30 if extended else 0x20
            names_header_con = ct.Aligned(16, ct.Struct(
                'offset' / ct.Int32ul,
                'count' / ct.Int32ul,
            ))
            names_header_con.build_stream(dict(offset=names_info_offset, count=count), ostream)

            data_header_offset = 0x10
            if extended:
                digests_header_offset = 0x20

            names_info_con = ct.Aligned(16, ct.Int64ul[count])
            names_data_offset = names_info_offset + names_info_con.sizeof()

            ct.stream_seek(ostream, names_data_offset)
            offsets = []
            names_data_con = ct.Aligned(16, NamesData(offsets))
            names_data_con.build_stream(rpaths, ostream)
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

            if checked:
                digest_size = 20
                digests_data_con = ct.Aligned(16, ct.Bytes(digest_size)[count])
                digests_data_offset = data_info_offset + data_info_con.sizeof()
                data_offset = digests_data_offset + digests_data_con.sizeof()
                digests_data = []
            else:
                data_offset = data_info_offset + data_info_con.sizeof()
        except ct.ConstructError as e:
            raise VromfsPackError('Ошибка при формировании метаданных: секция имен.') from e

        try:
            ct.stream_seek(ostream, data_offset)
            data_info = []

            for rpath in rpaths:
                path = source / rpath
                size = path.stat().st_size
                offset = ct.stream_tell(ostream)
                data_info.append(dict(offset=offset, size=size))
                with open(path, 'rb') as istream:
                    bs = ct.stream_read(istream, size)
                if checked:
                    digest = sha1(bs).digest()
                    digests_data.append(digest)
                datum_con = ct.Aligned(16, ct.Bytes(size))
                datum_con.build_stream(bs, ostream)
        except ct.ConstructError as e:
            raise VromfsPackError('Ошибка при формировании блока данных') from e

        try:
            ct.stream_seek(ostream, data_info_offset)
            data_info_con.build_stream(data_info, ostream)

            if checked:
                ct.stream_seek(ostream, digests_data_offset)
                digests_data_con.build_stream(digests_data, ostream)

            if extended:
                if checked:
                    begin, end = digests_data_offset, digests_data_offset + digest_size*count
                else:
                    begin, end = 0, data_offset
                ct.stream_seek(ostream, digests_header_offset)
                digests_header_con = ct.Aligned(16, ct.Struct(
                    'end' / ct.Int64ul,
                    'begin' / ct.Int16ul,
                ))
                digests_header_con.build_stream(dict(end=end, begin=begin), ostream)

            ct.stream_seek(ostream, 0, SEEK_END)
        except ct.ConstructError as e:
            raise VromfsPackError('Ошибка при формировании метаданных: секции адресов и дайджестов.') from e

        return ostream

    @classmethod
    def pack(cls, source: os.PathLike, target: os.PathLike,
             extended: bool = False, checked: bool = False):
        """
        **Для подготовки тестовых данных.**

        Упаковка дерева, заданного путем директории source в образ, заданный путем target.

        :param source: Путь входной директории.
        :param target: Выходной поток.
        :param extended: Образ содержит заголовок с указателем на таблицу дайджестов.
        :param checked: Содержимое доступно для проверки.
        :raises TypeError: Неверный тип source. Неверный тип target. Checked и не extended.
        :raises VromfsPackError: Ошибка при записи.
        :raises EnvironmentError: Ошибка при открытии target.
        """

        if not isinstance(target, os.PathLike):
            raise TypeError('target: ожидался PathLike: {}'.format(type(target)))

        with open(target, 'wb') as ostream:
            cls.pack_into(source, ostream, extended, checked)
