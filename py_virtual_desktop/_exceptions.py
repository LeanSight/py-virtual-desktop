from __future__ import annotations


class VirtualDesktopError(Exception):
    pass


class DesktopNotFoundError(VirtualDesktopError, IndexError):
    def __init__(self, index: int) -> None:
        self.index = index
        super().__init__(f"Desktop index {index} is out of range.")


class WindowMoveError(VirtualDesktopError, OSError):
    def __init__(
        self,
        message: str,
        *,
        pid: int | None = None,
        hwnd: int | None = None,
        target_desktop: int = 0,
        windows_moved: int = 0,
    ) -> None:
        self.pid = pid
        self.hwnd = hwnd
        self.target_desktop = target_desktop
        self.windows_moved = windows_moved
        super().__init__(message)


class WindowNotFoundError(VirtualDesktopError, LookupError):
    def __init__(
        self,
        *,
        pid: int | None = None,
        title: str | None = None,
    ) -> None:
        self.pid = pid
        self.title = title
        parts = []
        if pid is not None:
            parts.append(f"pid={pid}")
        if title is not None:
            parts.append(f"title={title!r}")
        detail = ", ".join(parts) or "no criteria"
        super().__init__(f"No windows found matching {detail}.")
