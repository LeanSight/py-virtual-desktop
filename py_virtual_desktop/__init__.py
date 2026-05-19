from py_virtual_desktop._desktop import Desktop, Desktops
from py_virtual_desktop._exceptions import (
    VirtualDesktopError,
    DesktopNotFoundError,
    WindowMoveError,
    WindowNotFoundError,
)
from py_virtual_desktop._compat import is_available

__all__ = [
    "Desktop",
    "Desktops",
    "VirtualDesktopError",
    "DesktopNotFoundError",
    "WindowMoveError",
    "WindowNotFoundError",
    "is_available",
]
