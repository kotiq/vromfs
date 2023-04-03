from argparse import Action, ArgumentError, ArgumentParser, Namespace
import os.path
from io import BytesIO, SEEK_END
import logging
from pathlib import Path
import sys
from typing import NamedTuple, Optional, Type
from vromfs.bin import BinFile, Version, BinPackError, PlatformType
from vromfs.vromfs import VromfsFile, VromfsPackError


def get_logger(name: str) -> logging.Logger:
    formatter = logging.Formatter('%(created)s %(levelname)s %(message)s')
    logger_ = logging.getLogger(name)
    logger_.level = logging.DEBUG
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger_.addHandler(console_handler)

    return logger_


logger = get_logger('vromfs')


class Args(NamedTuple):
    @classmethod
    def from_namespace(cls, ns: Namespace) -> 'Args':
        return cls(**vars(ns))

    version: Version
    out_path: Path
    in_path: Path
    compressed: bool
    checked: bool


class MakeVersion(Action):
    def __call__(self, parser: ArgumentParser, namespace: Namespace,
                 values: str, option_string: Optional[str] = None) -> None:
        xs = values.split('.')
        sz = len(xs)
        if sz > 4:
            raise ArgumentError(self, 'Ожидалось 4х компонентное значение с разделителем "."')

        vs = []
        for i, x in enumerate(xs, 1):
            try:
                v = int(x)
            except ValueError:
                raise ArgumentError(self, 'Ожидалось десятичное целое: поз.{}, {}'.format(i, x))
            else:
                if not 0 <= v < 256:
                    raise ArgumentError(self, 'Ожидалось целое 0... 255: поз.{}, {}'.format(i, v))
                vs.append(v)

        for _ in range(4 - sz):
            vs.insert(0, 0)

        setattr(namespace, self.dest, tuple(vs))


def make_in_path(out_path_dest: str) -> Type[Action]:
    class MakeInputPath(Action):
        def __call__(self, parser: ArgumentParser, namespace: Namespace,
                     values: str, option_string: Optional[str] = None) -> None:
            out_path: Path = getattr(namespace, out_path_dest).absolute()
            in_path = Path(values).absolute()
            if not in_path.is_dir():
                raise ArgumentError(self, 'Ожидалась директория: {}'.format(in_path))
            # if out_path.is_relative_to(in_path):  # 3.9+
            if Path(os.path.commonpath([in_path, out_path])) == in_path:
                raise ArgumentError(self, 'Выходной файл во входной директории: {}'.format(in_path))

            setattr(namespace, self.dest, in_path)

    return MakeInputPath


def get_args() -> Args:
    parser = ArgumentParser(description='Упаковщик vromfs bin контейнера.',
                            epilog='Если не указаны ни checked ни compressed, применяются оба аргумента.')
    parser.add_argument('-v', '--ver', dest='version',  action=MakeVersion,
                        help='Версия архива xxx.yyy.zzz.www')
    parser.add_argument('--compressed', action='store_true', default=False, help='Сжать образ.')
    parser.add_argument('--checked', action='store_true', default=False, help='Добавить дайджест несжатого образа.')
    parser.add_argument('-o', '--output', dest='out_path', type=Path, default=Path('out.vromfs.bin'),
                        help='Выходной файл. По умолчанию %(default)s')
    parser.add_argument('in_path', action=make_in_path('out_path'), help='Директория для упаковки.')
    args = parser.parse_args()

    if not (args.compressed or args.checked):
        args.compressed = args.checked = True

    return Args.from_namespace(args)


def main() -> int:
    args_ns = get_args()
    vromfs_stream = BytesIO()
    try:
        VromfsFile.pack_into(args_ns.in_path, vromfs_stream)
    except VromfsPackError as e:
        logger.error(f'{args_ns.in_path} => temp vromfs')
        logger.exception(e)
        return 1

    logger.debug(f'{args_ns.in_path} => temp vromfs')

    vromfs_size = vromfs_stream.seek(0, SEEK_END)
    vromfs_stream.seek(0)

    logger.debug(f'Размер временного образа: {vromfs_size}')

    with open(args_ns.out_path, 'wb') as bin_stream:
        try:
            BinFile.pack_into(vromfs_stream, bin_stream, PlatformType.PC, args_ns.version,
                              compressed=args_ns.compressed, checked=args_ns.checked, size=vromfs_size)
        except BinPackError as e:
            logger.error(f'temp vromfs => {args_ns.out_path}')
            logger.exception(e)
            return 1

    logger.debug(f'temp vromfs => {args_ns.out_path}')
    logger.info(f'{args_ns.in_path} => {args_ns.out_path}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
