from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

from py_virtual_desktop._types import Desktop, WindowHandle, MoveResult


def _make_mock_vd(number: int, guid: str = ""):
    vd = MagicMock()
    vd.number = number
    vd.id = guid or f"guid-{number}"
    vd.name = ""
    return vd


@pytest.fixture
def mock_deps(monkeypatch):
    mock_pyvda = MagicMock()
    desktops = [_make_mock_vd(1, "g1"), _make_mock_vd(2, "g2"), _make_mock_vd(3, "g3")]
    mock_pyvda.get_virtual_desktops.return_value = desktops
    mock_pyvda.VirtualDesktop.side_effect = lambda number: desktops[number - 1]
    mock_pyvda.VirtualDesktop.create.return_value = _make_mock_vd(4, "g4")
    mock_pyvda.AppView.side_effect = lambda hwnd: MagicMock()
    monkeypatch.setitem(sys.modules, "pyvda", mock_pyvda)

    mock_win32gui = MagicMock()
    mock_win32process = MagicMock()
    monkeypatch.setitem(sys.modules, "win32gui", mock_win32gui)
    monkeypatch.setitem(sys.modules, "win32process", mock_win32process)

    import importlib
    import py_virtual_desktop._desktop as desktop_mod
    import py_virtual_desktop._window as window_mod
    import py_virtual_desktop._manager as manager_mod
    importlib.reload(desktop_mod)
    importlib.reload(window_mod)
    importlib.reload(manager_mod)

    return manager_mod, mock_pyvda, mock_win32gui, mock_win32process


class TestMoveWindow:
    def test_success(self, mock_deps):
        mod, mock_pyvda, _, _ = mock_deps
        result = mod.move_window(hwnd=100, desktop_index=1)
        assert isinstance(result, MoveResult)
        assert result.ok is True
        assert result.desktop_index == 1
        assert result.windows_moved == 1
        mock_pyvda.AppView.assert_called_once_with(hwnd=100)

    def test_pyvda_error(self, mock_deps):
        mod, mock_pyvda, _, _ = mock_deps
        mock_pyvda.AppView.side_effect = Exception("COM error")
        result = mod.move_window(hwnd=100, desktop_index=1)
        assert result.ok is False
        assert "COM error" in result.error


class TestMoveWindowsByPid:
    def test_moves_all_windows(self, mock_deps):
        mod, mock_pyvda, mock_gui, mock_proc = mock_deps

        windows = [(200, 5000, "Win A", True), (201, 5000, "Win B", True)]

        def fake_enum(cb, _):
            for hwnd, *_ in windows:
                cb(hwnd, None)

        mock_gui.EnumWindows.side_effect = fake_enum
        mock_gui.IsWindowVisible.return_value = True
        mock_gui.GetWindowText.side_effect = lambda h: {200: "Win A", 201: "Win B"}[h]
        mock_proc.GetWindowThreadProcessId.side_effect = lambda h: (0, 5000)

        result = mod.move_windows_by_pid(pid=5000, desktop_index=1)
        assert result.ok is True
        assert result.windows_moved == 2
        assert mock_pyvda.AppView.call_count == 2

    def test_auto_creates_desktops(self, mock_deps):
        mod, mock_pyvda, mock_gui, mock_proc = mock_deps

        mock_pyvda.get_virtual_desktops.return_value = [_make_mock_vd(1, "g1")]
        new_vd = _make_mock_vd(2, "g2")
        mock_pyvda.VirtualDesktop.create.return_value = new_vd
        mock_pyvda.VirtualDesktop.side_effect = lambda number: (
            [_make_mock_vd(1, "g1"), new_vd][number - 1]
        )
        mock_pyvda.get_virtual_desktops.side_effect = [
            [_make_mock_vd(1, "g1")],
            [_make_mock_vd(1, "g1"), new_vd],
        ]

        windows = [(300, 7000, "App", True)]

        def fake_enum(cb, _):
            for hwnd, *_ in windows:
                cb(hwnd, None)

        mock_gui.EnumWindows.side_effect = fake_enum
        mock_gui.IsWindowVisible.return_value = True
        mock_gui.GetWindowText.return_value = "App"
        mock_proc.GetWindowThreadProcessId.return_value = (0, 7000)

        result = mod.move_windows_by_pid(pid=7000, desktop_index=1)
        assert result.ok is True
        mock_pyvda.VirtualDesktop.create.assert_called_once()

    def test_no_windows_found(self, mock_deps):
        mod, mock_pyvda, mock_gui, mock_proc = mock_deps

        mock_gui.EnumWindows.side_effect = lambda cb, _: None

        result = mod.move_windows_by_pid(pid=9999, desktop_index=1)
        assert result.ok is False
        assert "No window" in result.error

    def test_fallback_to_main_window_handle(self, mock_deps):
        mod, mock_pyvda, mock_gui, mock_proc = mock_deps

        mock_gui.EnumWindows.side_effect = lambda cb, _: None

        import ctypes
        with patch.object(mod, "_get_main_window_handle", return_value=500):
            result = mod.move_windows_by_pid(pid=8000, desktop_index=1)
            assert result.ok is True
            assert result.windows_moved == 1
