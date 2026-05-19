from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch, call

import pytest

from py_virtual_desktop._types import Desktop


def _make_mock_vd(number: int, guid: str = "", name: str = ""):
    vd = MagicMock()
    vd.number = number
    vd.id = guid or f"guid-{number}"
    vd.name = name
    return vd


@pytest.fixture
def mock_pyvda(monkeypatch):
    mock = MagicMock()

    desktops = [_make_mock_vd(1, "g1"), _make_mock_vd(2, "g2")]
    mock.get_virtual_desktops.return_value = desktops
    mock.VirtualDesktop.side_effect = lambda number: desktops[number - 1]
    mock.VirtualDesktop.current.return_value = desktops[0]
    mock.VirtualDesktop.create.return_value = _make_mock_vd(3, "g3")

    monkeypatch.setitem(sys.modules, "pyvda", mock)

    import importlib
    import py_virtual_desktop._desktop as mod
    importlib.reload(mod)
    return mod, mock


class TestGetDesktopCount:
    def test_returns_count(self, mock_pyvda):
        mod, _ = mock_pyvda
        assert mod.get_desktop_count() == 2


class TestGetDesktop:
    def test_zero_indexed(self, mock_pyvda):
        mod, mock = mock_pyvda
        d = mod.get_desktop(0)
        assert isinstance(d, Desktop)
        assert d.index == 0
        assert d.id == "g1"
        mock.VirtualDesktop.assert_called_with(number=1)

    def test_second_desktop(self, mock_pyvda):
        mod, mock = mock_pyvda
        d = mod.get_desktop(1)
        assert d.index == 1
        assert d.id == "g2"
        mock.VirtualDesktop.assert_called_with(number=2)

    def test_negative_index_raises(self, mock_pyvda):
        mod, _ = mock_pyvda
        with pytest.raises(ValueError, match="non-negative"):
            mod.get_desktop(-1)


class TestGetCurrentDesktop:
    def test_returns_current(self, mock_pyvda):
        mod, _ = mock_pyvda
        d = mod.get_current_desktop()
        assert isinstance(d, Desktop)
        assert d.index == 0
        assert d.id == "g1"


class TestCreateDesktop:
    def test_creates_and_returns(self, mock_pyvda):
        mod, mock = mock_pyvda
        d = mod.create_desktop()
        assert isinstance(d, Desktop)
        assert d.index == 2
        assert d.id == "g3"
        mock.VirtualDesktop.create.assert_called_once()


class TestEnsureDesktopCount:
    def test_noop_when_enough(self, mock_pyvda):
        mod, mock = mock_pyvda
        result = mod.ensure_desktop_count(2)
        assert len(result) == 2
        mock.VirtualDesktop.create.assert_not_called()

    def test_creates_missing(self, mock_pyvda):
        mod, mock = mock_pyvda
        new_vd = _make_mock_vd(3, "g3")
        mock.VirtualDesktop.create.return_value = new_vd
        mock.get_virtual_desktops.side_effect = [
            [_make_mock_vd(1, "g1"), _make_mock_vd(2, "g2")],
            [_make_mock_vd(1, "g1"), _make_mock_vd(2, "g2"), new_vd],
        ]
        result = mod.ensure_desktop_count(3)
        assert len(result) == 3
        mock.VirtualDesktop.create.assert_called_once()

    def test_zero_raises(self, mock_pyvda):
        mod, _ = mock_pyvda
        with pytest.raises(ValueError, match="at least 1"):
            mod.ensure_desktop_count(0)


class TestSwitchDesktop:
    def test_switches(self, mock_pyvda):
        mod, mock = mock_pyvda
        mod.switch_desktop(1)
        vd = mock.VirtualDesktop(number=2)
        vd.go.assert_called_once()


class TestRemoveDesktop:
    def test_removes(self, mock_pyvda):
        mod, mock = mock_pyvda
        mod.remove_desktop(1)
        vd = mock.VirtualDesktop(number=2)
        vd.remove.assert_called_once()
