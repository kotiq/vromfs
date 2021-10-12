import os
from pathlib import Path
import typing as t
import construct as ct

T = t.TypeVar('T')
VT = t.Union[T, t.Callable[[ct.Container], T]]


def getvalue(val: VT[T], context: ct.Container) -> T:
    return val(context) if callable(val) else val


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
