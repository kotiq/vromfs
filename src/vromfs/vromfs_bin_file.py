import io
import os
from pathlib import Path
import hashlib
import typing as t
from .parser import BinContainer, FileInfo, BinContailerData
from .reader import RangedReader

__all__ = ['CheckResult', 'VromfsBinFile']


class CheckResult(t.NamedTuple):
    status: t.Optional[bool]
    """Статус проверки: True: успех, False: неудача, None: не применимо."""

    failed: t.Optional[t.Sequence[Path]]
    """
    Список не прошедших проверку в случае неудачи для несжатого образа, иначе None.
    None для сжатого образа для любого статуса.
    """


FileItem = t.Union[str, Path, FileInfo]


class VromfsError(Exception):
    pass


class UnpackError(Exception):
    pass


class VromfsBinFile:
    """Интерфейс, подобный zipfile.ZipFile."""

    chunk_size: int = 2**20

    def __init__(self, name_or_stream: t.Union[os.PathLike, io.BufferedReader]):  # type: ignore
        """
        Первичная распаковка образа.
        Для несжатого образа файл следует держать открытым.

        :param name_or_stream: путь или открытый двоичный файл.
        :raises TypeError: name_or_stream не PathLike и не BufferedReader
        :raises UnpackError: при ошибке распаковки
        """

        if isinstance(name_or_stream, os.PathLike):
            name = os.fspath(name_or_stream)
            stream = open(name, 'rb')
        elif isinstance(name_or_stream, io.BufferedReader):
            stream = name_or_stream
        else:
            raise TypeError("Ожидалось PathLike | BufferedReader: {}".format(type(name_or_stream)))

        try:
            self.container: BinContailerData = BinContainer.parse_stream(stream)
        except Exception as e:
            raise UnpackError("Ошибка при первичной распаковке: {0}".format(stream)) from e

        self.info_map = {info.path: info for info in self.container.info.files_info}

    def get_info(self, name_or_path: t.Union[str, Path]) -> FileInfo:
        """
        FileInfo по имени или пути.

        :param name_or_path: имя или путь
        :return: FileInfo, содержащий путь
        :raises KeyError: искомый FileInfo отсутствует
        :raises TypeError: name_of_path не str и не Path
        """

        if isinstance(name_or_path, str):
            name = Path(name_or_path)
        elif isinstance(name_or_path, Path):
            name = name_or_path
        else:
            raise TypeError("Ожидалось str | Path: {}".format(type(name_or_path)))

        try:
            info = self.info_map[name]
        except KeyError:
            raise KeyError("Нет FileInfo, содержащего путь {}".format(name))

        return info

    def name_list(self) -> t.Sequence[Path]:
        """
        :return: cписок путей в образе.
        """

        return [info.path for info in self.container.info.files_info]

    def info_list(self) -> t.Sequence[FileInfo]:
        """
        :return: список FileInfo в образе.
        """

        return self.container.info.files_info

    def print_dir(self, file: t.Optional[t.TextIO] = None) -> None:
        """
        Вывод сводки об архиве в file: путь, размер, контрольная сумма, если есть.

        :param file: открытый текстовый файл
        """

        files_info = self.container.info.files_info
        if not files_info:
            return

        fmt = '{0!s:<52} {1:>12}'
        header = ["File Name", "Size"]
        getters = [lambda o: o.path, lambda o: o.size]

        checked = files_info[0].sha1 is not None
        if checked:
            fmt = fmt + ' {2:>5}'
            header.append("SHA-1")
            getters.append(lambda o: o.sha1.hex()[:5])

        print(fmt.format(*header), file=file)
        for info in self.container.info.files_info:
            values = map(lambda g: g(info), getters)  # type: ignore
            print(fmt.format(*values), file=file)

    def extract(self, item: FileItem,
                path: t.Optional[os.PathLike] = None  # type: ignore
                ) -> Path:
        """
        Извлечение item в директорию path.

        :param item: строка, путь или FileInfo
        :param path: путь выходной директории; текущая директория, если не указан.
        :return: путь файла в выходной директории path
        :raises KeyError: item отсутствует
        :raises TypeError: не удалось построить Path по указанному path
        :raises TypeError: item не str и не Path
        :raises EnvironmentError: ошибка ввода-вывода
        """

        if path is None:
            path = Path.cwd()
        elif not isinstance(path, Path):
            path = Path(path)

        return self._extract_item(item, path)

    def extract_all(self,
                    path: t.Optional[os.PathLike] = None,  # type: ignore
                    items: t.Optional[t.Sequence[FileItem]] = None
                    ) -> None:
        """
        Извлечение items в директорию path.

        :param path: путь PathLike выходной директории; текущая директория, если не указан.
        :param items: FileItem, файлы которых подлежат извлечению; все, если не указано
        :raises KeyError: один из items отсутствует
        :raises TypeError: не удалось построить Path по указанному path
        :raises TypeError: один из item не str и не Path
        :raises EnvironmentError: ошибка ввода-вывода
        """

        if items is None:
            items = self.info_list()

        if path is None:
            path = Path.cwd()
        elif not isinstance(path, Path):
            path = Path(path)

        for item in items:
            self._extract_item(item, path)

    def _chunk_reader(self, reader: RangedReader) -> t.Iterable[bytes]:
        """
        Итератор reader байтовых строк размером не более chunk_size

        :param reader: объект, реализующий протокол файла
        :return: байтовые строки
        :raises TypeError: объект не Iterable
        :raises EnvironmentError: ошибка ввода-вывода
        """

        return iter(lambda: reader.read(self.chunk_size), b'')

    def _extract_item(self, item: FileItem, path: Path) -> Path:
        """
        Извлечение файла, связанного с item, в директорию path.

        :param item: FileItem целевого файла
        :param path: путь выходной директории
        :return: путь файла в выходной директории path
        :raises KeyError: один из items отсутствует
        :raises TypeError: item не str и не Path
        :raises EnvironmentError: ошибка ввода-вывода
        """

        if not isinstance(item, FileInfo):  # str | Path
            item = self.get_info(item)

        out_path = path / item.path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        istream = self.container.info.stream
        with open(out_path, 'wb') as ostream:
            reader = RangedReader(istream, item.offset, item.offset + item.size)
            for chunk in self._chunk_reader(reader):
                ostream.write(chunk)

        return out_path

    def check(self, inner: bool = False) -> CheckResult:
        """
        Проверка содержимого по контрольной сумме в контейнере.

        :param inner: проверка по контрольным суммам файлов
        :return: результат проверки
        """

        istream: t.Union[RangedReader, io.BufferedIOBase] = self.container.info.stream

        if self.container.md5 is None:
            return CheckResult(None, None)

        m = hashlib.md5()
        for chunk in iter(lambda: istream.read(self.chunk_size), b''):
            m.update(chunk)
        md5 = m.digest()
        status = md5 == self.container.md5
        if status is False:
            return CheckResult(False, None)

        if inner:
            files_info = self.container.info.files_info
            if files_info and files_info[0].sha1 is not None:
                failed = []
                for info in files_info:
                    m = hashlib.sha1()
                    reader = RangedReader(istream, info.offset, info.offset + info.size)
                    for chunk in self._chunk_reader(reader):
                        m.update(chunk)
                    if m.digest() != info.sha1:
                        failed.append(info.path)
                return CheckResult(not failed, failed if failed else None)

        return CheckResult(True, None)
