"""Acceptance tests for Window.find() discovery."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

SAMPLE_WINDOWS = [
    (100, 1000, "Chrome - Google", True),
    (101, 1000, "Chrome - Settings", True),
    (102, 2000, "Notepad", True),
    (103, 3000, "Hidden", False),
]


@pytest.fixture
def mock_win32(monkeypatch):
    win32gui = MagicMock()
    win32process = MagicMock()

    def fake_enum(callback, _extra):
        for hwnd, *_ in SAMPLE_WINDOWS:
            callback(hwnd, None)

    win32gui.EnumWindows.side_effect = fake_enum
    win32gui.GetWindowText.side_effect = lambda h: next(
        (t for hw, _, t, _ in SAMPLE_WINDOWS if hw == h), ""
    )
    win32gui.IsWindowVisible.side_effect = lambda h: next(
        (v for hw, _, _, v in SAMPLE_WINDOWS if hw == h), False
    )
    win32process.GetWindowThreadProcessId.side_effect = lambda h: (
        0, next((p for hw, p, _, _ in SAMPLE_WINDOWS if hw == h), 0)
    )

    monkeypatch.setitem(sys.modules, "win32gui", win32gui)
    monkeypatch.setitem(sys.modules, "win32process", win32process)


class TestWindowFind:
    def test_find_by_pid(self, mock_win32):
        """
        Given  3 visible windows, 2 belonging to PID 1000
        When   Window.find(pid=1000) is called
        Then   2 Window objects are returned with correct hwnd, pid, title
        """
        from py_virtual_desktop import Window

        windows = Window.find(pid=1000)

        assert len(windows) == 2
        assert all(w.pid == 1000 for w in windows)
        titles = {w.title for w in windows}
        assert "Chrome - Google" in titles
        assert "Chrome - Settings" in titles

    def test_find_by_title(self, mock_win32):
        """
        Given  3 visible windows
        When   Window.find(title="Settings") is called
        Then   only the matching window is returned
        """
        from py_virtual_desktop import Window

        windows = Window.find(title="Settings")

        assert len(windows) == 1
        assert windows[0].title == "Chrome - Settings"

    def test_find_excludes_invisible_by_default(self, mock_win32):
        """
        Given  1 invisible window with PID 3000
        When   Window.find(pid=3000) is called
        Then   no windows are returned
        """
        from py_virtual_desktop import Window

        assert len(Window.find(pid=3000)) == 0

    def test_find_includes_invisible_when_requested(self, mock_win32):
        """
        Given  1 invisible window with PID 3000
        When   Window.find(pid=3000, visible_only=False) is called
        Then   the window is returned
        """
        from py_virtual_desktop import Window

        windows = Window.find(pid=3000, visible_only=False)
        assert len(windows) == 1
        assert windows[0].title == "Hidden"

    def test_window_repr(self, mock_win32):
        """
        Given  a Window with hwnd=102, pid=2000, title='Notepad'
        When   repr() is called
        Then   it shows Window(0x66, pid=2000, 'Notepad')
        """
        from py_virtual_desktop import Window

        w = Window.find(pid=2000)[0]
        assert "0x66" in repr(w)
        assert "2000" in repr(w)
        assert "Notepad" in repr(w)
