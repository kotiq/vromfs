from pathlib import Path
import typing as t


def containers(dir_path: Path) -> t.Generator[Path, None, None]:
    for path in dir_path.iterdir():
        if path.is_dir():
            yield from containers(path)
        elif path.name.endswith('.vromfs.bin'):
            yield path
