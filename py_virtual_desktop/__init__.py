from py_virtual_desktop._types import Desktop, WindowHandle, MoveResult
from py_virtual_desktop._compat import is_available
from py_virtual_desktop._window import find_window_handles
from py_virtual_desktop._desktop import (
    get_desktop_count,
    get_desktop,
    get_current_desktop,
    create_desktop,
    ensure_desktop_count,
    switch_desktop,
    remove_desktop,
)
from py_virtual_desktop._manager import move_window, move_windows_by_pid

__all__ = [
    "Desktop",
    "WindowHandle",
    "MoveResult",
    "is_available",
    "find_window_handles",
    "get_desktop_count",
    "get_desktop",
    "get_current_desktop",
    "create_desktop",
    "ensure_desktop_count",
    "switch_desktop",
    "remove_desktop",
    "move_window",
    "move_windows_by_pid",
]
