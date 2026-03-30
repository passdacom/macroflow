"""Win32 DPI 스케일링 처리.

논리 해상도 조회 및 픽셀 ↔ 비율 좌표 변환을 담당한다.
모듈 임포트 시 SetProcessDpiAwarenessContext를 호출해 DPI Aware로 선언한다.

core-beliefs.md 원칙 4: 좌표는 화면 비율로 정규화해야 DPI 환경 간 재현성이 보장된다.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys

assert sys.platform == "win32", "dpi.py는 Windows에서만 실행 가능합니다"

_user32 = ctypes.windll.user32
_shcore = ctypes.windll.shcore

# ── DPI Aware 선언 ────────────────────────────────────────────────────────────
# DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
# Windows 10 1703+ 필요. 실패 시 SetProcessDPIAware(구형)로 폴백.
try:
    _user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
except (AttributeError, OSError):
    try:
        _user32.SetProcessDPIAware()
    except (AttributeError, OSError):
        pass  # 구형 Windows — 폴백 없음

# SM_CXSCREEN / SM_CYSCREEN: 기본 모니터 논리 해상도
_SM_CXSCREEN = 0
_SM_CYSCREEN = 1


def get_logical_screen_size() -> tuple[int, int]:
    """기본 모니터의 논리 해상도를 반환한다 (DPI 스케일링 보정 후).

    Returns:
        (width, height) 픽셀 단위.
    """
    w: int = _user32.GetSystemMetrics(_SM_CXSCREEN)
    h: int = _user32.GetSystemMetrics(_SM_CYSCREEN)
    return (w, h)


def get_dpi_scale() -> float:
    """시스템 DPI 배율을 반환한다 (96dpi 기준 1.0).

    Returns:
        DPI 배율. 예: 125% DPI → 1.25
    """
    try:
        dpi: int = _user32.GetDpiForSystem()
        return dpi / 96.0
    except (AttributeError, OSError):
        return 1.0


def pixel_to_ratio(x: int, y: int) -> tuple[float, float]:
    """픽셀 절대 좌표를 화면 크기 대비 비율로 변환한다.

    core-beliefs.md 원칙 4 — 녹화 시 비율로 저장, 재생 시 현재 해상도로 역변환.

    Args:
        x: 화면 X 좌표 (픽셀).
        y: 화면 Y 좌표 (픽셀).

    Returns:
        (x_ratio, y_ratio) 각각 0.0~1.0.
    """
    w, h = get_logical_screen_size()
    return (x / w, y / h)


def ratio_to_pixel(x_ratio: float, y_ratio: float) -> tuple[int, int]:
    """화면 비율 좌표를 현재 해상도의 픽셀 좌표로 변환한다.

    Args:
        x_ratio: X 좌표 비율 (0.0~1.0).
        y_ratio: Y 좌표 비율 (0.0~1.0).

    Returns:
        (x, y) 픽셀 좌표.
    """
    w, h = get_logical_screen_size()
    return (int(x_ratio * w), int(y_ratio * h))
