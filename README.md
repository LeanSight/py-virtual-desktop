# py-virtual-desktop

Native Python access to Windows 10/11 virtual desktop management. Thin facade over [pyvda](https://github.com/mirober/pyvda) with added window discovery by PID, auto-creation of desktops, and a high-level `move_windows_by_pid()` API.

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
