import io
import os
from pathlib import Path
import hashlib
import itertools as itt
import typing as t
from .parser import BinContainer, FileInfo, BinContailerData
from .reader import RangedReader

__all__ = ['CheckResult', 'VromfsBinFile']


class CheckResult(t.NamedTuple):
    status: t.Optional[bool]
    """Статус проверки: True: успех, False: неудача, None: не применимо"""
    failed: t.Optional[t.Sequence[Path]]
    """Список не прошедших проверку в случае неудачи для несжатого образа, иначе None.
    None для сжатого образа для любого статуса.
    """


FileItem = t.Union[str, Path, FileInfo]


class VromfsBinFile:
    chunk_size: t.ClassVar[int] = 2**20

    def __init__(self, name_or_stream: t.Union[os.PathLike, io.BufferedReader]):  # type: ignore
        if isinstance(name_or_stream, os.PathLike):
            name = os.fspath(name_or_stream)
            stream = open(name, 'rb')
        elif isinstance(name_or_stream, io.BufferedReader):
            stream = name_or_stream
        else:
            raise TypeError("Ожидалось PathLike | BufferedReader: {}".format(type(name_or_stream)))

        self.container: BinContailerData = BinContainer.parse_stream(stream)
        self.info_map = {info.name: info for info in self.container.info.files_info}

    def get_info(self, name_or_path: t.Union[str, Path]) -> t.Optional[FileInfo]:
        """FileInfo по имени, None, если нет."""

        if isinstance(name_or_path, str):
            name = Path(name_or_path)
        elif isinstance(name_or_path, Path):
            name = name_or_path
        else:
            raise TypeError("Ожидалось str | Path: {}".format(type(name_or_path)))

        return self.info_map.get(name)

    def name_list(self) -> t.Sequence[Path]:
        """Список имен в образе."""

        return [info.name for info in self.container.info.files_info]

    def info_list(self) -> t.Sequence[FileInfo]:
        """Список узлов в образе."""

        return self.container.info.files_info

    def print_dir(self, file: t.Optional[t.TextIO] = None) -> None:
        """Сводка об архиве в file"""

        files_info = self.container.info.files_info
        if not files_info:
            return

        fmt = '{0!s:<52} {1:>12}'
        header = ["File Name", "Size"]
        getters = [lambda o: o.name, lambda o: o.size]

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
                ) -> t.Sequence[Path]:
        """Извлечение item в директорию path и список путей извлеченных файлов.

        path - текущая директория, если не указана.
        """

        if path is None:
            path = Path.cwd()
        elif not isinstance(path, Path):
            path = Path(path)

        opath = self._extract_item(item, path)
        return [opath] if opath is not None else []

    def extract_all(self,
                    path: t.Optional[os.PathLike] = None,  # type: ignore
                    items: t.Optional[t.Sequence[FileItem]] = None
                    ) -> t.Sequence[Path]:
        """Извлечение items в директорию path и список путей извлеченных файлов.

        path - текущая директория, если не указана.
        items - все элементы, если не указаны.
        """

        if items is None:
            items = self.info_list()

        if path is None:
            path = Path.cwd()
        elif not isinstance(path, Path):
            path = Path(path)

        return list(itt.filterfalse(lambda p: p is None,
                    map(lambda item: self._extract_item(item, path), items)))  # type: ignore

    def _extract_item(self, item: FileItem, path: Path) -> t.Optional[Path]:
        if not isinstance(item, FileInfo):  # str | Path
            info = self.get_info(item)
            if info is None:
                return None
        else:
            info = item

        opath = path / info.name
        opath.parent.mkdir(parents=True, exist_ok=True)
        istream = self.container.info.stream
        with open(opath, 'wb') as ostream:
            reader = RangedReader(istream, info.offset, info.offset + info.size)
            for chunk in iter(lambda: reader.read(self.chunk_size), b''):
                ostream.write(chunk)

        return opath

    def check(self, inner: bool = False) -> CheckResult:
        """Проверка содержимого по контрольной сумме в контейнере.

        inner: проверка по контрольным суммам файлов, если они есть."""

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
                    for chunk in iter(lambda: reader.read(self.chunk_size), b''):
                        m.update(chunk)
                    if m.digest() != info.sha1:
                        failed.append(info.name)
                return CheckResult(not failed, failed if failed else None)

        return CheckResult(True, None)
