"""Win32 Low-Level Hook — WH_MOUSE_LL / WH_KEYBOARD_LL.

단일 메시지 펌프 스레드에서 마우스·키보드 이벤트를 캡처한다.
콜백 내에서는 타임스탬프 기록 + deque push만 수행한다 (최소 처리 원칙).

이벤트 포맷:
    ("m", timestamp_ns: int, wParam: int, data: tuple[int, int, int])
        data = (x_px, y_px, mouse_data)
    ("k", timestamp_ns: int, wParam: int, data: tuple[int, int, int])
        data = (vk_code, scan_code, flags)
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys
import threading
import time
from collections import deque

assert sys.platform == "win32", "hooks.py는 Windows에서만 실행 가능합니다"

# ── Win32 메시지 상수 ─────────────────────────────────────────────────────────
WH_MOUSE_LL: int = 14
WH_KEYBOARD_LL: int = 13

WM_MOUSEMOVE: int = 0x0200
WM_LBUTTONDOWN: int = 0x0201
WM_LBUTTONUP: int = 0x0202
WM_RBUTTONDOWN: int = 0x0204
WM_RBUTTONUP: int = 0x0205
WM_MBUTTONDOWN: int = 0x0207
WM_MBUTTONUP: int = 0x0208

WM_KEYDOWN: int = 0x0100
WM_KEYUP: int = 0x0101
WM_SYSKEYDOWN: int = 0x0104
WM_SYSKEYUP: int = 0x0105

WM_QUIT: int = 0x0012

# ── ctypes 구조체 ─────────────────────────────────────────────────────────────

class _POINT(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.wintypes.LONG),
        ("y", ctypes.wintypes.LONG),
    ]


class _MSLLHOOKSTRUCT(ctypes.Structure):
    """마우스 Low-Level Hook 이벤트 구조체."""

    _fields_ = [
        ("pt",          _POINT),
        ("mouseData",   ctypes.wintypes.DWORD),
        ("flags",       ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),  # ULONG_PTR — 플랫폼 너비
    ]


class _KBDLLHOOKSTRUCT(ctypes.Structure):
    """키보드 Low-Level Hook 이벤트 구조체."""

    _fields_ = [
        ("vkCode",      ctypes.wintypes.DWORD),
        ("scanCode",    ctypes.wintypes.DWORD),
        ("flags",       ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


_HOOKPROC = ctypes.WINFUNCTYPE(
    ctypes.c_long,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
)

# ── Win32 DLL 참조 ────────────────────────────────────────────────────────────
_user32 = ctypes.windll.user32
_gdi32 = ctypes.windll.gdi32
_kernel32 = ctypes.windll.kernel32

# ── 내부 상태 ─────────────────────────────────────────────────────────────────
_event_queue: deque[tuple[str, int, int, tuple[int, int, int]]] | None = None
_mouse_hook_id: ctypes.c_long | None = None
_keyboard_hook_id: ctypes.c_long | None = None
_pump_thread: threading.Thread | None = None
_pump_tid: int = 0


# ── Hook 콜백 ─────────────────────────────────────────────────────────────────

def _mouse_proc(nCode: int, wParam: int, lParam: int) -> int:
    """마우스 LL Hook 콜백 — 최소 처리 후 즉시 반환."""
    if nCode >= 0 and _event_queue is not None:
        ts = time.perf_counter_ns()
        ms = ctypes.cast(lParam, ctypes.POINTER(_MSLLHOOKSTRUCT)).contents
        _event_queue.append(("m", ts, wParam, (ms.pt.x, ms.pt.y, ms.mouseData)))
    return _user32.CallNextHookEx(None, nCode, wParam, lParam)


def _keyboard_proc(nCode: int, wParam: int, lParam: int) -> int:
    """키보드 LL Hook 콜백 — 최소 처리 후 즉시 반환."""
    if nCode >= 0 and _event_queue is not None:
        ts = time.perf_counter_ns()
        kb = ctypes.cast(lParam, ctypes.POINTER(_KBDLLHOOKSTRUCT)).contents
        _event_queue.append(("k", ts, wParam, (kb.vkCode, kb.scanCode, kb.flags)))
    return _user32.CallNextHookEx(None, nCode, wParam, lParam)


_mouse_cb = _HOOKPROC(_mouse_proc)
_keyboard_cb = _HOOKPROC(_keyboard_proc)


# ── 메시지 펌프 스레드 ────────────────────────────────────────────────────────

def _message_pump() -> None:
    """WH_MOUSE_LL + WH_KEYBOARD_LL을 단일 스레드에서 처리하는 메시지 펌프.

    WM_QUIT 수신 시 Hook 해제 후 종료.
    GetMessageW 기반이므로 OS가 Hook 콜백을 이 스레드에서 호출한다.
    """
    global _mouse_hook_id, _keyboard_hook_id, _pump_tid

    _pump_tid = _kernel32.GetCurrentThreadId()

    _mouse_hook_id = _user32.SetWindowsHookExW(WH_MOUSE_LL, _mouse_cb, None, 0)
    _keyboard_hook_id = _user32.SetWindowsHookExW(WH_KEYBOARD_LL, _keyboard_cb, None, 0)

    msg = ctypes.wintypes.MSG()
    while _user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
        _user32.TranslateMessage(ctypes.byref(msg))
        _user32.DispatchMessageW(ctypes.byref(msg))

    if _mouse_hook_id:
        _user32.UnhookWindowsHookEx(_mouse_hook_id)
        _mouse_hook_id = None
    if _keyboard_hook_id:
        _user32.UnhookWindowsHookEx(_keyboard_hook_id)
        _keyboard_hook_id = None
    _pump_tid = 0


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────

def start_hook(queue: deque[tuple[str, int, int, tuple[int, int, int]]]) -> None:
    """Hook을 등록하고 메시지 펌프 스레드를 시작한다.

    Args:
        queue: 캡처된 원시 이벤트를 쌓을 deque.
            recorder.py의 소비자 스레드가 이 큐를 읽는다.
    """
    global _event_queue, _pump_thread

    _event_queue = queue
    _pump_thread = threading.Thread(
        target=_message_pump, daemon=True, name="HookPump"
    )
    _pump_thread.start()
    # Hook 등록이 완료될 때까지 잠깐 대기
    time.sleep(0.05)


def stop_hook() -> None:
    """WM_QUIT을 펌프 스레드에 보내 Hook을 해제하고 스레드를 종료한다."""
    global _pump_thread, _event_queue

    if _pump_tid:
        _user32.PostThreadMessageW(_pump_tid, WM_QUIT, 0, 0)

    if _pump_thread is not None:
        _pump_thread.join(timeout=2.0)
        _pump_thread = None

    _event_queue = None


def get_pixel_color(x: int, y: int) -> tuple[int, int, int]:
    """GetPixel로 단일 픽셀 RGB 값을 반환한다.

    core-beliefs.md 원칙 7: 스크린샷 API 금지 — GetPixel만 허용.

    Args:
        x: 화면 X 좌표 (픽셀).
        y: 화면 Y 좌표 (픽셀).

    Returns:
        (R, G, B) 튜플.
    """
    hdc = _user32.GetDC(0)
    color: int = _gdi32.GetPixel(hdc, x, y)
    _user32.ReleaseDC(0, hdc)
    return (color & 0xFF, (color >> 8) & 0xFF, (color >> 16) & 0xFF)


def find_window(title_contains: str) -> int | None:
    """title_contains를 제목에 포함하는 창 핸들(HWND)을 반환한다.

    Args:
        title_contains: 검색할 창 제목 부분 문자열 (대소문자 무시).

    Returns:
        첫 번째 일치하는 HWND. 없으면 None.
    """
    _WNDENUMPROC = ctypes.WINFUNCTYPE(
        ctypes.c_bool,
        ctypes.wintypes.HWND,
        ctypes.wintypes.LPARAM,
    )

    found: list[int | None] = [None]

    @_WNDENUMPROC
    def _enum_cb(hwnd: int, lParam: int) -> bool:
        buf = ctypes.create_unicode_buffer(512)
        _user32.GetWindowTextW(hwnd, buf, 512)
        if title_contains.lower() in buf.value.lower():
            found[0] = hwnd
            return False  # 열거 중단
        return True

    _user32.EnumWindows(_enum_cb, 0)
    return found[0]
