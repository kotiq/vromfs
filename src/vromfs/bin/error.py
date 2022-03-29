__all__ = [
    'BinError',
    'BinUnpackError',
    'BinPackError',
]


class BinError(Exception):
    pass


class BinUnpackError(BinError):
    pass


class BinPackError(BinError):
    pass
