import argparse
import json
import logging
from pathlib import Path
import sys
import typing as t
from vromfs.bin import BinFile
from vromfs.vromfs import OutType, VromfsFile

FILES_INFO_VERSION = '1.1'


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
    out_format: OutType
    is_sorted: bool
    dump_files_info: bool
    maybe_out_path: t.Optional[Path]
    input: t.BinaryIO
    maybe_in_files: t.Optional[t.TextIO]


def get_args() -> ArgsNS:
    parser = argparse.ArgumentParser(description='Распаковщик vromfs bin контейнера.')
    parser.add_argument('--format', dest='out_format', choices=tuple(OutType),
                        type=lambda s: OutType[s.upper()], default=OutType.JSON,
                        help='Формат блоков. По умолчанию %(default)s.')
    parser.add_argument('--sort', dest='is_sorted', action='store_true', default=False,
                        help='Сортировать ключи для JSON*.')
    parser.add_argument('--metadata', dest='dump_files_info', action='store_true', default=False,
                        help='Сводка о файлах: имя => SHA1 дайджест.')
    parser.add_argument('--input_filelist', dest='maybe_in_files', type=argparse.FileType(), default=None,
                        help=('Файл со списком файлов в формате JSON. '
                              '"-" - читать из stdin.'))
    parser.add_argument('-o', '--output', dest='maybe_out_path', type=Path, default=None,
                        help=('Выходной файл для сводки о файлах или родитель выходной директории для распаковки. '
                              'Если output не указан, вывод сводки о файлах в stdout, выходная директория '
                              'для распаковки - имя контейнера с постфиксом _u.')
                        )
    parser.add_argument(dest='input', type=argparse.FileType('rb'), help='Контейнер.')
    args_ns = parser.parse_args()
    return ArgsNS(**args_ns.__dict__)


def dump_files_info(vromfs: VromfsFile,
                    paths: t.Optional[t.Iterable[Path]] = None, ostream: t.Optional[t.TextIO] = None):
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
    args_ns = get_args()

    vromfs = VromfsFile(BinFile(args_ns.input))

    if args_ns.maybe_in_files is None:
        maybe_paths = args_ns.maybe_in_files
    else:
        try:
            names = json.load(args_ns.maybe_in_files)
            maybe_paths = [Path(name) for name in names]
        except Exception as e:
            logger.error('Ошибка при получении списка файлов.')
            logger.exception(e)
            return 1
        else:
            if not len(maybe_paths):
                logger.info('Нет файлов для извлечения.')
                return 0

    if args_ns.dump_files_info:
        try:
            if args_ns.maybe_out_path is None:
                dump_files_info(vromfs, maybe_paths)
            else:
                with open(args_ns.maybe_out_path, 'w') as ostream:
                    dump_files_info(vromfs, maybe_paths, ostream)
        except Exception as e:
            logger.error('Ошибка при формировании сводки о файлах.')
            logger.exception(e)
            return 1
    else:
        if args_ns.maybe_out_path is None:
            out_path = Path(args_ns.input.name + '_u')
        else:
            out_path = args_ns.maybe_out_path / Path(args_ns.input.name).name

        failed = successful = 0
        try:
            logger.info('Начало распаковки.')
            for result in vromfs.unpack_gen(out_path, maybe_paths, args_ns.out_format, args_ns.is_sorted):
                if result.error is not None:
                    failed += 1
                    logger.error(f'[FAIL] {args_ns.input.name!r}::{str(result.path)!r}: {result.error}')
                else:
                    successful += 1

            logger.info('Успешно распаковано: {}/{}.'.format(successful, successful+failed))
            if failed:
                logger.error('Ошибка при обработке файлов.')
                return 1

        except Exception as e:
            logger.error('Ошибка при распаковке файлов.')
            logger.exception(e)
            return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
