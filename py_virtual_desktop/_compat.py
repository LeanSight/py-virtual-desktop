from __future__ import annotations

import sys


def check_platform() -> None:
    if sys.platform != "win32":
        raise NotImplementedError(
            "py-virtual-desktop requires Windows 10 or later."
        )


def is_available() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import pyvda  # noqa: F811
        pyvda.VirtualDesktop.current()
        return True
    except Exception:
        return False
