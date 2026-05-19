from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Desktop:
    index: int
    id: str
    name: str = ""


@dataclass(frozen=True)
class WindowHandle:
    hwnd: int
    pid: int
    title: str = ""


@dataclass(frozen=True)
class MoveResult:
    ok: bool
    desktop_index: int
    windows_moved: int = 0
    error: str | None = None
