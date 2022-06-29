from io import IOBase, SEEK_CUR, SEEK_END, SEEK_SET

__all__ = [
    'RangedReader',
]


class RangedReader(IOBase):
    def __init__(self, wrapped: IOBase, offset: int, size: int):
        if offset < 0:
            raise ValueError("invalid offset: {}".format(offset))
        if size < 0:
            raise ValueError("invalid size: {}".format(size))
        self.wrapped = wrapped
        self.offset = offset
        self.size = size
        self.pos = 0

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return self.wrapped.seekable()

    def seek(self, target: int, whence: int = SEEK_SET) -> int:
        if whence == SEEK_SET:
            if target < 0:
                raise ValueError('negative seek value {}'.format(target))
            self.pos = target
        else:
            if whence == SEEK_CUR:
                pos = self.pos + target
            elif whence == SEEK_END:
                pos = self.size + target
            else:
                raise ValueError('invalid whence ({}, should be {}, {} or {})'.
                                 format(whence, SEEK_SET, SEEK_CUR, SEEK_END))
            self.pos = 0 if pos < 0 else pos

        return self.pos

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = -1
        if size == 0:
            data = b''
        else:
            pos = self.tell()
            if pos >= self.size:
                data = b''
            else:
                self.wrapped.seek(self.offset + pos)
                if size == -1 or pos + size > self.size:
                    size = self.size - pos
                data = self.wrapped.read(size)
                self.pos += len(data)

        return data
