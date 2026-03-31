"""Win32 Mock 구현 — Linux/개발 환경용.

openclaw 같은 Linux 서버에서 Claude Code가 작업할 때 자동으로 사용됨.
실제 Win32 API를 호출하지 않고 로그만 남긴다.
pytest에서 이 모듈을 monkeypatch 없이 바로 사용 가능.
"""

from __future__ import annotations

import logging
from collections import deque

logger = logging.getLogger(__name__)


# ── 이벤트 캡처 ──────────────────────────────────────────

def start_hook(queue: deque) -> None:  # type: ignore[type-arg]
    """Hook 등록 Mock — 아무것도 하지 않음."""
    logger.debug("[Mock] start_hook called (no-op on non-Windows)")


def stop_hook() -> None:
    """Hook 해제 Mock."""
    logger.debug("[Mock] stop_hook called (no-op on non-Windows)")


# ── 픽셀 색 감지 ─────────────────────────────────────────

# 테스트에서 원하는 색을 주입할 수 있는 설정값
_mock_pixel_color: tuple[int, int, int] = (255, 255, 255)

def set_mock_pixel_color(r: int, g: int, b: int) -> None:
    """테스트에서 GetPixel 반환값을 제어하기 위한 헬퍼."""
    global _mock_pixel_color
    _mock_pixel_color = (r, g, b)


def get_pixel_color(x: int, y: int) -> tuple[int, int, int]:
    """GetPixel Mock — 설정된 색 반환."""
    logger.debug(f"[Mock] get_pixel_color({x}, {y}) → {_mock_pixel_color}")
    return _mock_pixel_color


# ── 커서 위치 ─────────────────────────────────────────────

_mock_cursor_pos: tuple[int, int] = (0, 0)


def get_cursor_pos() -> tuple[int, int]:
    """GetCursorPos Mock — 설정된 커서 위치 반환."""
    logger.debug(f"[Mock] get_cursor_pos() → {_mock_cursor_pos}")
    return _mock_cursor_pos


# ── 긴급 중지 Hook ────────────────────────────────────────

def start_emergency_hook(callback: object) -> None:
    """긴급 중지 Hook Mock — 아무것도 하지 않음."""
    logger.debug("[Mock] start_emergency_hook called (no-op on non-Windows)")


def stop_emergency_hook() -> None:
    """긴급 중지 Hook 해제 Mock."""
    logger.debug("[Mock] stop_emergency_hook called (no-op on non-Windows)")


# ── 창 감지 ──────────────────────────────────────────────

def find_window(title_contains: str) -> int | None:
    """FindWindow Mock — 항상 None 반환."""
    logger.debug(f"[Mock] find_window('{title_contains}') → None")
    return None


# ── 입력 재생 ─────────────────────────────────────────────

def send_mouse_move(x: int, y: int) -> None:
    logger.debug(f"[Mock] send_mouse_move({x}, {y})")


def send_mouse_click(x: int, y: int, button: str = "left") -> None:
    logger.debug(f"[Mock] send_mouse_click({x}, {y}, {button})")


def send_mouse_button(x: int, y: int, button: str, down: bool) -> None:
    logger.debug(f"[Mock] send_mouse_button({x}, {y}, {button}, down={down})")


def send_mouse_drag(x1: int, y1: int, x2: int, y2: int, button: str = "left") -> None:
    logger.debug(f"[Mock] send_mouse_drag({x1},{y1} → {x2},{y2})")


def send_key(vk_code: int, is_down: bool) -> None:
    logger.debug(f"[Mock] send_key(vk={vk_code:#04x}, down={is_down})")


# ── DPI / 해상도 ──────────────────────────────────────────

_mock_screen_size: tuple[int, int] = (1920, 1080)

def get_logical_screen_size() -> tuple[int, int]:
    """GetSystemMetrics Mock — 기본 1920×1080."""
    return _mock_screen_size


def ratio_to_pixel(x_ratio: float, y_ratio: float) -> tuple[int, int]:
    w, h = _mock_screen_size
    return (int(x_ratio * w), int(y_ratio * h))


def pixel_to_ratio(x: int, y: int) -> tuple[float, float]:
    w, h = _mock_screen_size
    return (x / w, y / h)
