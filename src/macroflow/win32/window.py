"""Win32 helpers for restoring and foregrounding an application window."""

from __future__ import annotations

import sys
from typing import Any

_SW_SHOW = 5
_HWND_TOPMOST = -1
_HWND_NOTOPMOST = -2
_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_SHOWWINDOW = 0x0040
_RAISE_FLAGS = _SWP_NOSIZE | _SWP_NOMOVE | _SWP_SHOWWINDOW


def _activate_with_user32(user32: Any, hwnd: int) -> bool:
    """Show, transiently raise, and foreground ``hwnd`` through user32."""
    if hwnd <= 0:
        return False

    shown = bool(user32.ShowWindow(hwnd, _SW_SHOW))
    raised = bool(
        user32.SetWindowPos(hwnd, _HWND_TOPMOST, 0, 0, 0, 0, _RAISE_FLAGS)
    )
    lowered = bool(
        user32.SetWindowPos(hwnd, _HWND_NOTOPMOST, 0, 0, 0, 0, _RAISE_FLAGS)
    )
    foregrounded = bool(user32.SetForegroundWindow(hwnd))
    return shown or (raised and lowered) or foregrounded


def bring_window_to_foreground(hwnd: int) -> bool:
    """Bring a native window to the foreground on Windows.

    The temporary TOPMOST → NOTOPMOST transition avoids leaving MacroFlow pinned
    above other applications while still making a global-hotkey prompt visible.
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
