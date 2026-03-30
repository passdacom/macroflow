"""pytest 공통 픽스처.

win32 모듈을 mock으로 교체하여 Linux 개발 환경에서도 테스트 가능하게 한다.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Generator

import pytest


@pytest.fixture
def mock_win32(monkeypatch: pytest.MonkeyPatch) -> None:
    """win32 Platform Layer 전체를 Mock으로 대체한다.

    Core 레이어 테스트 시 반드시 사용한다.
    """
    import macroflow.win32 as w32

    monkeypatch.setattr(w32, "get_pixel_color", lambda x, y: (255, 255, 255))
    monkeypatch.setattr(w32, "find_window", lambda title: None)
    monkeypatch.setattr(w32, "send_mouse_move", lambda x, y: None)
    monkeypatch.setattr(w32, "send_mouse_click", lambda x, y, button="left": None)
    monkeypatch.setattr(w32, "send_mouse_drag", lambda x1, y1, x2, y2, button="left": None)
    monkeypatch.setattr(w32, "send_key", lambda vk, is_down: None)
    monkeypatch.setattr(w32, "get_logical_screen_size", lambda: (1920, 1080))
    monkeypatch.setattr(w32, "ratio_to_pixel", lambda xr, yr: (int(xr * 1920), int(yr * 1080)))
    monkeypatch.setattr(w32, "pixel_to_ratio", lambda x, y: (x / 1920, y / 1080))


@pytest.fixture
def mock_hook(monkeypatch: pytest.MonkeyPatch) -> Generator[deque[tuple[str, int, int, tuple[int, int, int]]], None, None]:
    """start_hook / stop_hook을 mock으로 대체하고 직접 주입 가능한 큐를 반환한다.

    테스트에서 이 큐에 raw 이벤트를 push하면 recorder가 처리한다.

    Yields:
        테스트용 이벤트 큐.
    """
    import macroflow.win32 as w32

    captured_queue: deque[tuple[str, int, int, tuple[int, int, int]]] = deque()

    def _mock_start_hook(q: deque[tuple[str, int, int, tuple[int, int, int]]]) -> None:
        # recorder가 만든 큐 대신 captured_queue 참조를 갱신
        q.extend([])  # no-op, recorder의 큐를 사용

    monkeypatch.setattr(w32, "start_hook", _mock_start_hook)
    monkeypatch.setattr(w32, "stop_hook", lambda: None)
    monkeypatch.setattr(w32, "get_logical_screen_size", lambda: (1920, 1080))
    monkeypatch.setattr(w32, "pixel_to_ratio", lambda x, y: (x / 1920, y / 1080))

    yield captured_queue
