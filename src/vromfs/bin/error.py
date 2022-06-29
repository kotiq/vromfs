__all__ = [
    'BinError',
    'BinPackError',
    'BinUnpackError',
]


class BinError(Exception):
    pass


class BinUnpackError(BinError):
    pass


class BinPackError(BinError):
    pass
