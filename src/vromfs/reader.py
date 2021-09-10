import io
import typing as t

# todo: BufferedIOBase iface
class RangedReader:
    def __init__(self, wrapped: t.Union['RangedReader', io.BufferedIOBase], from_: int, to: int):
        self.wrapped = wrapped
        self.from_ = from_
        self.to = to
        self.pos = 0

    def seek(self, target: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            if target < 0:
                raise ValueError('negative seek value {}'.format(target))
            self.pos = target
        else:
            if whence == io.SEEK_CUR:
                pos = self.pos + target
            elif whence == io.SEEK_END:
                pos = (self.to - self.from_) + target
            else:
                raise ValueError('invalid whence ({}, should be {}, {} or {})'.
                                 format(whence, io.SEEK_SET, io.SEEK_CUR, io.SEEK_END))
            self.pos = 0 if pos < 0 else pos

        return self.pos

    def tell(self) -> int:
        return self.seek(0, io.SEEK_CUR)

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = -1

        pos = self.tell()
        if size == 0:
            data = b''
        else:
            apos = self.from_ + pos
            if apos >= self.to:
                data = b''
            else:
                self.wrapped.seek(apos)
                if size == -1 or apos + size > self.to:
                    size = self.to - apos
                data = self.wrapped.read(size)
                self.pos += len(data)

        return data
