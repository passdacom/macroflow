"""Win32 helpers for restoring and foregrounding an application window."""

from __future__ import annotations

import sys
from typing import Any

_SW_SHOW = 5
_HWND_TOP = 0
_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_SHOWWINDOW = 0x0040
_RAISE_FLAGS = _SWP_NOSIZE | _SWP_NOMOVE | _SWP_SHOWWINDOW


def _activate_with_user32(user32: Any, hwnd: int) -> bool:
    """Show, transiently raise, and foreground ``hwnd`` through user32."""
    if hwnd <= 0:
        return False

    shown = bool(user32.ShowWindow(hwnd, _SW_SHOW))
    raised = bool(user32.SetWindowPos(hwnd, _HWND_TOP, 0, 0, 0, 0, _RAISE_FLAGS))
    foregrounded = bool(user32.SetForegroundWindow(hwnd))
    return shown or raised or foregrounded


def bring_window_to_foreground(hwnd: int) -> bool:
    """Bring a native window to the foreground on Windows.

    The window is moved to the top of the non-topmost z-order, so MacroFlow is
    surfaced without risking a persistent always-on-top state.
    """
    if sys.platform != "win32" or hwnd <= 0:
        return False

    import ctypes
    import ctypes.wintypes

    user32 = ctypes.windll.user32
    user32.ShowWindow.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = ctypes.wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        ctypes.wintypes.HWND,
        ctypes.wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.wintypes.UINT,
    ]
    user32.SetWindowPos.restype = ctypes.wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [ctypes.wintypes.HWND]
    user32.SetForegroundWindow.restype = ctypes.wintypes.BOOL
    return _activate_with_user32(user32, hwnd)


def get_foreground_window() -> int:
    """Return the current native foreground HWND, or 0 when unavailable."""
    if sys.platform != "win32":
        return 0
    import ctypes
    import ctypes.wintypes

    get_foreground = ctypes.windll.user32.GetForegroundWindow
    get_foreground.argtypes = []
    get_foreground.restype = ctypes.wintypes.HWND
    return int(get_foreground() or 0)


def is_foreground_window(hwnd: int) -> bool:
    """Read back whether ``hwnd`` is currently foreground."""
    return hwnd > 0 and get_foreground_window() == hwnd
