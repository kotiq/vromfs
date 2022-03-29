import io
import construct as ct
import pytest
from pytest import param as _
from pytest_lazyfixture import lazy_fixture
from vromfs.vromfs import NamesData
from test_vromfs import check_parse, check_build

separate_bytes = lazy_fixture('separate_bytes')
separate_offsets = lazy_fixture('separate_offsets')
reversed_separate_bytes = lazy_fixture('reversed_separate_bytes')
reversed_separate_offsets = lazy_fixture('reversed_separate_offsets')
overlapping_bytes = lazy_fixture('overlapping_bytes')
overlapping_offsets = lazy_fixture('overlapping_offsets')


@pytest.mark.parametrize(['bytes_', 'offsets'], [
    _(separate_bytes, separate_offsets, id='separate'),
    _(reversed_separate_bytes, reversed_separate_offsets, id='reversed_separate'),
    _(overlapping_bytes, overlapping_offsets, id='overlapping'),
])
def test_parse(bytes_, offsets, names):
    con = NamesData(offsets)
    istream = io.BytesIO(bytes_)
    bytes_len = len(bytes_)
    check_parse(con, istream, bytes_len, names)


def test_parse_no_offsets_raises_check_error(separate_bytes):
    con = NamesData([])
    istream = io.BytesIO(separate_bytes)
    with pytest.raises(ct.CheckError, match='Ожидалась не пустая последовательность смещений'):
        con.parse_stream(istream)


@pytest.mark.parametrize(['bytes_', 'offsets'], [
    _(separate_bytes, separate_offsets, id='separate'),
])
def test_build(names, bytes_, offsets, ostream):
    built_offsets = []
    con = NamesData(built_offsets)
    check_build(con, names, bytes_, ostream)
    assert built_offsets == offsets


def test_build_no_paths_raises_check_error(separate_offsets, ostream):
    con = NamesData(separate_offsets)
    with pytest.raises(ct.CheckError, match='Ожидалась не пустая последовательность имен'):
        con.build_stream([], ostream)
