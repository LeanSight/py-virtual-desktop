from __future__ import annotations

from py_virtual_desktop._types import Desktop


def _wrap(vd: object) -> Desktop:
    return Desktop(index=vd.number - 1, id=str(vd.id), name=str(vd.name))


def get_desktop_count() -> int:
    import pyvda  # type: ignore[import-untyped]
    return len(pyvda.get_virtual_desktops())


def get_desktop(index: int) -> Desktop:
    import pyvda  # type: ignore[import-untyped]
    if index < 0:
        raise ValueError("Desktop index must be non-negative.")
    vd = pyvda.VirtualDesktop(number=index + 1)
    return _wrap(vd)


def get_current_desktop() -> Desktop:
    import pyvda  # type: ignore[import-untyped]
    return _wrap(pyvda.VirtualDesktop.current())


def create_desktop() -> Desktop:
    import pyvda  # type: ignore[import-untyped]
    return _wrap(pyvda.VirtualDesktop.create())


def ensure_desktop_count(n: int) -> list[Desktop]:
    import pyvda  # type: ignore[import-untyped]
    if n < 1:
        raise ValueError("Desktop count must be at least 1.")
    current = pyvda.get_virtual_desktops()
    for _ in range(n - len(current)):
        pyvda.VirtualDesktop.create()
    return [_wrap(vd) for vd in pyvda.get_virtual_desktops()]


def switch_desktop(index: int) -> None:
    import pyvda  # type: ignore[import-untyped]
    if index < 0:
        raise ValueError("Desktop index must be non-negative.")
    vd = pyvda.VirtualDesktop(number=index + 1)
    vd.go()


def remove_desktop(index: int) -> None:
    import pyvda  # type: ignore[import-untyped]
    if index < 0:
        raise ValueError("Desktop index must be non-negative.")
    vd = pyvda.VirtualDesktop(number=index + 1)
    vd.remove()
