from hashlib import md5
from io import BytesIO, IOBase, SEEK_CUR, SEEK_END, SEEK_SET
import os
from pathlib import Path
from typing import BinaryIO, Optional, Tuple, Union
from zstandard import ZstdCompressor, ZstdDecompressor
import construct as ct
from .common import BinExtHeader, BinHeader, HeaderType, PackType, PlatformType
from .error import BinPackError, BinUnpackError
from vromfs.common import file_apply
from vromfs.ranged_reader import RangedReader
from vromfs.obfs_reader import ObfsReader

__all__ = [
    'BinContainer',
    'BinFile',
    'Version',
]


BinContainer = ct.Struct(
    'header' / BinHeader,
    'ext_header' / ct.If(lambda ctx: ctx.header.type is HeaderType.VRFX, BinExtHeader),
    'offset' / ct.Tell,
    ct.Seek(lambda ctx: ctx.header.size if ctx.header.packed.type is PackType.PLAIN else ctx.header.packed.size,
            SEEK_CUR),
    'digest' / ct.If(lambda ctx: ctx.header.packed.type is not PackType.ZSTD_OBFS_NOCHECK, ct.Bytes(16)),
    'extra' / ct.GreedyBytes,
    ct.Check(lambda ctx: len(ctx.extra) in (0, 0x100)),
)

Version = Tuple[int, int, int, int]


class BinFile(IOBase):
    """
    Класс для работы с bin контейнером.
    """

    def __init__(self, source: Union[os.PathLike, IOBase]):
        """
        :param source: Входной файл или путь к файлу контейнера.
        :raises TypeError: Неверный тип source.
        :raises EnvironmentError: Ошибка доступа к source.
        """

        if isinstance(source, os.PathLike):
            self._bin_stream = open(source, 'rb')
            self._owner = True
            self._name = os.fspath(source)
        elif isinstance(source, IOBase) and source.readable():
            self._bin_stream = source
            self._owner = False
            maybe_name = getattr(source, 'name', None)
            if isinstance(maybe_name, str):
                self._name = maybe_name
            else:
                self._name = None
        else:
            raise TypeError('source: ожидалось PathLike | Binary Reader: {}'.format(type(source)))

        self._stream = None
        self._meta = None

    @property
    def name(self) -> Optional[str]:
        """
        Имя файла. None, если объект на основе потока.
        """

        return self._name

    @property
    def meta(self):
        """
        Вспомогательное пространство имен метаданных контейнера.

        :raises BinUnpackError: Ошибка при построении пространства имен.
        """

        if self._meta is None:
            try:
                self._meta = BinContainer.parse_stream(self._bin_stream)
            except ct.ConstructError as e:
                raise BinUnpackError('Ошибка при построении метаданных контейнера.') from e

        return self._meta

    @property
    def size(self) -> int:
        """
        Размер распакованного содержимого.

        :raises BinUnpackError: Ошибка при построении пространства имен.
        """

        return self.meta.header.size

    @property
    def pack_type(self) -> PackType:
        """
        Тип упаковки контейнера.

        :raises BinUnpackError: Ошибка при построении пространства имен.
        """

        return self.meta.header.packed.type

    @property
    def platform(self) -> PlatformType:
        """
        Целевая платформа контейнера.

        :raises BinUnpackError: Ошибка при построении пространства имен.
        """

        return self.meta.header.platform

    @property
    def compressed(self) -> bool:
        """
        Сжато ли содержимое контейнера?

        :raises BinUnpackError: Ошибка при построении пространства имен.
        """

        return self.pack_type != PackType.PLAIN

    @property
    def checked(self) -> bool:
        """Содержит ли контейнер MD5 дайджест распакованного содержимого?

        :raises BinUnpackError: Ошибка при построении пространства имен.
        """

        return self.pack_type != PackType.ZSTD_OBFS_NOCHECK

    @property
    def digest(self) -> Optional[bytes]:
        """
        MD5 дайджест содержимого контейнера. None, если метаданные не содержат дайджеста.

        :raises BinUnpackError: Ошибка при построении пространства имен.
        """

        return self.meta.digest

    @property
    def version(self) -> Optional[Version]:
        """
        Версия файла. None, если версия отсутствует в заголовке.

        :raises BinUnpackError: Ошибка при построении пространства имен.
        """

        return None if self.meta.header.type is HeaderType.VRFS else self.meta.ext_header.version

    @property
    def stream(self) -> BinaryIO:
        """
        Поток содержимого контейнера.

        :raises BinUnpackError: Ошибка при построении пространства имен.
        """

        if self._stream is None:
            if self.compressed:
                self._set_compressed_stream()
            else:
                self._set_not_compressed_stream()

        return self._stream

    def _set_not_compressed_stream(self):
        offset = self.meta.offset
        size = self.meta.header.size
        self._stream = RangedReader(self._bin_stream, offset, size)

    def _set_compressed_stream(self):
        offset = self.meta.offset
        size = self.meta.header.packed.size
        obfs_reader = ObfsReader(RangedReader(self._bin_stream, offset, size), size)
        dctx = ZstdDecompressor()
        self._stream = dctx.stream_reader(obfs_reader)

    def close(self):
        if self._owner:
            self._bin_stream.close()
        super().close()

    def readable(self) -> bool:
        return True

    def seek(self, target: int, whence: int = SEEK_SET) -> int:
        """
        Смена позиции в потоке содержимого контейнера.
        Для контейнера со сжатием передвижение назад повлечет сброс потока содержимого.

        :raises ValueError: Позиция задана относительно конца файла.
        """

        if self.compressed:
            pos = self.stream.tell()
            if whence == SEEK_SET and target < pos:
                self._set_compressed_stream()
            elif whence == SEEK_CUR and target < 0:
                self._set_compressed_stream()
            elif whence == SEEK_END:
                raise ValueError('Offsets relative to the end of stream are not allowed.')

        return self.stream.seek(target, whence)

    def read(self, size: int = -1) -> bytes:
        return self.stream.read(size)

    def tell(self) -> int:
        return self.stream.tell()

    def check(self) -> Optional[bool]:
        """Проверка содержимого по MD5 дайджесту в контейнере.

        :returns: Результат проверки. Bool для контейнера с MD5 дайджестом, иначе None.
        :raises BinUnpackError: Ошибка при построении пространства имен.
        :raises ct.ConstructError: Ошибка при чтении.
        """

        if self.checked:
            m = md5()
            self.seek(0)
            file_apply(self, m.update, self.size)
            return m.digest() == self.digest

        return None

    def unpack_into(self, ostream: Optional[IOBase] = None) -> IOBase:
        """
        **Для подготовки тестовых данных.**

        Распаковка содержимого в двоичный поток, открытый для записи.
        Ostream будет создан в памяти, если не указан.

        :param ostream: Выходной поток.
        :return: Выходной поток.
        :raises TypeError: Неверный тип ostream.
        :raises BinUnpackError: Ошибка при построении пространства имен.
        :raises ct.ConstructError: Ошибка при чтении.
        :raises EnvironmentError: Ошибка при записи.
        """

        if ostream is None:
            ostream = BytesIO()
        elif not isinstance(ostream, IOBase) or not ostream.writable():
            raise TypeError('ostream: ожидалось None | Binary Writer: {}'.format(type(ostream)))

        self.seek(0)
        file_apply(self, ostream.write, self.size)

        return ostream

    def unpack(self, target: os.PathLike):
        """
        **Для подготовки тестовых данных.**

        Распаковка содержимого в файл, заданный путем target.
        В случае ошибки распаковки частичный результат доступен как ``target~``.

        :param target: Путь выходного файла..
        :raises TypeError: Неверный тип target.
        :raises BinUnpackError: Ошибка при построении пространства имен.
        :raises EnvironmentError: Ошибка при создании временного файла target~. Ошибка при записи.
        :raises ct.ConstructError: Ошибка при чтении.
        """

        if isinstance(target, Path):
            pass
        elif isinstance(target, os.PathLike):
            target = Path(target)
        else:
            raise TypeError('Ожидалось None | PathLike: {}'.format(type(target)))

        tmp = target.with_name(target.name + '~')
        with open(tmp, 'wb') as ostream:
            try:
                self.unpack_into(ostream)
                tmp.replace(target)
            except Exception:
                raise

    @classmethod
    def pack_into(cls, istream: IOBase, ostream: Optional[IOBase],
                  platform: PlatformType, version: Optional[Version], compressed: bool, checked: bool,
                  size: int, extra: Optional[bytes] = None) -> IOBase:
        """
        **Для подготовки тестовых данных.**

        Упаковка потока содержимого двоичного istream, открытого для чтения в двоичный поток ostream,
        окрытый для записи.
        Ostream будет создан в памяти, если задан как None.

        :param istream: Входной поток.
        :param ostream: Выходной поток
        :param platform: Тип платформы.
        :param version: Версия файла.
        :param compressed: Содержимое сжимается.
        :param checked: Содержимое доступно для проверки.
        :param size: Размер содержимого.
        :param extra: Дополнительные данные.
        :return: Выходной поток.
        :raises TypeError: Неверный тип istream, ostream, platform, version, size, extra. Не compressed и не checked.
        :raises BinPackError: Ошибка при записи.
        """

        if not (isinstance(istream, IOBase) or not istream.readable()):
            raise TypeError('Ожидался Binary Reader: {}'.format(type(istream)))

        if ostream is None:
            ostream = BytesIO()
        elif not (isinstance(ostream, IOBase) or not ostream.writable()):
            raise TypeError('ostream: ожидалось None | Binary Writer: {}'.format(type(ostream)))

        if not isinstance(platform, PlatformType):
            raise TypeError('platform: ожидался PlatformType: {}'.format(type(platform)))

        if version is not None:
            if not isinstance(version, tuple):
                raise TypeError('version: ожидался tuple: {}'.format(type(version)))
            size_ = len(version)
            if size_ != 4:
                raise TypeError('version: ожидалась последовательность длины 4: {}'.format(size_))
            for x in version:
                if not isinstance(x, int):
                    raise TypeError('version element: ожидался int: {}'.format(type(x)))

        if not isinstance(size, int):
            raise TypeError('size: ожидался int: {}'.format(type(size)))
        if size < 0:
            raise TypeError('size: ожидалось положительное: {}'.format(size))

        if extra is not None:
            if not isinstance(extra, bytes):
                raise TypeError('extra: ожидался bytes: {}'.format(type(extra)))
            size_ = len(extra)
            if len(extra) != 0x100:
                raise TypeError('extra: ожидалась последовательность длины 0x100: {}'.format(size_))

        if not compressed and not checked:
            raise TypeError('compress, check: не определен тип упаковки для compress == check == False')

        packed_size = 0
        image = BytesIO()
        if compressed:
            cctx = ZstdCompressor()
            with cctx.stream_writer(image, closefd=False) as compressed_writer:
                if checked:
                    packed_type = PackType.ZSTD_OBFS
                    m = md5()
                    try:
                        file_apply(istream, lambda c: (m.update(c) or ct.stream_write(compressed_writer, c)), size)
                    except ct.ConstructError as e:
                        raise BinPackError('Ошибка при формировании сжатого образа.') from e
                    digest = m.digest()
                else:
                    packed_type = PackType.ZSTD_OBFS_NOCHECK
                    try:
                        file_apply(istream, lambda c: ct.stream_write(compressed_writer, c), size)
                    except ct.ConstructError as e:
                        raise BinPackError('Ошибка при формировании сжатого образа.') from e
                    digest = None
            packed_size = len(image.getvalue())
            image.seek(0)
            image = ObfsReader(image, packed_size)
        else:
            if checked:
                try:
                    packed_type = PackType.PLAIN
                    m = md5()
                    file_apply(istream, m.update, size)
                    digest = m.digest()
                except ct.ConstructError as e:
                    raise BinPackError('Ошибка при формировании сжатого образа.') from e
            else:
                raise BinPackError('Не определен тип упаковки для compress == check == False')
            image = istream
        try:
            header_type = HeaderType.VRFS if version is None else HeaderType.VRFX
            bin_header = dict(
                type=header_type,
                platform=platform,
                size=size,
                packed=dict(
                    type=packed_type,
                    size=packed_size,
                )
            )
            BinHeader.build_stream(bin_header, ostream)
            if header_type is HeaderType.VRFX:
                BinExtHeader.build_stream(dict(flags=0, version=version), ostream)
        except ct.ConstructError as e:
            raise BinPackError('Ошибка при записи метаданных образа.') from e

        image.seek(0)
        try:
            size_ = packed_size if compressed else size
            file_apply(image, lambda c: ct.stream_write(ostream, c), size_)
        except ct.ConstructError as e:
            raise BinPackError('Ошибка при записи образа.') from e

        if checked:
            try:
                ct.Bytes(16).build_stream(digest, ostream)
            except ct.ConstructError as e:
                raise BinPackError('Ошибка при записи дайджеста.') from e

        if extra:
            try:
                ct.stream_write(ostream, extra)
            except ct.ConstructError as e:
                raise BinPackError('Ошибка при записи дополнительных данных.') from e

        return ostream

    @classmethod
    def pack(cls, source: os.PathLike, target: os.PathLike,
             platform: PlatformType, version: Optional[Tuple[int, int, int, int]],
             compressed: bool, checked: bool, extra: Optional[bytes] = None):
        """
        **Для подготовки тестовых данных.**

        Упаковка содержимого, заданного путем source, в контейнер, заданный путем target.

        :param source: Входной файл.
        :param target: Выходной файл.
        :param platform: Тип платформы.
        :param version: Версия файла.
        :param compressed: Содержимое сжимается.
        :param checked: Содержимое доступно для проверки.
        :param extra: Дополнительные данные.
        :raises TypeError: Неверный тип source, target, platform, version, size, extra. compress == check == False
        :raises BinPackError: Ошибка при записи.
        :raises EnvironmentError: Ошибка при окрытии source. Ошибка при окрытии target.
        """

        if not isinstance(source, os.PathLike):
            raise TypeError('source: ожидался PathLike: {}'.format(type(source)))
        if not isinstance(target, os.PathLike):
            raise TypeError('target: ожидался PathLike: {}'.format(type(target)))

        with open(source, 'rb') as istream, open(target, 'wb') as ostream:
            size = os.fstat(istream.fileno()).st_size
            cls.pack_into(istream, ostream, platform, version, compressed, checked, size, extra)
