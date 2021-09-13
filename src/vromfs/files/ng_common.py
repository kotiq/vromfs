import construct as ct
from construct import len_, this
from blk.types import Name


RawCString = ct.NullTerminated(ct.GreedyBytes).compile()

NameCon = ct.ExprAdapter(
    RawCString,
    lambda obj, ctx: Name.of(obj),
    lambda obj, ctx: obj.encode()
).compile()

Names = ct.FocusedSeq(
    'names',
    'names_count' / ct.Rebuild(ct.VarInt, len_(this.names)),
    'names' / ct.Prefixed(ct.VarInt, NameCon[this.names_count])
).compile()
