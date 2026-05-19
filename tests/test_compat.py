from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest


class TestIsAvailable:
    def test_returns_true_when_pyvda_works(self, monkeypatch):
        mock_pyvda = MagicMock()
        mock_pyvda.VirtualDesktop.current.return_value = MagicMock()
        monkeypatch.setitem(sys.modules, "pyvda", mock_pyvda)

        from py_virtual_desktop._compat import is_available
        assert is_available() is True

    def test_returns_false_when_pyvda_import_fails(self, monkeypatch):
        monkeypatch.setitem(sys.modules, "pyvda", None)

        import importlib
        import py_virtual_desktop._compat as mod
        importlib.reload(mod)

        assert mod.is_available() is False

    def test_returns_false_on_non_windows(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")

        import importlib
        import py_virtual_desktop._compat as mod
        importlib.reload(mod)

        assert mod.is_available() is False


class TestCheckPlatform:
    def test_raises_on_linux(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "linux")

        import importlib
        import py_virtual_desktop._compat as mod
        importlib.reload(mod)

        with pytest.raises(NotImplementedError, match="Windows"):
            mod.check_platform()

    def test_passes_on_win32(self, monkeypatch):
        monkeypatch.setattr(sys, "platform", "win32")

        import importlib
        import py_virtual_desktop._compat as mod
        importlib.reload(mod)

        mod.check_platform()
