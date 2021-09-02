"""Сводка о двоичных blk."""
import json
import typing as t
import typing_extensions as te
from pathlib import Path
import pytest
from test_vromfs.test_parser import containers
from vromfs.parser import BinContainer, FileInfo
from helpers import make_outpath

outpath = make_outpath(__name__)


def starts_with(prefix: bytes):
    def g(bs: bytes):
        return bs.startswith(prefix)

    return g


is_bbf = starts_with(b'\x00BBF')
is_bbz = starts_with(b'\x00BBz')
is_fat = starts_with(b'\x01')
is_fat_zstd = starts_with(b'\x02')
is_slim = starts_with(b'\x03')
is_slim_zstd = starts_with(b'\x04')
is_slim_zstd_dict = starts_with(b'\x05')


def is_text(bs: bytes) -> bool:
    restricted = bytes.fromhex('00 01 02 03 04 05 06 07 08 0b 0c 0e 0f 10 11 12 14 13 15 16 17 18 19')
    return not any(b in restricted for b in bs)


BBF = 'bbf'
BBZ = 'bbz'
FAT = 'fat'
FAT_ZSTD = 'fat_zstd'
SLIM = 'slim'
SLIM_ZSTD = 'slim_zstd'
SLIM_SZTD_DICT = 'slim_zstd_dict'


@pytest.fixture(scope='module')
def blk_summary_path(outpath: Path):
    return outpath / 'blk_summary.json'


class Record(te.TypedDict):
    path: str
    name: str
    type: t.Optional[str]
    data: str


def test_collect_blk_summary(gamepaths: t.Sequence[Path], blk_summary_path: Path):
    rs: t.List[Record] = []

    for gamepath in gamepaths:
        root = gamepath.parent
        for path in containers(gamepath):
            rpath = str(path.relative_to(root))
            with open(path, 'rb') as istream:
                try:
                    bin_container = BinContainer.parse_stream(istream)
                except Exception as e:
                    print(f'[SKIP] {rpath!r} => {e}')
                    continue

                files_info: t.Sequence[FileInfo] = bin_container.info.files_info
                istream: t.BinaryIO = bin_container.info.stream
                data_sz = 5
                for file_info in files_info:
                    if not file_info.name.suffix == '.blk':
                        continue

                    if not file_info.size:
                        print(f'[SKIP] VOID {rpath}, {file_info.name}')
                        continue

                    if file_info.size >= data_sz:
                        istream.seek(file_info.offset)
                        bs = istream.read(data_sz)
                        if is_bbf(bs):
                            type_ = BBF
                        elif is_bbz(bs):
                            type_ = BBZ
                        elif is_fat(bs):
                            type_ = FAT
                        elif is_fat_zstd(bs):
                            type_ = FAT_ZSTD
                        elif is_slim(bs):
                            type_ = SLIM
                        elif is_slim_zstd(bs):
                            type_ = SLIM_ZSTD
                        elif is_slim_zstd_dict(bs):
                            type_ = SLIM_SZTD_DICT
                        else:
                            istream.seek(file_info.offset)
                            bs = istream.read(file_info.size)
                            if is_text(bs):
                                print(f'[SKIP] TEXT {rpath}, {file_info.name}')
                                continue
                            else:
                                type_ = None
                    else:
                        istream.seek(file_info.offset)
                        bs = istream.read(file_info.size)
                        if is_text(bs):
                            print(f'[SKIP] TEXT {rpath}, {file_info.name}')
                            continue
                        else:
                            type_ = None

                    name = str(file_info.name)
                    data = bs[:data_sz].hex()
                    r = Record(path=rpath, name=name, type=type_, data=data)
                    rs.append(r)

    for r in rs:
        assert (r['type'] is not None), f'{r["path"]}, {r["name"]}'

    with open(blk_summary_path, 'w', encoding='utf8') as ostream:
        json.dump(rs, ostream, indent=2)
