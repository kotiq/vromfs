from pathlib import Path
import pytest
from vromfs.files.names import decompress_shared_names, FS
from helpers import make_outpath

outpath = make_outpath(__name__)


class UnpackedFS(FS):
    def __init__(self, root: Path):
        super().__init__()
        self.root = root

    def bytes(self, path: Path) -> bytes:
        return (self.root / path).read_bytes()


@pytest.mark.parametrize('sub', ['aces', 'char'])
def test_decompress_shared_names(sub, binrespath: Path, outpath: Path):
    root_path = binrespath / 'vromfs' / sub
    compressed_path = root_path / 'nm'
    fs = UnpackedFS(root_path)
    uncompressed_path = outpath / sub / 'nm'
    uncompressed_path.parent.mkdir(parents=True, exist_ok=True)
    with open(compressed_path, 'rb') as istream:
        uncompressed_path.write_bytes(decompress_shared_names(istream, fs))
