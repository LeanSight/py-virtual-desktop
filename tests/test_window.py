from __future__ import annotations

import re
from unittest.mock import MagicMock, patch, call

import pytest

from py_virtual_desktop._types import WindowHandle


def _make_enum_windows(windows: list[tuple[int, int, str, bool]]):
    """Return a fake EnumWindows that calls the callback with the given windows.

    Each tuple is (hwnd, pid, title, is_visible).
    """
    def fake_enum(callback, _extra):
        for hwnd, _pid, _title, _vis in windows:
            callback(hwnd, None)
    return fake_enum


def _make_get_pid(windows: list[tuple[int, int, str, bool]]):
    pid_map = {hwnd: pid for hwnd, pid, _, _ in windows}
    def fake_get_pid(hwnd):
        return (0, pid_map.get(hwnd, 0))
    return fake_get_pid


def _make_get_title(windows: list[tuple[int, int, str, bool]]):
    title_map = {hwnd: title for hwnd, _, title, _ in windows}
    def fake_get_title(hwnd):
        return title_map.get(hwnd, "")
    return fake_get_title


def _make_is_visible(windows: list[tuple[int, int, str, bool]]):
    vis_map = {hwnd: vis for hwnd, _, _, vis in windows}
    def fake_is_visible(hwnd):
        return vis_map.get(hwnd, False)
    return fake_is_visible


SAMPLE_WINDOWS = [
    (100, 1000, "Chrome - Google", True),
    (101, 1000, "Chrome - Settings", True),
    (102, 2000, "Notepad", True),
    (103, 3000, "Hidden Thing", False),
    (104, 1000, "", True),
]


@pytest.fixture
def mock_win32(monkeypatch):
    win32gui = MagicMock()
    win32process = MagicMock()

    win32gui.EnumWindows.side_effect = _make_enum_windows(SAMPLE_WINDOWS)
    win32gui.GetWindowText.side_effect = _make_get_title(SAMPLE_WINDOWS)
    win32gui.IsWindowVisible.side_effect = _make_is_visible(SAMPLE_WINDOWS)
    win32process.GetWindowThreadProcessId.side_effect = _make_get_pid(SAMPLE_WINDOWS)

    monkeypatch.setitem(__import__("sys").modules, "win32gui", win32gui)
    monkeypatch.setitem(__import__("sys").modules, "win32process", win32process)

    import importlib
    import py_virtual_desktop._window as mod
    importlib.reload(mod)
    return mod


class TestFindWindowHandles:
    def test_filter_by_pid(self, mock_win32):
        results = mock_win32.find_window_handles(pid=1000)
        assert len(results) == 3
        assert all(wh.pid == 1000 for wh in results)

    def test_filter_by_title_pattern(self, mock_win32):
        results = mock_win32.find_window_handles(title_pattern="Chrome")
        assert len(results) == 2
        titles = {wh.title for wh in results}
        assert "Chrome - Google" in titles
        assert "Chrome - Settings" in titles

    def test_filter_by_pid_and_title(self, mock_win32):
        results = mock_win32.find_window_handles(pid=1000, title_pattern="Settings")
        assert len(results) == 1
        assert results[0].title == "Chrome - Settings"

    def test_invisible_excluded_by_default(self, mock_win32):
        results = mock_win32.find_window_handles(pid=3000)
        assert len(results) == 0

    def test_invisible_included_when_requested(self, mock_win32):
        results = mock_win32.find_window_handles(pid=3000, visible_only=False)
        assert len(results) == 1
        assert results[0].title == "Hidden Thing"

    def test_no_filters_returns_all_visible(self, mock_win32):
        results = mock_win32.find_window_handles()
        assert len(results) == 4

    def test_returns_window_handle_dataclass(self, mock_win32):
        results = mock_win32.find_window_handles(pid=2000)
        assert len(results) == 1
        wh = results[0]
        assert isinstance(wh, WindowHandle)
        assert wh.hwnd == 102
        assert wh.pid == 2000
        assert wh.title == "Notepad"
