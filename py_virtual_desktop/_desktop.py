from __future__ import annotations

from typing import Iterator

from py_virtual_desktop._exceptions import DesktopNotFoundError


class Desktop:
    __slots__ = ("_index", "_id", "_name")

    def __init__(self, *, index: int, id: str, name: str = "") -> None:
        object.__setattr__(self, "_index", index)
        object.__setattr__(self, "_id", id)
        object.__setattr__(self, "_name", name)

    @property
    def index(self) -> int:
        return self._index

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_active(self) -> bool:
        import pyvda  # type: ignore[import-untyped]
        current = pyvda.VirtualDesktop.current()
        return str(current.id) == self._id

    def activate(self) -> None:
        import pyvda  # type: ignore[import-untyped]
        vd = pyvda.VirtualDesktop(number=self._index + 1)
        vd.go()

    def remove(self) -> None:
        import pyvda  # type: ignore[import-untyped]
        vd = pyvda.VirtualDesktop(number=self._index + 1)
        vd.remove()

    def __repr__(self) -> str:
        if self._name:
            return f"Desktop({self._index}, {self._name!r})"
        return f"Desktop({self._index})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Desktop):
            return NotImplemented
        return self._id == other._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("Desktop objects are immutable.")


def _wrap(vd: object) -> Desktop:
    return Desktop(index=vd.number - 1, id=str(vd.id), name=str(vd.name))


class Desktops:
    def __len__(self) -> int:
        import pyvda  # type: ignore[import-untyped]
        return len(pyvda.get_virtual_desktops())

    def __iter__(self) -> Iterator[Desktop]:
        import pyvda  # type: ignore[import-untyped]
        for vd in pyvda.get_virtual_desktops():
            yield _wrap(vd)

    def __getitem__(self, index: int) -> Desktop:
        import pyvda  # type: ignore[import-untyped]
        count = len(pyvda.get_virtual_desktops())
        if index < 0:
            index = count + index
        if index < 0 or index >= count:
            raise DesktopNotFoundError(index)
        vd = pyvda.VirtualDesktop(number=index + 1)
        return _wrap(vd)

    def __contains__(self, item: Desktop | int) -> bool:
        count = len(self)
        if isinstance(item, int):
            return 0 <= item < count
        if isinstance(item, Desktop):
            return 0 <= item.index < count
        return False

    @property
    def current(self) -> Desktop:
        import pyvda  # type: ignore[import-untyped]
        return _wrap(pyvda.VirtualDesktop.current())

    def create(self) -> Desktop:
        import pyvda  # type: ignore[import-untyped]
        return _wrap(pyvda.VirtualDesktop.create())

    def ensure(self, count: int) -> list[Desktop]:
        import pyvda  # type: ignore[import-untyped]
        if count < 1:
            raise ValueError("Desktop count must be at least 1.")
        current = pyvda.get_virtual_desktops()
        for _ in range(count - len(current)):
            pyvda.VirtualDesktop.create()
        return [_wrap(vd) for vd in pyvda.get_virtual_desktops()]

    def __repr__(self) -> str:
        return f"Desktops({list(self)})"
