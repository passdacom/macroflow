"""Win32 API 레이어.

Windows에서는 실제 ctypes 구현을 사용.
Linux/개발 환경(openclaw 등)에서는 Mock을 자동 주입.
Claude Code가 Linux 서버에서 작업할 때도 import 오류 없이 동작한다.
"""

import sys

if sys.platform == "win32":
    from .dpi import get_logical_screen_size, pixel_to_ratio, ratio_to_pixel
    from .hooks import (
        find_window,
        get_cursor_pos,
        get_pixel_color,
        start_emergency_hook,
        start_hook,
        stop_emergency_hook,
        stop_hook,
    )
    from .sendinput import (
        send_key,
        send_mouse_button,
        send_mouse_click,
        send_mouse_drag,
        send_mouse_move,
        send_mouse_wheel,
    )
else:
    # 비-Windows 환경: Mock 자동 주입 (개발·테스트용)
    from .mock import (
        find_window,
        get_cursor_pos,
        get_logical_screen_size,
        get_pixel_color,
        pixel_to_ratio,
        ratio_to_pixel,
        send_key,
        send_mouse_button,
        send_mouse_click,
        send_mouse_drag,
        send_mouse_move,
        send_mouse_wheel,
        start_emergency_hook,
        start_hook,
        stop_emergency_hook,
        stop_hook,
    )

__all__ = [
    "get_cursor_pos",
    "get_pixel_color",
    "start_hook",
    "stop_hook",
    "start_emergency_hook",
    "stop_emergency_hook",
    "find_window",
    "send_mouse_button",
    "send_mouse_click",
    "send_mouse_drag",
    "send_mouse_move",
    "send_mouse_wheel",
    "send_key",
    "get_logical_screen_size",
    "ratio_to_pixel",
    "pixel_to_ratio",
]
