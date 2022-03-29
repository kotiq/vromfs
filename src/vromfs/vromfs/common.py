import os
from pathlib import Path
import typing as t
import construct as ct
from construct import this

__all__ = [
    'Name',
    'NamesData',
    'FileInfo',
]

T = t.TypeVar('T')
VT = t.Union[T, t.Callable[[ct.Container], T]]

RawCString = ct.NullTerminated(ct.GreedyBytes)


class NameAdapter(ct.Adapter):
    def _decode(self, obj: bytes, context: ct.Container, path: str) -> Path:
        name = 'nm' if obj == b'\xff\x3fnm' else obj.decode()
        if os.path.isabs(name):
            pos = 0
            sz = len(name)
            while pos < sz and name[pos] == os.path.sep:
                pos += 1
            name = name[pos:]

        if not name:
            raise ValueError('Пустое имя')

        return Path(name)

    def _encode(self, obj: Path, context: ct.Container, path: str) -> bytes:
        if obj.is_absolute():
            raise ValueError('Ожидался относительный путь: {}'.format(obj))

        name = str(obj)
        return b'\xff\x3fnm' if name == 'nm' else name.encode()


Name = NameAdapter(RawCString)


class NamesData(ct.Construct):
    def __init__(self, offsets: VT[t.Union[t.Sequence[int], t.MutableSequence[int]]]):
        super().__init__()
        self.offsets = offsets

    def _parse(self, stream: t.BinaryIO, context: ct.Container, path: str) -> t.Sequence[Path]:
        offsets: t.Sequence[int] = ct.evaluate(self.offsets, context)
        if not offsets:
            raise ct.CheckError('Ожидалась не пустая последовательность смещений.')

        names = []
        max_end_offset = 0
        for offset in offsets:
            ct.stream_seek(stream, offset)
            name = Name._parsereport(stream, context, path)
            end_offset = ct.stream_tell(stream)
            max_end_offset = max(end_offset, max_end_offset)
            names.append(name)
        ct.stream_seek(stream, max_end_offset)
        return names

    def _build(self, obj: t.Sequence[Path], stream: ct.Container, context: ct.Container, path: str
               ) -> t.Sequence[Path]:
        if not obj:
            raise ct.CheckError('Ожидалась не пустая последовательность имен.')

        offsets: t.MutableSequence[int] = ct.evaluate(self.offsets, context)
        offsets.clear()

        for name in obj:
            offset = ct.stream_tell(stream)
            offsets.append(offset)
            Name._build(name, stream, context, path)

        return obj


Names = ct.Struct(
    'names_info' / ct.Aligned(16, ct.Int64ul[this.count]),
    'names_data' / ct.Aligned(16, NamesData(this.names_info)),
)


class FileInfo(t.NamedTuple):
    path: Path
    """Относительный путь."""

    offset: int
    """Смещение от начала образа VROMFS."""

    size: int
    """Размер данных в байтах."""

    digest: t.Optional[bytes]
    """SHA-1 дайджест данных."""
