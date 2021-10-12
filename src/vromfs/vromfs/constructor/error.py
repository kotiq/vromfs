class VromfsConstructError(Exception):
    pass


class VromfsUnpackError(VromfsConstructError):
    pass


class VromfsDecompressionError(VromfsUnpackError):
    pass


class VromfsPackError(VromfsConstructError):
    pass
