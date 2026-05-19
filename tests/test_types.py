from __future__ import annotations

import pytest

from py_virtual_desktop import Desktop, WindowHandle, MoveResult


class TestDesktop:
    def test_frozen(self):
        d = Desktop(index=0, id="abc-123")
        with pytest.raises(AttributeError):
            d.index = 1  # type: ignore[misc]

    def test_defaults(self):
        d = Desktop(index=0, id="abc")
        assert d.name == ""

    def test_fields(self):
        d = Desktop(index=2, id="guid-x", name="Work")
        assert d.index == 2
        assert d.id == "guid-x"
        assert d.name == "Work"


class TestWindowHandle:
    def test_frozen(self):
        wh = WindowHandle(hwnd=123, pid=456)
        with pytest.raises(AttributeError):
            wh.hwnd = 0  # type: ignore[misc]

    def test_defaults(self):
        wh = WindowHandle(hwnd=1, pid=2)
        assert wh.title == ""

    def test_fields(self):
        wh = WindowHandle(hwnd=0xDEAD, pid=42, title="Notepad")
        assert wh.hwnd == 0xDEAD
        assert wh.pid == 42
        assert wh.title == "Notepad"


class TestMoveResult:
    def test_success(self):
        r = MoveResult(ok=True, desktop_index=1, windows_moved=3)
        assert r.ok is True
        assert r.desktop_index == 1
        assert r.windows_moved == 3
        assert r.error is None

    def test_failure(self):
        r = MoveResult(ok=False, desktop_index=1, error="no handles")
        assert r.ok is False
        assert r.windows_moved == 0
        assert r.error == "no handles"

    def test_frozen(self):
        r = MoveResult(ok=True, desktop_index=0)
        with pytest.raises(AttributeError):
            r.ok = False  # type: ignore[misc]
