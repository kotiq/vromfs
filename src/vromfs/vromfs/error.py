__all__ = [
    'VromfsError',
    'VromfsPackError',
    'VromfsUnpackError',
]


class VromfsError(Exception):
    pass


class VromfsUnpackError(VromfsError):
    pass


class VromfsPackError(VromfsError):
    pass
