# py-virtual-desktop

Native Python access to Windows 10/11 virtual desktop management. Thin facade over [pyvda](https://github.com/mirober/pyvda) with added window discovery by PID, auto-creation of desktops, and a high-level `move_windows_by_pid()` API.

## Why

Managing virtual desktops from Python previously required shelling out to PowerShell with the [PSVirtualDesktop](https://github.com/MScholtes/PSVirtualDesktop) module (`Import-Module VirtualDesktop`). This worked but added subprocess overhead, fragile string-templated scripts, and a hard dependency on PowerShell.

py-virtual-desktop replaces that approach with direct Python calls. The API mirrors the PSVirtualDesktop cmdlets that matter most — `Get-DesktopCount`, `Get-Desktop`, `New-Desktop`, `Move-Window`, and `Find-WindowHandle` — but as native Python functions with typed return values.

Under the hood it uses [pyvda](https://github.com/mirober/pyvda), which wraps the same undocumented Windows COM interfaces (`IVirtualDesktopManagerInternal`, `IVirtualDesktopManager`, `IApplicationView`) that PSVirtualDesktop reverse-engineered in C#. The window discovery by PID (`find_window_handles`) is the one piece pyvda doesn't cover — it uses `win32gui.EnumWindows` directly.

## Install

```bash
pip install -e .
```

## Quick start

```python
from py_virtual_desktop import (
    get_desktop_count,
    get_current_desktop,
    move_windows_by_pid,
    find_window_handles,
)

print(get_desktop_count())        # 3
print(get_current_desktop())      # Desktop(index=0, id='{...}', name='')

# Move all windows of a process to desktop index 1 (second desktop)
result = move_windows_by_pid(pid=12345, desktop_index=1)
print(result)  # MoveResult(ok=True, desktop_index=1, windows_moved=2, error=None)
```

## API

| Function | Description |
|---|---|
| `get_desktop_count()` | Number of virtual desktops |
| `get_desktop(index)` | Get desktop by 0-based index |
| `get_current_desktop()` | Active desktop |
| `create_desktop()` | Create a new desktop |
| `ensure_desktop_count(n)` | Create desktops until count reaches `n` |
| `switch_desktop(index)` | Switch to desktop |
| `remove_desktop(index)` | Remove desktop |
| `find_window_handles(pid, title_pattern, visible_only)` | Find windows by PID/title |
| `move_window(hwnd, desktop_index)` | Move a single window |
| `move_windows_by_pid(pid, desktop_index)` | Move all windows of a process |
| `is_available()` | Check if virtual desktop management works |

## Requirements

- Windows 10 or 11
- Python >= 3.12
- [pyvda](https://pypi.org/project/pyvda/) >= 0.5.0 (installed automatically)

## License

MIT
