"""Key-name to Windows VK-code mapping for the MacroFlow event editor.

This module is intentionally PyQt-free so key editing policy can be tested without
loading the GUI runtime.
"""

from __future__ import annotations

import sys

# ── 키 이름 → VK 코드 매핑 ────────────────────────────────────────────────────

NAME_TO_VK: dict[str, int] = {
    # 제어 키
    "backspace": 0x08, "tab": 0x09, "enter": 0x0D, "return": 0x0D,
    "shift": 0x10, "ctrl": 0x11, "control": 0x11, "alt": 0x12,
    "pause": 0x13, "capslock": 0x14,
    "escape": 0x1B, "esc": 0x1B, "space": 0x20,
    "pageup": 0x21, "pagedown": 0x22, "end": 0x23, "home": 0x24,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "insert": 0x2D, "delete": 0x2E, "del": 0x2E,
    # 숫자 (일반)
    **{str(d): 0x30 + d for d in range(10)},
    # 알파벳
    **{chr(ord("a") + k): 0x41 + k for k in range(26)},
    # 기능 키
    **{f"f{n}": 0x70 + n - 1 for n in range(1, 25)},
    # 숫자패드
    "num0": 0x60, "num1": 0x61, "num2": 0x62, "num3": 0x63,
    "num4": 0x64, "num5": 0x65, "num6": 0x66, "num7": 0x67,
    "num8": 0x68, "num9": 0x69,
    "num*": 0x6A, "num+": 0x6B, "num-": 0x6D, "num.": 0x6E, "num/": 0x6F,
    "numlock": 0x90, "scrolllock": 0x91,
    # OEM 특수문자 (US 표준 키보드 배열)
    ";": 0xBA,   # VK_OEM_1
    "=": 0xBB,   # VK_OEM_PLUS
    ",": 0xBC,   # VK_OEM_COMMA
    "-": 0xBD,   # VK_OEM_MINUS
    ".": 0xBE,   # VK_OEM_PERIOD
    "/": 0xBF,   # VK_OEM_2
    "`": 0xC0,   # VK_OEM_3
    "[": 0xDB,   # VK_OEM_4
    "\\": 0xDC,  # VK_OEM_5
    "]": 0xDD,   # VK_OEM_6
    "'": 0xDE,   # VK_OEM_7
    # 수식어 확장
    "lshift": 0xA0, "rshift": 0xA1,
    "lctrl": 0xA2, "rctrl": 0xA3,
    "lalt": 0xA4, "ralt": 0xA5,
    "lwin": 0x5B, "rwin": 0x5C,
    # 기타
    "printscreen": 0x2C, "prtsc": 0x2C,
    "apps": 0x5D,
    # 하위 호환 별칭 — recorder.py 구버전이 저장한 이름도 편집 가능하도록
    "period": 0xBE, "comma": 0xBC, "minus": 0xBD, "equal": 0xBB,
    "slash": 0xBF, "backtick": 0xC0,
    "bracket_left": 0xDB, "backslash": 0xDC,
    "bracket_right": 0xDD, "quote": 0xDE, "semicolon": 0xBA,
    "shift_left": 0xA0, "shift_right": 0xA1,
    "ctrl_left": 0xA2, "ctrl_right": 0xA3,
    "alt_left": 0xA4, "alt_right": 0xA5,
    "win_left": 0x5B, "win_right": 0x5C,
    "numpad0": 0x60, "numpad1": 0x61, "numpad2": 0x62, "numpad3": 0x63,
    "numpad4": 0x64, "numpad5": 0x65, "numpad6": 0x66, "numpad7": 0x67,
    "numpad8": 0x68, "numpad9": 0x69,
}


def key_name_to_vk(key_name: str, fallback_vk: int) -> int:
    """키 이름 문자열을 VK 코드로 변환한다.

    1) NAME_TO_VK 딕셔너리에서 찾는다.
    2) Windows 환경에서 단일 문자이면 VkKeyScanA API로 조회한다.
    3) 위 모두 실패하면 fallback_vk를 반환한다.
    """
    lower = key_name.lower()
    if lower in NAME_TO_VK:
        return NAME_TO_VK[lower]

    # Win32 VkKeyScanA: 단일 ASCII 문자 → VK 코드 변환 (US 레이아웃 기준)
    if sys.platform == "win32" and len(key_name) == 1:
        try:
            import ctypes

            result = ctypes.windll.user32.VkKeyScanA(ord(key_name[0]))
            vk = result & 0xFF
            # VkKeyScanA 실패 시 0xFF 반환
            if vk not in (0x00, 0xFF):
                return vk
        except Exception:
            pass

    return fallback_vk
