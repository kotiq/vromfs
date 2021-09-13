import json
from pathlib import Path
import pytest
from vromfs.files.names import decompress_shared_names, FS, compose_names, serialize_names
from helpers import make_outpath, create_text

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
        names_bs = decompress_shared_names(istream, fs)
        uncompressed_path.write_bytes(names_bs)


@pytest.mark.parametrize('sub', ['aces', 'char'])
def test_compose_shared_names(sub, binrespath: Path, outpath: Path):
    root_path = binrespath / 'vromfs' / sub
    input_path = root_path / 'nm'
    fs = UnpackedFS(root_path)
    output_path = outpath / sub / 'nm_dict.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(input_path, 'rb') as istream, create_text(output_path) as ostream:
        names_map = compose_names(istream, fs)
        json.dump(names_map, ostream, ensure_ascii=False, indent=2)


@pytest.mark.parametrize(['sub', 'dict_path'], [
    pytest.param('aces', Path('3d2907d0e7420dc093d67430955a607a2f467f1b79e0bea4aec49f6a9c2e4c71.dict'), id='aces'),
    pytest.param('char', None, id='char'),
])
def test_serialize_shared_names(sub, dict_path, binrespath: Path, outpath: Path):
    root_path = binrespath / 'vromfs' / sub
    input_path = root_path / 'nm'
    fs = UnpackedFS(root_path)
    output_path = outpath / sub / 'nm.zst.bin'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(input_path, 'rb') as istream, open(output_path, 'wb+') as iostream:
        names_map = compose_names(istream, fs)
        assert names_map.keys()
        pos = iostream.tell()
        serialize_names(names_map, dict_path, fs, iostream)
        assert iostream.tell() - pos > 40
        iostream.seek(0)
        names_map_ = compose_names(iostream, fs)
        assert names_map_ == names_map




