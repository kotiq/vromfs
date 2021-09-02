"""Проверка Obfuscated."""

import io
import construct as ct
import pytest
from vromfs.parser import Obfuscated

ks = [bytes.fromhex(s) for s in ('55aa55aa', '0ff00ff0', '55aa55aa', '48124812')]

hk = b''.join(ks)
fk = b''.join(reversed(ks))


def xor(xs, ys):
    return bytes(x ^ y for x, y in zip(xs, ys))


data = b'abcdefghijklmnopqrstuvwxyz0123456789~!@#$%^&*()_+'


@pytest.mark.parametrize(['given', 'expected'], [
    pytest.param(data[:15], data[:15], id='lt16'),
    pytest.param(xor(data[:16], hk) + data[16:26], data[:26], id='ge16lt32'),
    pytest.param(xor(data[:16], hk) + data[16:32] + xor(data[32:48], fk) + data[48:49], data[:49], id='ge32'),
])
def test_obfuscated(given, expected):
    istream = io.BytesIO(given)
    buffer = Obfuscated(ct.Bytes(len(given))).parse_stream(istream)
    assert buffer == expected
