import typing as t
import construct as ct


def _test_parse(con: ct.Construct, istream: t.BinaryIO, bs: bytes, expected: t.Any):
    parsed = con.parse_stream(istream)
    assert istream.tell() == len(bs)
    assert parsed == expected


def _test_build(con: ct.Construct, value: t.Any, expected_bs: bytes, ostream: t.BinaryIO):
    con.build_stream(value, ostream)
    assert ostream.tell() == len(expected_bs)
    ostream.seek(0)
    built_bs = ostream.read()
    assert built_bs == expected_bs
