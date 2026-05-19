"""Acceptance tests for the Desktops collection API."""
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
def three_desktops(monkeypatch):
    mock_pyvda = MagicMock()
    vds = [_make_mock_vd(1, "g1", "Main"), _make_mock_vd(2, "g2"), _make_mock_vd(3, "g3", "Work")]
    mock_pyvda.get_virtual_desktops.return_value = vds
    mock_pyvda.VirtualDesktop.side_effect = lambda number: vds[number - 1]
    mock_pyvda.VirtualDesktop.current.return_value = vds[0]
    monkeypatch.setitem(sys.modules, "pyvda", mock_pyvda)
    return mock_pyvda


class TestDesktopCollectionBehavior:
    def test_count_iteration_and_indexing(self, three_desktops):
        """
        Given  a system with 3 virtual desktops
        When   a user creates a Desktops collection
        Then   len(desktops) returns 3
         And   iterating yields Desktop objects with indices 0, 1, 2
         And   desktops[1] returns the second Desktop
         And   desktops[-1] returns the last Desktop
         And   accessing an out-of-range index raises DesktopNotFoundError
        """
        from py_virtual_desktop import Desktops, DesktopNotFoundError

        desktops = Desktops()

        assert len(desktops) == 3

        indices = [d.index for d in desktops]
        assert indices == [0, 1, 2]

        second = desktops[1]
        assert second.index == 1
        assert second.id == "g2"

        last = desktops[-1]
        assert last.index == 2
        assert last.name == "Work"

        with pytest.raises(DesktopNotFoundError):
            desktops[100]
