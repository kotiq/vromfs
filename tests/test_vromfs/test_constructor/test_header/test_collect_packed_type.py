"""Проверка заголовка."""

from collections import defaultdict
from pathlib import Path
import typing as t
from vromfs.constructor import BinHeader
from helpers import make_outpath

outpath = make_outpath(__name__)


def containers(dir_path: Path) -> t.Generator[Path, None, None]:
    for path in dir_path.iterdir():
        if path.is_dir():
            yield from containers(path)
        elif path.name.endswith('.vromfs.bin'):
            yield path


def test_collect_packed_type(gamepaths: t.Sequence[Path], outpath: Path):
    """Построение карты с типами упаковки и размерами."""

    m = defaultdict(list)
    for gamepath in gamepaths:
        root = gamepath.parent
        for path in containers(gamepath):
            header = BinHeader.parse_file(path)
            type_ = header.packed.type
            size = header.packed.size
            rpath = path.relative_to(root)
            m[type_].append((size, rpath))

    with open(outpath / 'packed_types.txt', 'w') as ostream:
        indent = ' '*2
        for type_ in sorted(m.keys()):
            infos = m[type_]
            print(hex(type_), file=ostream)
            for size, rpath in sorted(infos, key=lambda p: p[0]):
                print(f'{indent}{size:#010x} {rpath}', file=ostream)
