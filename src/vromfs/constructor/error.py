class ConstructError(Exception):
    pass


class UnpackError(ConstructError):
    pass


class PackError(ConstructError):
    pass
