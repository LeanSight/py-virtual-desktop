from py_virtual_desktop._desktop import Desktop, Desktops
from py_virtual_desktop._window import Window
from py_virtual_desktop._exceptions import (
    VirtualDesktopError,
    DesktopNotFoundError,
    WindowMoveError,
    WindowNotFoundError,
)
from py_virtual_desktop._manager import move_windows
from py_virtual_desktop._compat import is_available

__all__ = [
    "Desktop",
    "Desktops",
    "Window",
    "VirtualDesktopError",
    "DesktopNotFoundError",
    "WindowMoveError",
    "WindowNotFoundError",
    "move_windows",
    "is_available",
]
