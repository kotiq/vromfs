import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import typing as t
from vromfs.bin import BinFile, PlatformType
from vromfs.vromfs import VromfsFile

launcher = Path('~/games/linux/WarThunder/launcher.vromfs.bin').expanduser()
launcher_src = Path('~/games/resources/vromfs/launcher.src').expanduser()
launcher_new = Path('~/games/resources/vromfs/launcher.out/launcher.vromfs.bin').expanduser()


def get_args():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--unpack', action='store_true')
    group.add_argument('--pack', action='store_true')
    return parser.parse_args()


def unpack(source: Path, target: Path) -> t.Mapping[str, t.Any]:
    bin_ = BinFile(source)
    vromfs = VromfsFile(bin_)
    target.mkdir(parents=True, exist_ok=True)
    for result in vromfs.unpack_gen(target):
        pass

    return {
        'bin': {
            'platform': bin_.platform,
            'version': bin_.version,
            'compressed': bin_.compressed,
            'checked': bin_.checked,
        },
        'vromfs': {
            'checked': vromfs.checked,
            'extended': vromfs.extended,
        }

    }


def dump_params(params: t.Mapping[str, t.Any], ostream: t.TextIO):
    m = deepcopy(params)
    m['bin']['platform'] = m['bin']['platform'].name
    json.dump(m, ostream)


def load_params(istream: t.TextIO) -> t.Mapping[str, t.Any]:
    m = json.load(istream)
    m['bin']['platform'] = PlatformType[m['bin']['platform']]
    return m


def pack(source: Path, target: Path, params: t.Mapping[str, t.Any]):
    target.parent.mkdir(parents=True, exist_ok=True)
    istream = VromfsFile.pack_into(source, **params['vromfs'])
    size = istream.tell()
    istream.seek(0)
    with open(target, 'wb') as ostream:
        BinFile.pack_into(istream, ostream, size=size, **params['bin'])


def main():
    args_ns = get_args()
    if args_ns.unpack:
        params = unpack(launcher, launcher_src)
        dump_params(params, sys.stdout)
        print()
    elif args_ns.pack:
        params = load_params(sys.stdin)
        pack(launcher_src, launcher_new, params)

    return 0


if __name__ == '__main__':
    sys.exit(main())
