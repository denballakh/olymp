from __future__ import annotations
import typing as t
import collections.abc as t_abc


def c3[X](x: X, get_bases: t_abc.Callable[[X], list[X]]) -> list[X]:
    def merge(mros: list[list[X | None]]) -> list[X | None]:
        if not any(mros):
            return []
        for candidate, *_ in mros:
            if all(id(candidate) not in map(id, tail) for _, *tail in mros):
                return [candidate] + merge(
                    [tail if head is candidate else [head, *tail] for head, *tail in mros]
                )
        else:
            raise TypeError("no legal mro")

    def _c3(x: X) -> list[X | None]:
        if bases := get_bases(x):
            return [x] + merge([_c3(base) for base in bases])
        else:
            return [x, None]

    m = _c3(x)
    assert m[-1] is None
    assert all(x is not None for x in m[:-1])
    return m[:-1]  # type: ignore


def test():
    # fmt: off
    assert c3(1, {1:[],2:[],3:[1,2]}.get) == [1]
    assert c3(2, {1:[],2:[],3:[1,2]}.get) == [2]
    assert c3(3, {1:[],2:[],3:[1,2]}.get) == [3, 1, 2]

    assert c3(1, {1:[],2:[],3:[],4:[1,2],5:[2,3],6:[3,1]}.get) == [1]
    assert c3(4, {1:[],2:[],3:[],4:[1,2],5:[2,3],6:[3,1]}.get) == [4, 1, 2]
    assert c3(5, {1:[],2:[],3:[],4:[1,2],5:[2,3],6:[3,1]}.get) == [5, 2, 3]
    assert c3(6, {1:[],2:[],3:[],4:[1,2],5:[2,3],6:[3,1]}.get) == [6, 3, 1]
    try:
        c3(7, {1:[],2:[],3:[],4:[1,2],5:[2,3],6:[3,1],7:[4,5,6]}.get)
    except TypeError:
        pass # ok
    else:
        raise Exception(f"expected error")

    assert c3(7, {1:[],2:[],3:[],4:[1,2],5:[2,3],6:[1,3],7:[4,5,6]}.get) == [7, 4, 5, 6, 1, 2, 3]
    # fmt: on

    return True


assert test()


class C[K, V]:
    __slots__ = ('__C_d__', '__C_b__')
    __C_d__: dict[K, V]
    __C_b__: list[t.Self]

    def mro(self) -> list[t.Self]:
        return c3(self, lambda self: self.__C_b__)

    def __repr__(self) -> str:
        # return f'{self.__class__.__qualname__}({self.__C_d__}, {self.__C_b__})'
        return f'{self.__class__.__qualname__}({dict(self.items())})'

    def __init__(self, d: dict[K, V] | None = None, b: list[t.Self] | None = None):
        self.__C_d__ = d if d is not None else {}
        self.__C_b__ = b if b is not None else []

    def __getitem__(self, key: K) -> t.Any:
        for c in self.mro():
            if key in c.__C_d__:
                return c.__C_d__[key]
        raise KeyError(key)

    # at = __getitem__

    def __setitem__(self, key: K, val: V) -> None:
        self.__C_d__[key] = val

    def __contains__(self, key: K) -> bool:
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    @t.overload
    def get(self, key: K, default: None = None) -> V | None: ...
    @t.overload
    def get[D](self, key: K, default: D) -> V | D: ...
    def get[D](self, key: K, default: D | None = None) -> V | D | None:
        try:
            return self[key]
        except KeyError:
            return default

    def items(self):
        keys = set[K]()
        for c in self.mro():
            for k, v in c.__C_d__.items():
                if k not in keys:
                    keys.add(k)
                    yield k, v

    def dump(self) -> dict[K, V]:
        return dump(self)

def dump(self):
    if isinstance(self, (C, dict)):
        return {k: dump(v) for k, v in self.items()}
    if isinstance(self, (list, tuple, set)):
        return [dump(x) for x in self]
    return self
