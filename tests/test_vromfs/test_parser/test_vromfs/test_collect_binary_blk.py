"""Сводка о двоичных blk."""
import json
import typing as t
import typing_extensions as te
from pathlib import Path
import zstandard
import pytest
from test_vromfs.test_parser import containers
from vromfs.parser import BinContainer, FileInfo
from vromfs.reader import RangedReader
from helpers import make_outpath

outpath = make_outpath(__name__)


def starts_with(prefix: bytes):
    def g(bs: bytes):
        return bs.startswith(prefix)

    return g


is_bbf = starts_with(b'\x00BBF')
is_bbf_zlib = starts_with(b'\x00BBz')
is_fat = starts_with(b'\x01')
is_fat_zstd = starts_with(b'\x02')
is_slim = starts_with(b'\x03')
is_slim_zstd = starts_with(b'\x04')
is_slim_zstd_dict = starts_with(b'\x05')


def is_text(bs: bytes) -> bool:
    restricted = bytes.fromhex('00 01 02 03 04 05 06 07 08 0b 0c 0e 0f 10 11 12 14 13 15 16 17 18 19')
    return not any(b in restricted for b in bs)


BBF = 'bbf'
BBF_ZLIB = 'bbf_zlib'
FAT = 'fat'
FAT_ZSTD = 'fat_zstd'
SLIM = 'slim'
SLIM_ZSTD = 'slim_zstd'
SLIM_SZTD_DICT = 'slim_zstd_dict'

MAX_OUTPUT_SIZE = 5_000_000


@pytest.fixture(scope='module')
def blk_summary_path(outpath: Path):
    return outpath / 'blk_summary.json'


@pytest.fixture(scope='module')
def packed_path(outpath: Path):
    path = outpath / 'packed'
    path.mkdir(exist_ok=True)
    return path


@pytest.fixture(scope='module')
def samples_path(outpath: Path):
    path = outpath / 'samples'
    path.mkdir(exist_ok=True)
    return path


@pytest.fixture(scope='module')
def samples_summary_path(samples_path: Path):
    return samples_path / 'samples_summary.json'


class Record(te.TypedDict):
    path: str
    name: str
    type: t.Optional[str]
    data: str


def test_collect_blk_summary(
        gamepaths: t.Sequence[Path],
        blk_summary_path: Path,
        # packed_path: Path,
        samples_path: Path,
        samples_summary_path: Path,
):
    rs: t.List[Record] = []
    # dctx = zstandard.ZstdDecompressor(format=zstandard.FORMAT_ZSTD1)

    types_ = (BBF, BBF_ZLIB, FAT, FAT_ZSTD, SLIM, SLIM_ZSTD, SLIM_SZTD_DICT,)
    samples = dict.fromkeys(types_)

    for gamepath in gamepaths:
        root = gamepath.parent
        for path in containers(gamepath):
            rpath = path.relative_to(root)
            with open(path, 'rb') as istream:
                try:
                    bin_container = BinContainer.parse_stream(istream)
                except Exception as e:
                    print(f'[SKIP] {rpath} => {e}')
                    continue

                files_info: t.Sequence[FileInfo] = bin_container.info.files_info
                istream: t.BinaryIO = bin_container.info.stream
                head_sz = 5
                # используется первый словарь из контейнера
                dctx_dict: t.Optional[zstandard.ZstdDecompressor] = None

                for file_info in files_info:
                    if dctx_dict is None:
                        if file_info.name.suffix == '.dict':
                            istream.seek(file_info.offset)
                            dict_bs = istream.read(file_info.size)
                            zstd_dict = zstandard.ZstdCompressionDict(dict_bs)
                            dctx_dict = zstandard.ZstdDecompressor(dict_data=zstd_dict, format=zstandard.FORMAT_ZSTD1)

                    if not file_info.name.suffix == '.blk':
                        continue

                    if not file_info.size:
                        print(f'[SKIP] VOID {rpath}, {file_info.name}')
                        continue

                    if file_info.size >= head_sz:
                        istream.seek(file_info.offset)
                        maybe_packed_head = istream.read(head_sz)
                        if is_bbf(maybe_packed_head):
                            type_ = BBF
                        elif is_bbf_zlib(maybe_packed_head):
                            type_ = BBF_ZLIB
                        elif is_fat(maybe_packed_head):
                            type_ = FAT
                        elif is_fat_zstd(maybe_packed_head):
                            type_ = FAT_ZSTD
                        elif is_slim(maybe_packed_head):
                            type_ = SLIM
                        elif is_slim_zstd(maybe_packed_head):
                            type_ = SLIM_ZSTD
                        elif is_slim_zstd_dict(maybe_packed_head):
                            type_ = SLIM_SZTD_DICT
                        else:
                            istream.seek(file_info.offset)
                            maybe_packed_head = istream.read(file_info.size)
                            if is_text(maybe_packed_head):
                                print(f'[SKIP] TEXT {rpath}, {file_info.name}')
                                continue
                            else:
                                type_ = None

                        if type_ in types_:
                            if samples[type_] is None:
                                if file_info.size > 8:
                                    reader = RangedReader(istream, file_info.offset, file_info.offset+file_info.size)
                                    sample_path = samples_path / type_ / file_info.name.name
                                    sample_path.parent.mkdir(parents=True, exist_ok=True)
                                    sample_path.write_bytes(reader.read())
                                    samples[type_] = str(rpath / file_info.name)

                        # if type_ in (FAT_ZSTD, SLIM_ZSTD, SLIM_SZTD_DICT):
                        #     reader = RangedReader(istream, file_info.offset, file_info.offset+file_info.size)
                        #     decompressor = dctx_dict if type_ == SLIM_SZTD_DICT else dctx
                        #     start = 4 if type_ == FAT_ZSTD else 1
                        #     reader.seek(start)
                        #     # fat_zstd это наследник bbz
                        #     # [сигнатура / byte, sz / int24ul, zst архив / bytes(sz)]
                        #     try:
                        #         unpacked_reader = decompressor.stream_reader(reader, read_size=0x100, closefd=False)
                        #         unpacked_head = unpacked_reader.read(head_sz)
                        #         if type_ == FAT_ZSTD:
                        #             assert unpacked_head.startswith(b'\x01')
                        #         else:
                        #             assert unpacked_head.startswith(b'\x00')
                        #     except zstandard.ZstdError as e:
                        #         reader.seek(0)
                        #         packed_bs = reader.read()
                        #         packed_file_path = packed_path / rpath / file_info.name
                        #         packed_file_path.parent.mkdir(parents=True, exist_ok=True)
                        #         packed_file_path.write_bytes(packed_bs)
                        #         print(f'[FAIL] {rpath}, {file_info.name}')
                    else:
                        istream.seek(file_info.offset)
                        maybe_packed_head = istream.read(file_info.size)
                        if is_text(maybe_packed_head):
                            print(f'[SKIP] TEXT {rpath}, {file_info.name}')
                            continue
                        else:
                            type_ = None

                    name = str(file_info.name)
                    data = maybe_packed_head[:head_sz].hex()
                    r = Record(path=str(rpath), name=name, type=type_, data=data)
                    rs.append(r)

    for r in rs:
        assert (r['type'] is not None), f'{r["path"]}, {r["name"]}'

    with open(blk_summary_path, 'w', encoding='utf8') as ostream:
        json.dump(rs, ostream, indent=2)

    with open(samples_summary_path, 'w', encoding='utf8') as ostream:
        json.dump(samples, ostream, indent=2)
