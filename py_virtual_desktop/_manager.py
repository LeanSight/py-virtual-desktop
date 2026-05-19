from __future__ import annotations

import ctypes
import ctypes.wintypes

from py_virtual_desktop._types import MoveResult
from py_virtual_desktop._desktop import ensure_desktop_count
from py_virtual_desktop._window import find_window_handles


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


def move_window(hwnd: int, desktop_index: int) -> MoveResult:
    import pyvda  # type: ignore[import-untyped]
    try:
        ensure_desktop_count(desktop_index + 1)
        vd = pyvda.VirtualDesktop(number=desktop_index + 1)
        view = pyvda.AppView(hwnd=hwnd)
        view.move(vd)
        return MoveResult(ok=True, desktop_index=desktop_index, windows_moved=1)
    except Exception as exc:
        return MoveResult(ok=False, desktop_index=desktop_index, error=str(exc))


def move_windows_by_pid(pid: int, desktop_index: int) -> MoveResult:
    import pyvda  # type: ignore[import-untyped]
    try:
        ensure_desktop_count(desktop_index + 1)
        vd = pyvda.VirtualDesktop(number=desktop_index + 1)
    except Exception as exc:
        return MoveResult(ok=False, desktop_index=desktop_index, error=str(exc))

    handles = find_window_handles(pid=pid)

    if not handles:
        fallback_hwnd = _get_main_window_handle(pid)
        if fallback_hwnd is None:
            return MoveResult(
                ok=False, desktop_index=desktop_index,
                error=f"No window handle found for PID {pid}",
            )
        try:
            view = pyvda.AppView(hwnd=fallback_hwnd)
            view.move(vd)
            return MoveResult(ok=True, desktop_index=desktop_index, windows_moved=1)
        except Exception as exc:
            return MoveResult(ok=False, desktop_index=desktop_index, error=str(exc))

    moved = 0
    last_error: str | None = None
    for wh in handles:
        try:
            view = pyvda.AppView(hwnd=wh.hwnd)
            view.move(vd)
            moved += 1
        except Exception as exc:
            last_error = str(exc)

    if moved == 0:
        return MoveResult(ok=False, desktop_index=desktop_index, error=last_error)
    return MoveResult(ok=True, desktop_index=desktop_index, windows_moved=moved)
