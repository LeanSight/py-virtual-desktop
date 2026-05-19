"""Acceptance tests for window movement."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_vd(number: int, guid: str = ""):
    vd = MagicMock()
    vd.number = number
    vd.id = guid or f"guid-{number}"
    vd.name = ""
    return vd


@pytest.fixture
def mock_all(monkeypatch):
    mock_pyvda = MagicMock()
    vds = [_make_mock_vd(1, "g1"), _make_mock_vd(2, "g2")]
    mock_pyvda.get_virtual_desktops.return_value = vds
    mock_pyvda.VirtualDesktop.side_effect = lambda number: vds[number - 1]
    mock_pyvda.VirtualDesktop.current.return_value = vds[0]
    mock_pyvda.VirtualDesktop.create.return_value = _make_mock_vd(3, "g3")
    mock_pyvda.AppView.side_effect = lambda hwnd: MagicMock()
    monkeypatch.setitem(sys.modules, "pyvda", mock_pyvda)

    win32gui = MagicMock()
    win32process = MagicMock()
    monkeypatch.setitem(sys.modules, "win32gui", win32gui)
    monkeypatch.setitem(sys.modules, "win32process", win32process)

    return mock_pyvda, win32gui, win32process


def _setup_windows(win32gui, win32process, windows):
    def fake_enum(cb, _):
        for hwnd, *_ in windows:
            cb(hwnd, None)

    win32gui.EnumWindows.side_effect = fake_enum
    win32gui.IsWindowVisible.return_value = True
    win32gui.GetWindowText.side_effect = lambda h: next(
        (t for hw, _, t, _ in windows if hw == h), ""
    )
    win32process.GetWindowThreadProcessId.side_effect = lambda h: (
        0, next((p for hw, p, _, _ in windows if hw == h), 0)
    )


class TestWindowMoveTo:
    def test_move_to_int(self, mock_all):
        """
        Given  a window with hwnd=100
        When   window.move_to(1) is called
        Then   the window is moved to desktop index 1
        """
        mock_pyvda, win32gui, win32process = mock_all
        _setup_windows(win32gui, win32process, [(100, 5000, "App", True)])

        from py_virtual_desktop import Window

        w = Window.find(pid=5000)[0]
        w.move_to(1)

        mock_pyvda.AppView.assert_called_with(hwnd=100)

    def test_move_to_desktop_object(self, mock_all):
        """
        Given  a window and a Desktop object
        When   window.move_to(desktop) is called
        Then   the window is moved to that desktop
        """
        mock_pyvda, win32gui, win32process = mock_all
        _setup_windows(win32gui, win32process, [(100, 5000, "App", True)])

        from py_virtual_desktop import Window, Desktops

        w = Window.find(pid=5000)[0]
        target = Desktops()[1]
        w.move_to(target)

        mock_pyvda.AppView.assert_called_with(hwnd=100)


class TestMoveWindows:
    def test_moves_all_windows_of_pid(self, mock_all):
        """
        Given  a process with PID 5000 having 2 windows
        When   move_windows(pid=5000, to=1) is called
        Then   both windows are moved, returning count=2
        """
        mock_pyvda, win32gui, win32process = mock_all
        _setup_windows(win32gui, win32process, [
            (200, 5000, "Win A", True),
            (201, 5000, "Win B", True),
        ])

        from py_virtual_desktop import move_windows

        count = move_windows(pid=5000, to=1)

        assert count == 2
        assert mock_pyvda.AppView.call_count == 2

    def test_raises_when_no_windows_found(self, mock_all):
        """
        Given  no windows exist for PID 9999
        When   move_windows(pid=9999, to=1) is called
        Then   WindowNotFoundError is raised
        """
        _, win32gui, win32process = mock_all
        win32gui.EnumWindows.side_effect = lambda cb, _: None

        from py_virtual_desktop import move_windows, WindowNotFoundError

        with pytest.raises(WindowNotFoundError, match="pid=9999"):
            move_windows(pid=9999, to=1)

    def test_fallback_to_main_window(self, mock_all):
        """
        Given  EnumWindows finds nothing but the process has a MainWindowHandle
        When   move_windows(pid=8000, to=1) is called with fallback=True
        Then   the main window is moved, returning count=1
        """
        mock_pyvda, win32gui, win32process = mock_all
        win32gui.EnumWindows.side_effect = lambda cb, _: None

        from py_virtual_desktop import _manager
        from py_virtual_desktop import move_windows

        with patch.object(_manager, "_get_main_window_handle", return_value=500):
            count = move_windows(pid=8000, to=1)

        assert count == 1
        mock_pyvda.AppView.assert_called_with(hwnd=500)
