import argparse
import os.path
import io
import logging
from pathlib import Path
import sys
import typing as t
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


class ArgsNS(t.NamedTuple):
    version: Version
    out_path: Path
    in_path: Path


class MakeVersion(argparse.Action):
    def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                 values: str, option_string=None) -> None:
        xs = values.split('.')
        sz = len(xs)
        if sz > 4:
            raise argparse.ArgumentError(self, 'Ожидалось 4х компонентное значение с разделителем "."')

        vs = []
        for i, x in enumerate(xs, 1):
            try:
                v = int(x)
            except ValueError:
                raise argparse.ArgumentError(self, 'Ожидалось десятичное целое: поз.{}, {}'.format(i, x))
            else:
                if not 0 <= v < 256:
                    raise argparse.ArgumentError(self, 'Ожидалось целое 0... 255: поз.{}, {}'.format(i, v))
                vs.append(v)

        for _ in range(4 - sz):
            vs.insert(0, 0)

        setattr(namespace, self.dest, tuple(vs))


def make_in_path(out_path_dest: str) -> t.Type[argparse.Action]:
    class MakeInputPath(argparse.Action):
        def __call__(self, parser: argparse.ArgumentParser, namespace: argparse.Namespace,
                     values: str, option_string=None) -> None:
            out_path: Path = getattr(namespace, out_path_dest).absolute()
            in_path = Path(values).absolute()
            if not in_path.is_dir():
                raise argparse.ArgumentError(self, 'Ожидалась директория: {}'.format(in_path))
            # if out_path.is_relative_to(in_path):  # 3.9+
            if Path(os.path.commonpath([in_path, out_path])) == in_path:
                raise argparse.ArgumentError(self, 'Выходной файл во входной директории: {}'.format(in_path))

            setattr(namespace, self.dest, in_path)

    return MakeInputPath


def get_args() -> ArgsNS:
    parser = argparse.ArgumentParser(description='Упаковщик vromfs bin контейнера.')
    parser.add_argument('-v', '--ver', dest='version',  action=MakeVersion, required=True,
                        help='Версия архива xxx.yyy.zzz.www')
    parser.add_argument('-o', '--output', dest='out_path', type=Path, default=Path('out.vromfs.bin'),
                        help='Выходной файл. По умолчанию %(default)s')
    parser.add_argument('in_path', action=make_in_path('out_path'), help='Директория для упаковки.')

    args_ns = parser.parse_args()
    return ArgsNS(**args_ns.__dict__)


def main() -> int:
    args_ns = get_args()
    vromfs_stream = io.BytesIO()
    try:
        VromfsFile.pack_into(args_ns.in_path, vromfs_stream)
    except VromfsPackError as e:
        logger.error(f'{args_ns.in_path} => temp vromfs')
        logger.exception(e)
        return 1

    logger.debug(f'{args_ns.in_path} => temp vromfs')

    vromfs_size = vromfs_stream.seek(0, io.SEEK_END)
    vromfs_stream.seek(0)

    logger.debug(f'Размер временного образа: {vromfs_size}')

    with open(args_ns.out_path, 'wb') as bin_stream:
        try:
            BinFile.pack_into(vromfs_stream, bin_stream, PlatformType.PC, args_ns.version,
                              compressed=True, checked=True, size=vromfs_size)
        except BinPackError as e:
            logger.error(f'temp vromfs => {args_ns.out_path}')
            logger.exception(e)
            return 1

    logger.debug(f'temp vromfs => {args_ns.out_path}')
    logger.info(f'{args_ns.in_path} => {args_ns.out_path}')

    return 0


if __name__ == '__main__':
    sys.exit(main())
