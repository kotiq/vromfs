"""Проверка распаковки контейнера."""

import json
import shlex
import subprocess
from pathlib import Path
import typing as t
import typing_extensions as te
import pytest
from helpers import make_outpath
from vromfs.parser import MaybeCompressedRawBinContainer, RawBinContainer, VRFS, VRFX, ZSTD_OBFS_NOCHECK, IDENT, ZSTD_OBFS
from test_vromfs.test_parser import containers

outpath = make_outpath(__name__)


@pytest.mark.parametrize(['rpath', 'fst'], [
    pytest.param('char.vromfs.bin', b'\x20', id='char'),
    pytest.param('fonts.vromfs.bin', b'\x30', id='fonts'),
    pytest.param('grp_hdr.vromfs.bin', b'\x20', id='grp_hdr'),
])
def test_unbin(binrespath: Path, outpath: Path, rpath: str, fst: bytes):
    """Извлечение vromfs из bin контейнера.
    Для несжатых проверка содержимого на этом этапе не проводится.
    """

    ipath = binrespath / rpath
    opath = (outpath / rpath).with_suffix('')
    raw_bin_container = RawBinContainer.parse_file(ipath)
    with open(opath, 'wb') as ostream:
        ostream.write(raw_bin_container.vromfs)
    assert opath.stat().st_size
    with open(opath, 'rb') as istream:
        assert istream.read(1) == fst


def container_type_s(container_type: bytes) -> t.Optional[bool]:
    """container type s."""

    return {
        VRFS: True,
        VRFX: False,
    }.get(container_type)


def packet_type_poc(packed_type: int) -> t.Optional[t.Tuple[bool, bool, bool]]:
    """zstd packed, obfuscate, md5 outer checked."""

    return {
        ZSTD_OBFS_NOCHECK: (True, True, False),
        IDENT: (False, False, True),
        ZSTD_OBFS: (True, True, True),
    }.get(packed_type)


def vromfs_type_c(vromfs_type: int) -> t.Optional[bool]:
    """sha1 inner checked."""

    return {
        0x20: False,
        0x30: True,
    }.get(vromfs_type)


class Record(te.TypedDict):
    path: str
    container_type_s: bool

    size: int
    packed_size: int
    tail_size: int

    zstd_packed: bool
    obfuscated: bool
    outer_checked: bool
    inner_checked: bool


def test_collect_vromfs_bin_summary(gamepaths: t.Sequence[Path], outpath: Path, vromfs_bin_summary_path: Path):
    """Сводка по контейнерам и содержимому."""

    rs: t.List[Record] = []

    print()
    for gamepath in gamepaths:
        root = gamepath.parent
        for path in containers(gamepath):
            rpath = str(path.relative_to(root))
            try:
                raw_bin_container = RawBinContainer.parse_file(path)
            except Exception as e:
                print(f'{rpath!r} => {e}')
                compessed_raw_bin_container = MaybeCompressedRawBinContainer.parse_file(path)
                opath = (outpath / rpath).with_suffix('.unbin')
                opath.parent.mkdir(parents=True, exist_ok=True)
                opath.write_bytes(compessed_raw_bin_container.vromfs)
                continue
            header = raw_bin_container.header

            container_type = header.type
            container_type_s_ = container_type_s(container_type)
            if container_type_s_ is None:
                raise ValueError('Unknown container type: {}'.format(container_type.hex()))

            size = header.size

            packed_type = header.packed.type
            packed_type_poc_ = packet_type_poc(packed_type)
            if packed_type_poc_ is None:
                raise ValueError('Unknown packed type: {:#x}'.format(packed_type))
            zstd_packed, obfuscated, outer_checked = packed_type_poc_

            packed_size = header.packed.size
            tail_size = len(raw_bin_container.tail)

            vromfs_type = raw_bin_container.vromfs[0]
            inner_checked = vromfs_type_c(vromfs_type)
            if inner_checked is None:
                raise ValueError('Unknown vromfs type: {:#x}'.format(vromfs_type_c))

            r = Record(path=rpath, container_type_s=container_type_s_,
                       size=size, packed_size=packed_size, tail_size=tail_size,
                       zstd_packed=zstd_packed, obfuscated=obfuscated,
                       outer_checked=outer_checked, inner_checked=inner_checked)
            rs.append(r)

    with open(vromfs_bin_summary_path, 'w', encoding='utf8') as ostream:
        json.dump(rs, ostream, indent=2)


@pytest.fixture(scope='module')
def vromfs_bin_summary_path(outpath: Path):
    return outpath / 'vromfs_bin_summary.json'


@pytest.fixture(scope='module')
def vromfs_bin_summary(vromfs_bin_summary_path: Path) -> t.Sequence[Record]:
    if not vromfs_bin_summary_path.exists():
        cmdline = 'pytest -qs test_unbin.py::test_collect_vromfs_bin_summary'
        subprocess.check_call(shlex.split(cmdline))

    with open(vromfs_bin_summary_path, encoding='utf8') as istream:
        return json.load(istream)


def show_recs(recs: t.Iterable[Record], msg: str, p: t.Callable[[Record], bool]):
    indent = ' '*2
    print(msg + ':')
    for rec in recs:
        if p(rec):
            print(indent + rec['path'])
    print('-' * 25)


def test_vromfs_bin_summary(vromfs_bin_summary: t.Sequence[Record]):
    print()
    show_recs(vromfs_bin_summary, 'No tail and inner checked',
              lambda r: r['tail_size'] == 0 and r['inner_checked'])
    show_recs(vromfs_bin_summary, 'No tail and not packed',
              lambda r: r['tail_size'] == 0 and not r['packed_size'])
    show_recs(vromfs_bin_summary, 'Tail and not packed',
              lambda r: r['tail_size'] and not r['packed_size'])
    show_recs(vromfs_bin_summary, 'No tail and outer checked',
              lambda r: r['tail_size'] == 0 and r['outer_checked'])
