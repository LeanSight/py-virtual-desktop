from __future__ import annotations

import ctypes
import ctypes.wintypes

from py_virtual_desktop._desktop import Desktops
from py_virtual_desktop._window import Window
from py_virtual_desktop._exceptions import WindowMoveError, WindowNotFoundError


def _get_main_window_handle(pid: int) -> int | None:
    result: list[int] = []

    @ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    def _cb(hwnd, _lparam):
        tid_pid = ctypes.wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(tid_pid))
        if tid_pid.value == pid and ctypes.windll.user32.IsWindowVisible(hwnd):
            result.append(hwnd)
            return False
        return True

    ctypes.windll.user32.EnumWindows(_cb, 0)
    return result[0] if result else None


def move_windows(
    *,
    pid: int,
    to: object,
    fallback: bool = True,
) -> int:
    from py_virtual_desktop._desktop import Desktop

    if isinstance(to, int):
        target_index = to
    elif isinstance(to, Desktop):
        target_index = to.index
    else:
        raise TypeError(f"Expected Desktop or int for 'to', got {type(to).__name__}")

    Desktops().ensure(target_index + 1)

    import pyvda  # type: ignore[import-untyped]
    vd = pyvda.VirtualDesktop(number=target_index + 1)

    handles = Window.find(pid=pid)

    if not handles and fallback:
        fallback_hwnd = _get_main_window_handle(pid)
        if fallback_hwnd is not None:
            try:
                view = pyvda.AppView(hwnd=fallback_hwnd)
                view.move(vd)
                return 1
            except Exception as exc:
                raise WindowMoveError(
                    str(exc), pid=pid, hwnd=fallback_hwnd,
                    target_desktop=target_index,
                ) from exc

    if not handles:
        raise WindowNotFoundError(pid=pid)

    moved = 0
    last_exc: Exception | None = None
    for w in handles:
        try:
            view = pyvda.AppView(hwnd=w.hwnd)
            view.move(vd)
            moved += 1
        except Exception as exc:
            last_exc = exc

    if moved == 0 and last_exc is not None:
        raise WindowMoveError(
            str(last_exc), pid=pid, target_desktop=target_index,
        ) from last_exc

    return moved
