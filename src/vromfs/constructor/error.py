class ConstructError(Exception):
    pass


class UnpackError(ConstructError):
    pass


class DecompressionError(UnpackError):
    pass


class PackError(ConstructError):
    pass
