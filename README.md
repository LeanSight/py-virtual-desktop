# py-virtual-desktop

Pythonic access to Windows 10/11 virtual desktop management. API inspired by [PSVirtualDesktop](https://github.com/MScholtes/PSVirtualDesktop), built as a facade over [pyvda](https://github.com/mirober/pyvda).

## Why not just use pyvda directly?

[pyvda](https://github.com/mirober/pyvda) handles the hard part — COM interop with undocumented Windows interfaces. py-virtual-desktop adds what's missing for real-world automation:

- **Window discovery by PID** — `Window.find(pid=...)` enumerates windows belonging to a process via `win32gui.EnumWindows`. pyvda can move a window if you already have its `hwnd`, but has no way to find it.
- **`move_windows(pid, to)`** — one call that finds all windows for a PID, ensures the target desktop exists (creating it if needed), moves them, and falls back to `MainWindowHandle` if enumeration misses the window.
- **Auto-creation of desktops** — `desktops.ensure(n)` creates missing desktops silently. pyvda raises if you reference a desktop that doesn't exist yet.
- **Domain objects with behavior** — `Desktop` and `Window` are live handles with methods (`desktop.activate()`, `window.move_to()`), not inert data bags. Modeled after `pathlib.Path`.
- **0-indexed API** — matches Windows internals. pyvda uses 1-indexed desktop numbers.

## Install

```bash
pip install -e .
```

## Quick start

```python
from py_virtual_desktop import Desktops, Window, move_windows

# Iterate desktops
desktops = Desktops()
for d in desktops:
    print(f"Desktop {d.index}: {d.name or '(unnamed)'}")

# Access by index
work = desktops[1]
work.activate()

# Find and move windows
chrome = Window.find(title="Chrome")
chrome[0].move_to(work)         # with Desktop object
chrome[0].move_to(2)            # or by index

# Move all windows of a process
count = move_windows(pid=12345, to=1)
print(f"Moved {count} windows")
```

## API

### `Desktops` — collection (entry point)

| | |
|---|---|
| `len(desktops)` | Number of virtual desktops |
| `desktops[i]` | Get desktop by 0-based index (supports negative) |
| `for d in desktops` | Iterate all desktops |
| `desktops.current` | Active desktop |
| `desktops.create()` | Create a new desktop |
| `desktops.ensure(n)` | Ensure at least `n` desktops exist |

### `Desktop` — live handle

| | |
|---|---|
| `desktop.index` | 0-based index |
| `desktop.id` | Windows GUID |
| `desktop.name` | User-assigned name (Windows 11+) |
| `desktop.is_active` | Whether this is the current desktop |
| `desktop.activate()` | Switch to this desktop |
| `desktop.remove()` | Remove this desktop |

### `Window` — live handle

| | |
|---|---|
| `Window.find(pid=, title=, visible_only=)` | Find windows by PID/title regex |
| `window.hwnd` | Win32 window handle |
| `window.pid` | Owning process ID |
| `window.title` | Window title |
| `window.move_to(Desktop \| int)` | Move to another desktop |

### Module-level

| | |
|---|---|
| `move_windows(pid=, to=, fallback=)` | Move all windows of a process |
| `is_available()` | Check if virtual desktop management works |

### Exceptions

| | |
|---|---|
| `VirtualDesktopError` | Base exception |
| `DesktopNotFoundError` | Desktop index out of range (also `IndexError`) |
| `WindowMoveError` | Window movement failed (also `OSError`) |
| `WindowNotFoundError` | No windows match criteria (also `LookupError`) |

## Requirements

- Windows 10 or 11
- Python >= 3.12
- [pyvda](https://pypi.org/project/pyvda/) >= 0.5.0 (installed automatically)

## License

MIT
