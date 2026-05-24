from __future__ import annotations

import ctypes
import ctypes.wintypes
import subprocess
import time

from py_virtual_desktop._desktop import Desktops
from py_virtual_desktop._window import Window
from py_virtual_desktop._exceptions import WindowMoveError, WindowNotFoundError


def _get_child_pids(parent_pid: int) -> list[int]:
    TH32CS_SNAPPROCESS = 0x00000002
    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    class PROCESSENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize", ctypes.wintypes.DWORD),
            ("cntUsage", ctypes.wintypes.DWORD),
            ("th32ProcessID", ctypes.wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", ctypes.wintypes.DWORD),
            ("cntThreads", ctypes.wintypes.DWORD),
            ("th32ParentProcessID", ctypes.wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", ctypes.wintypes.DWORD),
            ("szExeFile", ctypes.c_char * 260),
        ]

    snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot == INVALID_HANDLE_VALUE:
        return []

    children: list[int] = []
    entry = PROCESSENTRY32()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32)

    try:
        if ctypes.windll.kernel32.Process32First(snapshot, ctypes.byref(entry)):
            while True:
                if entry.th32ParentProcessID == parent_pid:
                    children.append(entry.th32ProcessID)
                if not ctypes.windll.kernel32.Process32Next(snapshot, ctypes.byref(entry)):
                    break
    finally:
        ctypes.windll.kernel32.CloseHandle(snapshot)

    return children


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
    original = pyvda.VirtualDesktop.current()
    vd = pyvda.VirtualDesktop(number=target_index + 1)

    handles = Window.find(pid=pid)

    try:
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
    finally:
        original.go()


def launch_on(
    cmd: list[str] | str,
    *,
    to: object,
    timeout: float = 10.0,
    poll_interval: float = 0.2,
) -> subprocess.Popen:
    import pyvda  # type: ignore[import-untyped]
    from py_virtual_desktop._desktop import Desktop

    if isinstance(to, int):
        target_index = to
    elif isinstance(to, Desktop):
        target_index = to.index
    else:
        raise TypeError(f"Expected Desktop or int for 'to', got {type(to).__name__}")

    Desktops().ensure(target_index + 1)

    original = pyvda.VirtualDesktop.current()
    target_vd = pyvda.VirtualDesktop(number=target_index + 1)

    target_vd.go()
    try:
        proc = subprocess.Popen(cmd)

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            windows = Window.find(pid=proc.pid)
            if not windows:
                for child_pid in _get_child_pids(proc.pid):
                    windows = Window.find(pid=child_pid)
                    if windows:
                        break
            if windows:
                return proc
            time.sleep(poll_interval)

        raise WindowNotFoundError(pid=proc.pid)
    finally:
        original.go()
