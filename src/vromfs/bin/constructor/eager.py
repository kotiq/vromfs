import hashlib
import io
import typing as t
import construct as ct
import zstandard as zstd
from .error import UnpackError, PackError, DecompressionError
from .common import PlatformType, BinHeader, BinExtHeader, HeaderType, PackType, UnpackResult, BinContainerInfo


def inplace_xor(buffer: bytearray, from_: int, sz: int, key: t.Iterable[int]) -> None:
    it = iter(key)
    for i in range(from_, from_ + sz):
        buffer[i] ^= next(it)


obfs_ks: t.Sequence[bytes] = [bytes.fromhex(s) for s in ('55aa55aa', '0ff00ff0', '55aa55aa', '48124812')]


def deobfuscate(bs: bytes) -> bytes:
    """
    Восстановление частей сжатого образа.

    :param bs: сжатый образ с измененными частями
    :return: сжатый образ
    """

    buffer = bytearray(bs)
    sz = len(bs)
    key_sz = sum(map(len, obfs_ks))
    if sz >= key_sz:
        pos = 0
        inplace_xor(buffer, pos, key_sz, b''.join(obfs_ks))
        if sz >= 2 * key_sz:
            pos = (sz & 0x03ff_fffc) - key_sz
            inplace_xor(buffer, pos, key_sz, b''.join(reversed(obfs_ks)))

    return bytes(buffer)


def decompress(bs: bytes, sz: int) -> bytes:
    """
    Извлечение образа из архива.

    :param bs: сжатый образ
    :param sz: размер извлеченного образа
    :return: образ
    """

    return zstd.decompress(bs, sz)


def compress(bs: bytes) -> bytes:
    """
    Упаковка образа в архив.

    :param bs: образ
    :return: сжатый образ
    """

    return zstd.compress(bs)


def obfuscate(bs: bytes) -> bytes:
    """
    Сокрытие частей сжатого образа.

    :param bs: сжатый образ
    :return: сжатый образ с измененными частями
    """

    return deobfuscate(bs)


def unpack(istream: t.BinaryIO, decompress_: bool = True) -> UnpackResult:
    """
    Распаковка образа из bin контейнера.

    :param istream: входной поток контейнера
    :param_ decompress_: для сжатого образа: извлечь образ из архива
    :return: результат распаковки
    """

    try:
        header = BinHeader.parse_stream(istream)
        platform = header.platform
        size = header.size

        pack_type = header.packed.type

        if header.type is HeaderType.VRFX:
            ext_header = BinExtHeader.parse_stream(istream)
            version = ext_header.version
        else:
            version = None

        if pack_type is PackType.PLAIN:
            packed_size = None
            image = ct.stream_read(istream, size)
        else:
            packed_size = header.packed.size
            zstd_obfs_image = ct.stream_read(istream, packed_size)
            zstd_image = deobfuscate(zstd_obfs_image)
            if decompress_:
                try:
                    image = decompress(zstd_image, size)
                except zstd.ZstdError as e:
                    raise DecompressionError from e
            else:
                image = zstd_image

        ostream = io.BytesIO(image)

        if pack_type in (PackType.PLAIN, PackType.ZSTD_OBFS):
            hash_ = ct.Bytes(16).parse_stream(istream)
        else:
            hash_ = None

        tail = ct.stream_read_entire(istream)
        tail_sz = len(tail)
        if tail_sz not in (0, 0x100):
            raise UnpackError("Неожиданный размер остаточных данных: {}".format(tail_sz))

    except ct.ConstructError as e:
        raise UnpackError from e
    else:
        return UnpackResult(
            stream=ostream,
            info=BinContainerInfo(
                platform=platform,
                unpacked_size=size,
                packed_size=packed_size,
                version=version,
                hash=hash_
            )
        )


def pack(istream: t.BinaryIO, ostream: t.BinaryIO,
         platform: PlatformType, version: t.Tuple[int, int, int, int], compress_: bool, check: bool,
         tail: bytes) -> None:
    """
    Упаковка образа в bin контейнер.

    :param istream: входной поток образа
    :param ostream: выходной поток bin контейнера
    :param platform: целевая платформа
    :param version: версия образа
    :param compress_: сжать образ
    :param check: добавить контрольную сумму
    :param tail: дополнительные данные
    """

    try:
        image = ct.stream_read_entire(istream)
        size = len(image)

        if compress_:
            zstd_image = compress(image)
            zstd_obfs_image = obfuscate(zstd_image)
            packed_size = len(zstd_obfs_image)
            data = zstd_obfs_image
            if check:  # check: 1, compress: 1
                packed_type = PackType.ZSTD_OBFS
            else:  # check: 0, compress: 1
                packed_type = PackType.ZSTD_OBFS_NOCHECK
        else:
            if not check:
                raise PackError("Нет типа упаковки для compress_={}, check={}".format(compress_, check))
            # check: 1, compress: 0
            packed_size = 0
            packed_type = PackType.PLAIN
            data = image

        header_type = HeaderType.VRFS if version is None else HeaderType.VRFX
        bin_header = dict(
            type=header_type,
            platform=platform,
            size=size,
            packed=dict(
                type=packed_type,
                size=packed_size
            )
        )
        BinHeader.build_stream(bin_header, ostream)
        if header_type is HeaderType.VRFX:
            BinExtHeader.build_stream(dict(flags=0, version=version), ostream)
        ct.stream_write(ostream, data)
        if check:
            hash_ = hashlib.md5(image).digest()
            ct.Bytes(16).build_stream(hash_, ostream)
        if tail:
            ct.stream_write(ostream, tail, 0x100)

    except ct.ConstructError as e:
        raise PackError from e
