from pathlib import Path
import typing as t
import pytest
from pytest_lazyfixture import lazy_fixture
from vromfs.vromfs.constructor.eager import pack as eager_pack
from vromfs.vromfs.constructor.error import VromfsPackError
from helpers import make_tmppath

image_with_hashes_bs = lazy_fixture('image_with_hashes_bs')
image_with_hash_header_null_begin_bs = lazy_fixture('image_with_hash_header_null_begin_bs')
image_without_hashes_bs = lazy_fixture('image_without_hashes_bs')
tmppath = make_tmppath(__name__)


@pytest.fixture(scope='module')
def path(paths: t.Sequence[Path], contents: t.Sequence[bytes], tmppath: Path):
    root = tmppath / 'plain'
    root.mkdir(exist_ok=True)
    for path, content in zip(paths, contents):
        (root / path).write_bytes(content)
    return root


@pytest.mark.parametrize(['add_header', 'check', 'image_bs'], [
    pytest.param(True, True, image_with_hashes_bs, id='image_with_hashes'),
    pytest.param(True, False, image_with_hash_header_null_begin_bs, id='image_with_hash_header_null_begin'),
    pytest.param(False, False, image_without_hashes_bs, id='image_without_hashes')
])
@pytest.mark.parametrize('pack', [
    pytest.param(eager_pack, id='eager'),
])
def test_pack(pack, path: Path, add_header: bool, check: bool, image_bs: bytes, ostream: t.BinaryIO):
    pack(path, ostream, add_header, check)
    ostream.seek(0)
    built = ostream.read()
    assert built == image_bs


@pytest.mark.parametrize('pack', [
    pytest.param(eager_pack, id='eager'),
])
def test_pack_checked_no_hashes_header_raises_vromfs_pack_error(pack, path: Path, ostream: t.BinaryIO):
    with pytest.raises(VromfsPackError, match='Наличие дайджестов предполагает дополнительный заголовок'):
        pack(path, ostream, False, True)
