import io
import typing as t


class RangedReader:
    def __init__(self, wrapped: io.BufferedIOBase, from_: int, to: int):
        self.wrapped = wrapped
        self.from_ = from_
        self.to = to
        self.pos = 0

    def seek(self, target, whence=io.SEEK_SET):
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


def trace_reader(*funcnames: str):
    def cls_dec(cls: t.Type):
        init = cls.__init__

        def __init__(self, *args, log=None, **kwargs):
            init(self, *args, **kwargs)
            self.log = log

        cls.__init__ = __init__

        def trace_meth(meth):
            def meth_(self, *args, **kwargs):
                returns = meth(self, *args, *kwargs)
                if self.log:
                    print(f'{meth.__qualname__}: self={self}, args={args}, kwargs={kwargs}, returns={returns}',
                          file=self.log)
                return returns

            return meth_

        for funcname in funcnames:
            setattr(cls, funcname, trace_meth(getattr(cls, funcname)))

        return cls

    return cls_dec


@trace_reader('close',
              'closed',
              'detach',
              'fileno',
              'flush',
              'getbuffer',
              'getvalue',
              'isatty',
              'read',
              'read1',
              'readable',
              'readinto',
              'readinto1',
              'readline',
              'readlines',
              'seek',
              'seekable',
              'tell',
              'truncate',
              'writable',
              'write',
              'writelines')
class ProbeReader(io.BytesIO):
    pass
