import typing as t
import construct as ct


def check_parse(con: ct.Construct, istream: t.BinaryIO, bytes_len: int, expected_value: t.Any):
    parsed = con.parse_stream(istream)
    assert istream.tell() == bytes_len
    assert parsed == expected_value


def check_build(con: ct.Construct, value: t.Any, expected_bytes: bytes, ostream: t.BinaryIO):
    con.build_stream(value, ostream)
    assert ostream.tell() == len(expected_bytes)
    ostream.seek(0)
    built_bs = ostream.read()
    assert built_bs == expected_bytes
