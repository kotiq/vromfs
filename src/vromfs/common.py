import io
import typing as t
import construct as ct

__all__ = [
    'file_apply',
]

CHUNK_SIZE = 2 ** 20
"""Размер блока по умолчанию."""


def file_apply(file: io.IOBase, f: t.Callable[[bytes], t.Any], size: int, chunk_size: int = CHUNK_SIZE):
    """
    Вспомогательная функция для обхода файла по блокам.

    :param file: Входной файл.
    :param f: Функция, применяемая к блоку.
    :param size: Размер файла, байт.
    :param chunk_size: Размер блока, байт.
    :raises ct.ConstructError: Ошибка чтения.
    """

    n, r = divmod(size, chunk_size)
    for _ in range(n):
        chunk = ct.stream_read(file, chunk_size)
        f(chunk)
    chunk = ct.stream_read(file, r)
    f(chunk)
