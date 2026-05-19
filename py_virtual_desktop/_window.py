from __future__ import annotations

import re

from py_virtual_desktop._types import WindowHandle


def find_window_handles(
    pid: int | None = None,
    title_pattern: str | None = None,
    visible_only: bool = True,
) -> list[WindowHandle]:
    import win32gui  # type: ignore[import-untyped]
    import win32process  # type: ignore[import-untyped]

    compiled = re.compile(title_pattern) if title_pattern else None
    results: list[WindowHandle] = []

    def _callback(hwnd: int, _extra: object) -> None:
        if visible_only and not win32gui.IsWindowVisible(hwnd):
            return
        _, w_pid = win32process.GetWindowThreadProcessId(hwnd)
        if pid is not None and w_pid != pid:
            return
        title = win32gui.GetWindowText(hwnd)
        if compiled is not None and not compiled.search(title):
            return
        results.append(WindowHandle(hwnd=hwnd, pid=w_pid, title=title))

    win32gui.EnumWindows(_callback, None)
    return results
