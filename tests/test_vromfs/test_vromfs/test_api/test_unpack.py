import typing as t
import pytest
from pytest_lazyfixture import lazy_fixture
from vromfs.vromfs.constructor.eager import File, unpack as eager_unpack

image_with_hashes_istream = lazy_fixture('image_with_hashes_istream')
image_with_hashes_files = lazy_fixture('image_with_hashes_files')

image_with_hash_header_null_begin_istream = lazy_fixture('image_with_hash_header_null_begin_istream')
image_with_hash_header_null_begin_files = lazy_fixture('image_with_hash_header_null_begin_files')

image_without_hashes_istream = lazy_fixture('image_without_hashes_istream')
image_without_hashes_files = lazy_fixture('image_without_hashes_files')


@pytest.mark.parametrize(['image_istream', 'image_files'], [
    pytest.param(
        image_with_hashes_istream,
        image_with_hashes_files,
        id='image_with_hashes',
    ),
    pytest.param(
        image_with_hash_header_null_begin_istream,
        image_with_hash_header_null_begin_files,
        id='image_with_hash_header_null_begin',
    ),
    pytest.param(
        image_without_hashes_istream,
        image_without_hashes_files,
        id='image_without_hashes',
    ),
])
@pytest.mark.parametrize('unpack', [
    pytest.param(eager_unpack, id='eager'),
])
def test_unpack(unpack, image_istream: t.BinaryIO, image_files: t.Sequence[File]):
    files = unpack(image_istream)
    assert files == image_files
