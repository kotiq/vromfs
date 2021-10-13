from pathlib import Path
import typing as t
import construct as ct
import pytest
from pytest_lazyfixture import lazy_fixture
from vromfs.vromfs.constructor import NamesData
from test_vromfs import _test_parse, _test_build


separate_names_data_bs = lazy_fixture('separate_names_data_bs')
separate_names_data_istream = lazy_fixture('separate_names_data_istream')
separate_offsets = lazy_fixture('separate_offsets')

reversed_separate_names_data_bs = lazy_fixture('reversed_separate_names_data_bs')
reversed_separate_names_data_istream = lazy_fixture('reversed_separate_names_data_istream')
reversed_separate_offsets = lazy_fixture('reversed_separate_offsets')

overlapping_names_data_istream = lazy_fixture('overlapping_names_data_istream')
overlapping_names_data_bs = lazy_fixture('overlapping_names_data_bs')
overlapping_offsets = lazy_fixture('overlapping_offsets')


@pytest.mark.parametrize(['names_data_istream', 'names_data_bs', 'offsets'], [
    pytest.param(
        separate_names_data_istream,
        separate_names_data_bs,
        separate_offsets,
        id='separate'
    ),
    pytest.param(
        reversed_separate_names_data_istream,
        reversed_separate_names_data_bs,
        reversed_separate_offsets,
        id='reversed_separate'
    ),
    pytest.param(
        overlapping_names_data_istream,
        overlapping_names_data_bs,
        overlapping_offsets,
        id='overlapping'
    ),
])
def test_parse(names_data_istream: t.BinaryIO, names_data_bs: bytes, offsets: t.Sequence[int], names: t.Sequence[Path]):
    con = NamesData(offsets)
    _test_parse(con, names_data_istream, names_data_bs, names)


def test_parse_no_offsets_raises_check_error(separate_names_data_istream):
    con = NamesData([])
    with pytest.raises(ct.CheckError, match='Ожидалась непустая последовательность смещений'):
        con.parse_stream(separate_names_data_istream)


@pytest.mark.parametrize(['names_data_bs', 'offsets'], [
    pytest.param(separate_names_data_bs, separate_offsets, id='separate'),
])
def test_build(names: t.Sequence[Path], names_data_bs: bytes, offsets: t.Sequence[int], ostream: t.BinaryIO):
    built_offsets = []
    con = NamesData(built_offsets)
    _test_build(con, names, names_data_bs, ostream)
    assert built_offsets == offsets


def test_build_no_paths_raises_check_error(separate_offsets, ostream):
    con = NamesData(separate_offsets)
    with pytest.raises(ct.CheckError, match='Ожидалась непустая последовательность имен'):
        con.build_stream([], ostream)
