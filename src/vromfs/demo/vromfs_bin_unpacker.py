from argparse import Action, ArgumentParser, FileType, Namespace
import json
import logging
from pathlib import Path
import sys
from typing import BinaryIO, Iterable, NamedTuple, Optional, TextIO
from blk import Format
from vromfs.bin import BinFile
from vromfs.vromfs import VromfsFile

FILES_INFO_VERSION = '1.1'


def iname(f: Format) -> str:
    return f.name.lower()


def format_(s: str) -> Format:
    return Format[s.upper()]


def get_logger(name: str) -> logging.Logger:
    formatter = logging.Formatter('%(created)f %(levelname)s %(message)s')
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

    out_format: Format
    is_sorted: bool
    is_minified: bool
    dump_files_info: bool
    out_path: Optional[Path]
    input: BinaryIO
    in_files: Optional[TextIO]
    exit_first: bool
    loglevel: str


class CreateFormat(Action):
    def __call__(self, parser: ArgumentParser, namespace: Namespace,
                 values: str, option_string=None) -> None:
        f = format_(values)
        setattr(namespace, self.dest, f)


class CreateLogLevel(Action):
    def __call__(self, parser: ArgumentParser, namespace: Namespace, values: str, option_string=None) -> None:
        level = values.upper()
        setattr(namespace, self.dest, level)


def get_args() -> Args:
    parser = ArgumentParser(description='Распаковщик vromfs bin контейнера.')
    parser.add_argument('--format', dest='out_format', choices=sorted(map(iname, Format)),
                        action=CreateFormat, default=Format.JSON,
                        help='Формат блоков. По умолчанию {}.'.format(iname(Format.JSON)))
    parser.add_argument('--sort', dest='is_sorted', action='store_true', default=False,
                        help='Сортировать ключи для JSON*.')
    parser.add_argument('--minify', dest='is_minified', action='store_true', default=False,
                        help='Минифицировать JSON*.')
    parser.add_argument('--metadata', dest='dump_files_info', action='store_true', default=False,
                        help='Сводка о файлах: имя => SHA1 дайджест.')
    parser.add_argument('--input_filelist', dest='in_files', type=FileType(), default=None,
                        help=('Файл со списком файлов в формате JSON. '
                              '"-" - читать из stdin.'))
    parser.add_argument('-x', '--exitfirst', dest='exit_first', action='store_true', default=False,
                        help='Закончить распаковку при первой ошибке.')
    parser.add_argument('-o', '--output', dest='out_path', type=Path, default=None,
                        help=('Выходной файл для сводки о файлах или родитель выходной директории для распаковки. '
                              'Если output не указан, вывод сводки о файлах в stdout, выходная директория '
                              'для распаковки - имя контейнера с постфиксом _u.')
                        )
    parser.add_argument('--loglevel', action=CreateLogLevel, choices=('critical', 'error', 'warning', 'info', 'debug'),
                        default='INFO',
                        help='Уровень сообщений. По умолчанию info.')
    parser.add_argument(dest='input', type=FileType('rb'), help='Контейнер.')
    args = parser.parse_args()
    return Args.from_namespace(args)


def dump_files_info(vromfs: VromfsFile,
                    paths: Optional[Iterable[Path]] = None, ostream: Optional[TextIO] = None):
    if ostream is None:
        ostream = sys.stdout

    absent = []
    table = vromfs.digests_table(paths, absent)
    filelist = {str(path): digest.hex() for path, digest in table.items()}
    _filelist = [str(path) for path in absent]
    m = {
        'version': FILES_INFO_VERSION,
        'filelist': filelist,
    }
    if _filelist:
        m['~filelist'] = _filelist
    json.dump(m, ostream)


def main():
    args = get_args()
    logger.setLevel(args.loglevel)

    vromfs = VromfsFile(BinFile(args.input))

    if args.in_files is None:
        paths = args.in_files
    else:
        try:
            names = json.load(args.in_files)
            paths = [Path(name) for name in names]
        except Exception as e:
            logger.error('Ошибка при получении списка файлов.')
            logger.exception(e)
            return 1
        else:
            if not len(paths):
                logger.info('Нет файлов для извлечения.')
                return 0

    if args.dump_files_info:
        try:
            if args.out_path is None:
                dump_files_info(vromfs, paths)
            else:
                with open(args.out_path, 'w') as ostream:
                    dump_files_info(vromfs, paths, ostream)
        except Exception as e:
            logger.error('Ошибка при формировании сводки о файлах.')
            logger.exception(e)
            return 1
    else:
        if args.out_path is None:
            out_path = Path(args.input.name + '_u')
        else:
            out_path = args.out_path / Path(args.input.name).name

        failed = successful = 0
        try:
            logger.info('Начало распаковки.')
            for result in vromfs.unpack_iter(paths, out_path, args.out_format, args.is_sorted, args.is_minified):
                if result.error is not None:
                    failed += 1
                    logger.info(f'[FAIL] {args.input.name!r}::{str(result.path)!r}: {result.error}')
                    if args.exit_first:
                        break
                else:
                    logger.info(f'[ OK ] {args.input.name!r}::{str(result.path)!r}')
                    successful += 1

            logger.info('Успешно распаковано: {}/{}.'.format(successful, successful+failed))
            if failed:
                logger.info('Ошибка при обработке файлов.')
                return 1

        except Exception as e:
            logger.error('Ошибка при распаковке файлов.')
            logger.exception(e)
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
