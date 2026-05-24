"""Acceptance tests for launch_on()."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch, call

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


class TestLaunchOn:
    def test_switches_to_target_before_launching(self, mock_all):
        """
        Given  user is on desktop 0
        When   launch_on(cmd, to=1) is called
        Then   desktop 1 is activated BEFORE the process is launched
         And   the process is returned
        """
        mock_pyvda, win32gui, win32process = mock_all
        _setup_windows(win32gui, win32process, [(300, 4200, "NewApp", True)])

        target_vd = mock_pyvda.VirtualDesktop(number=2)
        mock_proc = MagicMock()
        mock_proc.pid = 4200

        from py_virtual_desktop import launch_on

        with patch("py_virtual_desktop._manager.subprocess") as mock_sub:
            mock_sub.Popen.return_value = mock_proc
            proc = launch_on(["myapp.exe"], to=1)

        assert proc.pid == 4200
        target_vd.go.assert_called()

    def test_restores_original_desktop(self, mock_all):
        """
        Given  user is on desktop 0
        When   launch_on(cmd, to=1) completes
        Then   user is back on desktop 0
        """
        mock_pyvda, win32gui, win32process = mock_all
        _setup_windows(win32gui, win32process, [(300, 4200, "NewApp", True)])

        original_vd = mock_pyvda.VirtualDesktop.current()
        mock_proc = MagicMock()
        mock_proc.pid = 4200

        from py_virtual_desktop import launch_on

        with patch("py_virtual_desktop._manager.subprocess") as mock_sub:
            mock_sub.Popen.return_value = mock_proc
            launch_on(["myapp.exe"], to=1)

        original_vd.go.assert_called()

    def test_restores_desktop_even_on_timeout(self, mock_all):
        """
        Given  a process that never creates a visible window
        When   launch_on times out
        Then   user is still restored to original desktop
        """
        mock_pyvda, win32gui, win32process = mock_all
        win32gui.EnumWindows.side_effect = lambda cb, _: None

        original_vd = mock_pyvda.VirtualDesktop.current()
        mock_proc = MagicMock()
        mock_proc.pid = 9999

        from py_virtual_desktop import launch_on, WindowNotFoundError

        with (
            patch("py_virtual_desktop._manager.subprocess") as mock_sub,
            patch("py_virtual_desktop._manager.time") as mock_time,
        ):
            mock_sub.Popen.return_value = mock_proc
            mock_time.monotonic.side_effect = [0.0, 100.0]
            mock_time.sleep = MagicMock()

            with pytest.raises(WindowNotFoundError):
                launch_on(["myapp.exe"], to=1, timeout=0.5)

        original_vd.go.assert_called()

    def test_polls_until_window_appears(self, mock_all):
        """
        Given  a process whose window appears after a delay
        When   launch_on(cmd, to=1) is called
        Then   it polls until the window is found
        """
        mock_pyvda, win32gui, win32process = mock_all

        call_count = 0

        def fake_enum_delayed(cb, _):
            nonlocal call_count
            call_count += 1
            if call_count >= 3:
                cb(300, None)

        win32gui.EnumWindows.side_effect = fake_enum_delayed
        win32gui.IsWindowVisible.return_value = True
        win32gui.GetWindowText.side_effect = lambda h: "NewApp"
        win32process.GetWindowThreadProcessId.side_effect = lambda h: (0, 4200)

        mock_proc = MagicMock()
        mock_proc.pid = 4200

        from py_virtual_desktop import launch_on

        with (
            patch("py_virtual_desktop._manager.subprocess") as mock_sub,
            patch("py_virtual_desktop._manager.time") as mock_time,
        ):
            mock_sub.Popen.return_value = mock_proc
            mock_time.monotonic.side_effect = [0.0, 0.1, 0.2, 0.3, 0.4]
            mock_time.sleep = MagicMock()
            proc = launch_on(["myapp.exe"], to=1, timeout=5.0)

        assert proc.pid == 4200
        assert call_count >= 3

    def test_finds_window_in_child_process(self, mock_all):
        """
        Given  a wrapper process (PID 4200) that spawns a child (PID 4201)
         And   only the child has a visible window
        When   launch_on(cmd, to=1) is called
        Then   the child's window is found and the process is returned
        """
        mock_pyvda, win32gui, win32process = mock_all

        def fake_enum(cb, _):
            cb(300, None)

        win32gui.EnumWindows.side_effect = fake_enum
        win32gui.IsWindowVisible.return_value = True
        win32gui.GetWindowText.side_effect = lambda h: "ChildApp"
        win32process.GetWindowThreadProcessId.side_effect = lambda h: (0, 4201)

        mock_proc = MagicMock()
        mock_proc.pid = 4200

        from py_virtual_desktop import launch_on

        with (
            patch("py_virtual_desktop._manager.subprocess") as mock_sub,
            patch("py_virtual_desktop._manager._get_child_pids", return_value=[4201]),
        ):
            mock_sub.Popen.return_value = mock_proc
            proc = launch_on(["wrapper.exe"], to=1)

        assert proc.pid == 4200
