from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_virtual_desktop._desktop import Desktop


class Window:
    __slots__ = ("_hwnd", "_pid", "_title")

    def __init__(self, *, hwnd: int, pid: int, title: str = "") -> None:
        object.__setattr__(self, "_hwnd", hwnd)
        object.__setattr__(self, "_pid", pid)
        object.__setattr__(self, "_title", title)

    @property
    def hwnd(self) -> int:
        return self._hwnd

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def title(self) -> str:
        return self._title

    def move_to(self, desktop: Desktop | int) -> None:
        import pyvda  # type: ignore[import-untyped]
        from py_virtual_desktop._desktop import Desktop as DesktopCls, Desktops
        from py_virtual_desktop._exceptions import WindowMoveError

        if isinstance(desktop, int):
            idx = desktop
        elif isinstance(desktop, DesktopCls):
            idx = desktop.index
        else:
            raise TypeError(f"Expected Desktop or int, got {type(desktop).__name__}")

        Desktops().ensure(idx + 1)
        try:
            vd = pyvda.VirtualDesktop(number=idx + 1)
            view = pyvda.AppView(hwnd=self._hwnd)
            view.move(vd)
        except Exception as exc:
            raise WindowMoveError(
                str(exc), hwnd=self._hwnd, target_desktop=idx,
            ) from exc

    @classmethod
    def find(
        cls,
        *,
        pid: int | None = None,
        title: str | None = None,
        visible_only: bool = True,
    ) -> list[Window]:
        import win32gui  # type: ignore[import-untyped]
        import win32process  # type: ignore[import-untyped]

        compiled = re.compile(title) if title else None
        results: list[Window] = []

        def _callback(hwnd: int, _extra: object) -> None:
            if visible_only and not win32gui.IsWindowVisible(hwnd):
                return
            _, w_pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid is not None and w_pid != pid:
                return
            w_title = win32gui.GetWindowText(hwnd)
            if compiled is not None and not compiled.search(w_title):
                return
            results.append(Window(hwnd=hwnd, pid=w_pid, title=w_title))

        win32gui.EnumWindows(_callback, None)
        return results

    def __repr__(self) -> str:
        return f"Window({self._hwnd:#x}, pid={self._pid}, {self._title!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Window):
            return NotImplemented
        return self._hwnd == other._hwnd

    def __hash__(self) -> int:
        return hash(self._hwnd)

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError("Window objects are immutable.")
