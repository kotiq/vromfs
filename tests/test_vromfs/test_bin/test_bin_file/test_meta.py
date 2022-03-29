from vromfs.bin import BinFile


def test_checked_checked(checked: BinFile):
    assert checked.checked


def test_checked_not_checked(not_checked: BinFile):
    assert not not_checked.checked


def test_digest_checked(checked: BinFile):
    assert isinstance(checked.digest, bytes)


def test_digest_not_checked(not_checked: BinFile):
    assert not_checked.digest is None


def test_compressed_compressed(compressed: BinFile):
    assert compressed.compressed


def test_compressed_not_compressed(not_compressed: BinFile):
    assert not not_compressed.compressed
