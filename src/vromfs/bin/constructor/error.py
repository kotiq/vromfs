class BinConstructError(Exception):
    pass


class BinUnpackError(BinConstructError):
    pass


class BinDecompressionError(BinUnpackError):
    pass


class BinPackError(BinConstructError):
    pass
