"""Win32 SendInput API 래퍼.

마우스 이동·클릭·드래그, 키보드 입력을 원자적으로 전송한다.
MOUSEEVENTF_ABSOLUTE 모드를 사용해 절대 좌표로 이벤트를 전송한다.

core-beliefs.md 원칙 5: 재생은 반드시 SendInput — pynput Controller 사용 금지.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import logging
import sys
import time

assert sys.platform == "win32", "sendinput.py는 Windows에서만 실행 가능합니다"

from .dpi import get_logical_screen_size  # noqa: E402

logger = logging.getLogger(__name__)

_user32 = ctypes.windll.user32

# ── SendInput 상수 ────────────────────────────────────────────────────────────
INPUT_MOUSE: int = 0
INPUT_KEYBOARD: int = 1

MOUSEEVENTF_MOVE: int = 0x0001
MOUSEEVENTF_LEFTDOWN: int = 0x0002
MOUSEEVENTF_LEFTUP: int = 0x0004
MOUSEEVENTF_RIGHTDOWN: int = 0x0008
MOUSEEVENTF_RIGHTUP: int = 0x0010
MOUSEEVENTF_MIDDLEDOWN: int = 0x0020
MOUSEEVENTF_MIDDLEUP: int = 0x0040
MOUSEEVENTF_ABSOLUTE: int = 0x8000

KEYEVENTF_KEYUP: int = 0x0002
KEYEVENTF_SCANCODE: int = 0x0008

# 버튼 이름 → (down flag, up flag) 매핑
_BUTTON_FLAGS: dict[str, tuple[int, int]] = {
    "left":   (MOUSEEVENTF_LEFTDOWN,   MOUSEEVENTF_LEFTUP),
    "right":  (MOUSEEVENTF_RIGHTDOWN,  MOUSEEVENTF_RIGHTUP),
    "middle": (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
}

# ── ctypes 구조체 ─────────────────────────────────────────────────────────────

class _MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx",          ctypes.wintypes.LONG),
        ("dy",          ctypes.wintypes.LONG),
        ("mouseData",   ctypes.wintypes.DWORD),
        ("dwFlags",     ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk",         ctypes.wintypes.WORD),
        ("wScan",       ctypes.wintypes.WORD),
        ("dwFlags",     ctypes.wintypes.DWORD),
        ("time",        ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.c_size_t),
    ]


class _HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg",    ctypes.wintypes.DWORD),
        ("wParamL", ctypes.wintypes.WORD),
        ("wParamH", ctypes.wintypes.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", _MOUSEINPUT),
        ("ki", _KEYBDINPUT),
        ("hi", _HARDWAREINPUT),
    ]


class _INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("_input", _INPUT_UNION),
    ]


_INPUT_SIZE = ctypes.sizeof(_INPUT)

# SendInput argtypes/restype — 반환값은 실제로 전송된 이벤트 수 (UINT)
_user32.SendInput.restype = ctypes.wintypes.UINT
_user32.SendInput.argtypes = [
    ctypes.wintypes.UINT,              # cInputs
    ctypes.POINTER(_INPUT),            # pInputs
    ctypes.c_int,                      # cbSize
]


# ── 좌표 변환 헬퍼 ────────────────────────────────────────────────────────────

def _normalize(x: int, y: int) -> tuple[int, int]:
    """픽셀 좌표를 SendInput ABSOLUTE 모드 좌표 (0~65535)로 변환한다."""
    w, h = get_logical_screen_size()
    nx = x * 65535 // max(w - 1, 1)
    ny = y * 65535 // max(h - 1, 1)
    return (nx, ny)


def _mouse_input(x: int, y: int, flags: int) -> _INPUT:
    nx, ny = _normalize(x, y)
    inp = _INPUT(type=INPUT_MOUSE)
    inp._input.mi = _MOUSEINPUT(
        dx=nx, dy=ny, mouseData=0,
        dwFlags=flags | MOUSEEVENTF_ABSOLUTE,
        time=0, dwExtraInfo=0,
    )
    return inp


def _send(*inputs: _INPUT) -> None:
    arr = (_INPUT * len(inputs))(*inputs)
    sent: int = _user32.SendInput(len(inputs), arr, _INPUT_SIZE)
    if sent != len(inputs):
        logger.warning(
            "SendInput: 요청 %d개 중 %d개만 전송됨 (UIPI 차단 또는 권한 문제 가능성)",
            len(inputs), sent,
        )


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────

def send_mouse_move(x: int, y: int) -> None:
    """커서를 절대 픽셀 좌표로 이동한다.

    Args:
        x: 목표 X 좌표 (픽셀).
        y: 목표 Y 좌표 (픽셀).
    """
    _send(_mouse_input(x, y, MOUSEEVENTF_MOVE))


def send_mouse_click(x: int, y: int, button: str = "left") -> None:
    """지정 좌표에서 마우스 클릭(down + up)을 원자적으로 전송한다.

    Args:
        x: 클릭 X 좌표 (픽셀).
        y: 클릭 Y 좌표 (픽셀).
        button: "left" | "right" | "middle".
    """
    down_flag, up_flag = _BUTTON_FLAGS.get(button, _BUTTON_FLAGS["left"])
    _send(
        _mouse_input(x, y, MOUSEEVENTF_MOVE),
        _mouse_input(x, y, down_flag),
        _mouse_input(x, y, up_flag),
    )


def send_mouse_drag(x1: int, y1: int, x2: int, y2: int, button: str = "left") -> None:
    """x1,y1 → x2,y2 직선 드래그를 전송한다 (down + 보간 이동 + up).

    10단계로 보간하여 자연스러운 드래그를 재현한다.

    Args:
        x1: 드래그 시작 X (픽셀).
        y1: 드래그 시작 Y (픽셀).
        x2: 드래그 종료 X (픽셀).
        y2: 드래그 종료 Y (픽셀).
        button: "left" | "right" | "middle".
    """
    down_flag, up_flag = _BUTTON_FLAGS.get(button, _BUTTON_FLAGS["left"])
    steps = 10

    _send(_mouse_input(x1, y1, MOUSEEVENTF_MOVE))
    _send(_mouse_input(x1, y1, down_flag))

    for i in range(1, steps + 1):
        mx = x1 + (x2 - x1) * i // steps
        my = y1 + (y2 - y1) * i // steps
        _send(_mouse_input(mx, my, MOUSEEVENTF_MOVE))
        time.sleep(0.01)

    _send(_mouse_input(x2, y2, up_flag))


def send_mouse_button(x: int, y: int, button: str, down: bool) -> None:
    """마우스 버튼 단독 이벤트(down 또는 up만)를 전송한다.

    send_mouse_click과 달리 down/up 중 하나만 전송한다.
    player.py가 타이밍을 직접 제어할 때 사용한다.

    Args:
        x: X 좌표 (픽셀).
        y: Y 좌표 (픽셀).
        button: "left" | "right" | "middle".
        down: True이면 button down, False이면 button up.
    """
    down_flag, up_flag = _BUTTON_FLAGS.get(button, _BUTTON_FLAGS["left"])
    flag = down_flag if down else up_flag
    _send(_mouse_input(x, y, flag))


def send_key(vk_code: int, is_down: bool) -> None:
    """가상 키 코드로 키 이벤트(down 또는 up)를 전송한다.

    Args:
        vk_code: Windows Virtual Key Code.
        is_down: True이면 key down, False이면 key up.
    """
    flags = 0 if is_down else KEYEVENTF_KEYUP
    inp = _INPUT(type=INPUT_KEYBOARD)
    inp._input.ki = _KEYBDINPUT(
        wVk=vk_code, wScan=0,
        dwFlags=flags, time=0, dwExtraInfo=0,
    )
    _send(inp)
