import json
from pathlib import Path
import zstandard as zstd
import pytest
from vromfs.files.shared_names import (decompress_shared_names, compress_shared_names, compose_shared_names,
                                       serialize_shared_names)
from helpers import make_outpath, create_text

outpath = make_outpath(__name__)


@pytest.mark.parametrize('sub', ['aces.zstd', 'char.zstd'])
def test_decompress_shared_names(sub: str, binrespath: Path, outpath: Path):
    sub = Path(sub)
    root_path = binrespath / sub
    compressed_path = root_path / 'nm'
    uncompressed_path = outpath / sub.with_suffix('.unzstd') / 'nm'
    uncompressed_path.parent.mkdir(parents=True, exist_ok=True)

    dict_paths = tuple(root_path.glob('*.dict'))
    if dict_paths:
        data = dict_paths[0].read_bytes()
        dict_data = zstd.ZstdCompressionDict(data)
        dctx = zstd.ZstdDecompressor(dict_data)
    else:
        dctx = zstd.ZstdDecompressor()

    with open(compressed_path, 'rb') as istream:
        names_bs = decompress_shared_names(istream, dctx)
        uncompressed_path.write_bytes(names_bs)


@pytest.mark.parametrize('sub', ['aces.unzstd', 'char.unzstd'])
def test_compress_shared_names(sub: str, binrespath: Path, outpath: Path):
    sub = Path(sub)
    root_path = binrespath / sub
    uncompressed_path = root_path / 'nm'
    compressed_path = outpath / sub.with_suffix('.zstd') / 'nm'
    compressed_path.parent.mkdir(parents=True, exist_ok=True)

    dict_paths = tuple(root_path.glob('*.dict'))
    if dict_paths:
        dict_path = dict_paths[0]
        data = dict_path.read_bytes()
        dict_data = zstd.ZstdCompressionDict(data)
        cctx = zstd.ZstdCompressor(dict_data=dict_data)
    else:
        dict_path = None
        cctx = zstd.ZstdCompressor()

    with open(compressed_path, 'wb') as ostream:
        names_bs = uncompressed_path.read_bytes()
        compress_shared_names(names_bs, ostream, cctx=cctx, dict_path=dict_path)


@pytest.mark.parametrize('sub', ['aces', 'char'])
def test_compose_shared_names(sub, binrespath: Path, outpath: Path):
    root_path = binrespath / sub
    input_path = root_path / 'nm'
    output_path = outpath / sub / 'nm_dict.json'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dict_paths = tuple(root_path.glob('*.dict'))
    if dict_paths:
        data = dict_paths[0].read_bytes()
        dict_data = zstd.ZstdCompressionDict(data)
        dctx = zstd.ZstdDecompressor(dict_data)
    else:
        dctx = zstd.ZstdDecompressor()

    with open(input_path, 'rb') as istream, create_text(output_path) as ostream:
        names_map = compose_shared_names(istream, dctx=dctx)
        json.dump(names_map, ostream, ensure_ascii=False, indent=2)


@pytest.mark.parametrize('sub', ['aces', 'char'])
def test_serialize_shared_names(sub: str, binrespath: Path, outpath: Path):
    root_path = binrespath / sub
    input_path = root_path / 'nm'
    output_path = outpath / sub / 'nm.zst.bin'
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dict_paths = tuple(root_path.glob('*.dict'))
    if dict_paths:
        dict_path = dict_paths[0]
        data = dict_path.read_bytes()
        dict_data = zstd.ZstdCompressionDict(data)
        dctx = zstd.ZstdDecompressor(dict_data)
        cctx = zstd.ZstdCompressor(dict_data=dict_data)
    else:
        dict_path = None
        dctx = zstd.ZstdDecompressor()
        cctx = zstd.ZstdCompressor()

    with open(input_path, 'rb') as istream, open(output_path, 'wb+') as iostream:
        inv_names_map = compose_shared_names(istream, dctx=dctx)
        assert inv_names_map
        serialize_shared_names(inv_names_map, iostream, cctx=cctx, dict_path=dict_path)
        assert iostream.tell() > 40
        iostream.seek(0)
        inv_names_map_ = compose_shared_names(iostream, dctx=dctx)
        assert inv_names_map_ == inv_names_map
