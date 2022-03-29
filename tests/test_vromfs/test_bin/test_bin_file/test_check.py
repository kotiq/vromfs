from vromfs.bin import BinFile


def test_check_checked(checked: BinFile):
    assert checked.check()


def test_check_not_checked(not_checked: BinFile):
    assert not_checked.check() is None
