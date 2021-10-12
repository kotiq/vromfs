import typing as t
import pytest
from pytest_lazyfixture import lazy_fixture
from vromfs.vromfs.constructor.eager import Image
from test_vromfs import _test_parse


image_with_hashes_bs = lazy_fixture('image_with_hashes_bs')
image_with_hashes_istream = lazy_fixture('image_with_hashes_istream')
image_with_hashes = lazy_fixture('image_with_hashes')

image_with_hash_header_null_begin_bs = lazy_fixture('image_with_hash_header_null_begin_bs')
image_with_hash_header_null_begin_istream = lazy_fixture('image_with_hash_header_null_begin_istream')
image_with_hash_header_null_begin = lazy_fixture('image_with_hash_header_null_begin')

image_without_hashes_bs = lazy_fixture('image_without_hashes_bs')
image_without_hashes_istream = lazy_fixture('image_without_hashes_istream')
image_without_hashes = lazy_fixture('image_without_hashes')


@pytest.mark.parametrize(['image_istream', 'image_bs', 'image'], [
    pytest.param(
        image_with_hashes_istream,
        image_with_hashes_bs,
        image_with_hashes,
        id='image_with_hashes'
    ),
    pytest.param(
        image_with_hash_header_null_begin_istream,
        image_with_hash_header_null_begin_bs,
        image_with_hash_header_null_begin,
        id='image_with_hash_header_null_begin'
    ),
    pytest.param(
        image_without_hashes_istream,
        image_without_hashes_bs,
        image_without_hashes,
        id='image_without_hashes'
    ),
])
def test_image_parse(image_istream: t.BinaryIO, image_bs: bytes, image: dict):
    _test_parse(Image, image_istream, image_bs, image)
