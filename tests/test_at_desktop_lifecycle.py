"""Acceptance tests for desktop current, create, ensure, activate, remove."""
from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest


def _make_mock_vd(number: int, guid: str = "", name: str = ""):
    vd = MagicMock()
    vd.number = number
    vd.id = guid or f"guid-{number}"
    vd.name = name
    return vd


@pytest.fixture
def two_desktops(monkeypatch):
    mock_pyvda = MagicMock()
    vds = [_make_mock_vd(1, "g1"), _make_mock_vd(2, "g2")]
    mock_pyvda.get_virtual_desktops.return_value = vds
    mock_pyvda.VirtualDesktop.side_effect = lambda number: vds[number - 1]
    mock_pyvda.VirtualDesktop.current.return_value = vds[0]
    mock_pyvda.VirtualDesktop.create.return_value = _make_mock_vd(3, "g3")
    monkeypatch.setitem(sys.modules, "pyvda", mock_pyvda)
    return mock_pyvda


class TestCurrentDesktop:
    def test_current_returns_active_desktop(self, two_desktops):
        """
        Given  a system with 2 virtual desktops, user on the first one
        When   desktops.current is accessed
        Then   returns a Desktop with index=0
        """
        from py_virtual_desktop import Desktops

        desktops = Desktops()
        current = desktops.current

        assert current.index == 0
        assert current.id == "g1"


class TestCreateDesktop:
    def test_create_returns_new_desktop(self, two_desktops):
        """
        Given  a system with 2 desktops
        When   desktops.create() is called
        Then   a new Desktop is returned with index=2
        """
        from py_virtual_desktop import Desktops

        desktops = Desktops()
        new = desktops.create()

        assert new.index == 2
        assert new.id == "g3"


class TestEnsureDesktops:
    def test_ensure_creates_missing(self, two_desktops):
        """
        Given  a system with 2 desktops
        When   desktops.ensure(4) is called
        Then   2 desktops are created, returning 4 Desktop objects
        """
        from py_virtual_desktop import Desktops

        new_vds = [
            _make_mock_vd(1, "g1"), _make_mock_vd(2, "g2"),
            _make_mock_vd(3, "g3"), _make_mock_vd(4, "g4"),
        ]
        two_desktops.get_virtual_desktops.side_effect = [
            [_make_mock_vd(1, "g1"), _make_mock_vd(2, "g2")],
            new_vds,
        ]

        desktops = Desktops()
        result = desktops.ensure(4)

        assert len(result) == 4
        assert two_desktops.VirtualDesktop.create.call_count == 2


class TestActivateDesktop:
    def test_activate_switches_to_desktop(self, two_desktops):
        """
        Given  a system with 2 desktops, user on the first
        When   desktops[1].activate() is called
        Then   the second desktop is activated
        """
        from py_virtual_desktop import Desktops

        desktops = Desktops()
        desktops[1].activate()

        vd = two_desktops.VirtualDesktop(number=2)
        vd.go.assert_called_once()


class TestRemoveDesktop:
    def test_remove_deletes_desktop(self, two_desktops):
        """
        Given  a system with 2 desktops
        When   desktops[1].remove() is called
        Then   the second desktop is removed
        """
        from py_virtual_desktop import Desktops

        desktops = Desktops()
        desktops[1].remove()

        vd = two_desktops.VirtualDesktop(number=2)
        vd.remove.assert_called_once()
