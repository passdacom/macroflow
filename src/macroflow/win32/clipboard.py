"""Win32 clipboard writes for user-confirmed macro text.

This module never reads or logs the existing clipboard contents.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys
import time

assert sys.platform == "win32", "clipboard.py는 Windows에서만 실행 가능합니다"

_CF_UNICODETEXT = 13
_GMEM_MOVEABLE = 0x0002
_OPEN_RETRY_COUNT = 10
_OPEN_RETRY_DELAY_S = 0.010

_user32 = ctypes.windll.user32
_kernel32 = ctypes.windll.kernel32

_user32.OpenClipboard.argtypes = [ctypes.wintypes.HWND]
_user32.OpenClipboard.restype = ctypes.wintypes.BOOL
_user32.EmptyClipboard.argtypes = []
_user32.EmptyClipboard.restype = ctypes.wintypes.BOOL
_user32.SetClipboardData.argtypes = [ctypes.wintypes.UINT, ctypes.wintypes.HANDLE]
_user32.SetClipboardData.restype = ctypes.wintypes.HANDLE
_user32.CloseClipboard.argtypes = []
_user32.CloseClipboard.restype = ctypes.wintypes.BOOL
_kernel32.GlobalAlloc.argtypes = [ctypes.wintypes.UINT, ctypes.c_size_t]
_kernel32.GlobalAlloc.restype = ctypes.wintypes.HGLOBAL
_kernel32.GlobalLock.argtypes = [ctypes.wintypes.HGLOBAL]
_kernel32.GlobalLock.restype = ctypes.c_void_p
_kernel32.GlobalUnlock.argtypes = [ctypes.wintypes.HGLOBAL]
_kernel32.GlobalUnlock.restype = ctypes.wintypes.BOOL
_kernel32.GlobalFree.argtypes = [ctypes.wintypes.HGLOBAL]
_kernel32.GlobalFree.restype = ctypes.wintypes.HGLOBAL


def set_clipboard_text(text: str) -> bool:
    """Replace the clipboard with ``text`` without reading prior clipboard data."""
    opened = False
    for _ in range(_OPEN_RETRY_COUNT):
        if _user32.OpenClipboard(None):
            opened = True
            break
        time.sleep(_OPEN_RETRY_DELAY_S)
    if not opened:
        return False

    handle = ctypes.wintypes.HGLOBAL()
    ownership_transferred = False
    try:
        if not _user32.EmptyClipboard():
            return False
        payload = (text + "\0").encode("utf-16-le")
        handle = _kernel32.GlobalAlloc(_GMEM_MOVEABLE, len(payload))
        if not handle:
            return False
        pointer = _kernel32.GlobalLock(handle)
        if not pointer:
            return False
        try:
            ctypes.memmove(pointer, payload, len(payload))
        finally:
            _kernel32.GlobalUnlock(handle)
        if not _user32.SetClipboardData(_CF_UNICODETEXT, handle):
            return False
        ownership_transferred = True
        return True
    finally:
        if handle and not ownership_transferred:
            _kernel32.GlobalFree(handle)
        _user32.CloseClipboard()
