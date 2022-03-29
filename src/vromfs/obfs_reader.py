import io
import typing as t
from .ranged_reader import RangedReader


def inplace_xor(buffer: bytearray, offset: int, size: int, key: t.Iterable[int]) -> None:
    it = iter(key)
    for i in range(offset, offset + min(len(buffer), size)):
        buffer[i] ^= next(it)


obfs_ks = tuple(map(bytes.fromhex, ('55aa55aa', '0ff00ff0', '55aa55aa', '48124812')))
head_ks = b''.join(obfs_ks)
tail_ks = b''.join(reversed(obfs_ks))


def deobfuscate(bs: bytes) -> bytes:
    buf = bytearray(bs)
    sz = len(bs)
    if sz >= 16:
        pos = 0
        inplace_xor(buf, pos, 16, head_ks)
        if sz >= 32:
            pos = (sz & 0x03ff_fffc) - 16
            inplace_xor(buf, pos, 16, tail_ks)

    return bytes(buf)


obfuscate = deobfuscate


class ObfsReader(io.IOBase):
    def __init__(self, wrapped: io.IOBase, size: int):
        self.wrapped = wrapped
        if size < 0:
            raise ValueError("invalid size: {}".format(size))
        self.size = size & 0x03ff_ffff

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return self.wrapped.seekable()

    def tell(self) -> int:
        return self.wrapped.tell()

    def seek(self, target: int, whence: int = io.SEEK_SET) -> int:
        return self.wrapped.seek(target, whence)

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = -1

        if size == 0:
            data = b''
        else:
            lpos = self.tell()
            if lpos > self.size:
                data = b''
            else:
                rpos = self.size if size == -1 else min(self.size, lpos + size)
                size = rpos - lpos
                data = self.wrapped.read(size)
                tpos = (self.size & 0x03ff_fffc) - 16
                if self.size >= 32:
                    # 0        16        tpos     tpos+16   self.size
                    # |--------|---------|--------|---------|
                    # |  head  |  body   |  tail  |  extra  |
                    buf = None
                    if lpos < 16:
                        buf = bytearray(data)
                        ks = head_ks[lpos:]
                        sz = min(size, len(ks))
                        inplace_xor(buf, 0, sz, ks)
                        if tpos < rpos:
                            if buf is None:
                                buf = bytearray(data)
                            ks = tail_ks[:rpos-tpos]
                            inplace_xor(buf, tpos-lpos, len(ks), ks)
                    elif lpos < tpos:
                        if tpos < rpos:
                            if buf is None:
                                buf = bytearray(data)
                            ks = tail_ks[:rpos-tpos]
                            inplace_xor(buf, tpos-lpos, len(ks), ks)
                    elif lpos < tpos+16:
                        if buf is None:
                            buf = bytearray(data)
                        ks = tail_ks[lpos-tpos:]
                        inplace_xor(buf, 0, len(ks), ks)
                    if buf is not None:
                        data = bytes(buf)
                elif self.size >= 16:
                    # 0        16     self.size
                    # |--------|------|
                    # |  head  | body |
                    if lpos < 16:
                        buf = bytearray(data)
                        ks = head_ks[lpos:]
                        inplace_xor(buf, 0, len(ks), ks)
                        data = bytes(buf)

        return data
