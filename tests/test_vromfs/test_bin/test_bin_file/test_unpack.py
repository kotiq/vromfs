import hashlib
from pathlib import Path
from vromfs.bin import BinFile
from helpers import make_tmppath

tmppath = make_tmppath(__name__)


def test_unpack_check_digest(binfile: BinFile, tmppath: Path):
    in_path = Path(binfile.name)
    out_path = tmppath / in_path.stem
    binfile.unpack(out_path)
    assert binfile.size == out_path.stat().st_size
    if binfile.checked:
        m = hashlib.md5()
        size = 2**20
        with open(out_path, 'rb') as istream:
            for chunk in iter(lambda: istream.read(size), b''):
                m.update(chunk)
        assert binfile.digest == m.digest()
