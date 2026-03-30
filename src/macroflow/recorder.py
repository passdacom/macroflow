"""MacroFlow 이벤트 캡처 엔진.

Win32 LL Hook (WH_MOUSE_LL + WH_KEYBOARD_LL)으로 캡처한 원시 이벤트를
MacroEvent 객체로 변환하여 MacroData를 반환한다.

core-beliefs.md 원칙 1: 녹화는 무손실. 클릭/드래그 판별 금지.
core-beliefs.md 원칙 2: 이벤트 순서는 OS가 보장. 재정렬 금지.
core-beliefs.md 원칙 4: 좌표를 화면 비율로 정규화.
"""

from __future__ import annotations

import copy
import logging
import secrets
import threading
import time
from collections import deque
from datetime import datetime

from macroflow import __version__
from macroflow.types import (
    AnyEvent,
    KeyEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
)
from macroflow.win32 import (
    get_logical_screen_size,
    pixel_to_ratio,
    start_hook,
    stop_hook,
)

logger = logging.getLogger(__name__)

# ── 핫키 VK 코드 — 이 키들은 raw_events에 기록하지 않는다 ─────────────────────
# spec: 단축키 자체(F6 key_down/key_up)는 raw_events에 기록하지 않음
_FILTERED_VK_CODES: frozenset[int] = frozenset({0x75, 0x76})  # F6, F7

# ── Win32 메시지 상수 (hooks.py와 동기화) ─────────────────────────────────────
_WM_MOUSEMOVE: int = 0x0200
_WM_LBUTTONDOWN: int = 0x0201
_WM_LBUTTONUP: int = 0x0202
_WM_RBUTTONDOWN: int = 0x0204
_WM_RBUTTONUP: int = 0x0205
_WM_MBUTTONDOWN: int = 0x0207
_WM_MBUTTONUP: int = 0x0208

_WM_KEYDOWN: int = 0x0100
_WM_KEYUP: int = 0x0101
_WM_SYSKEYDOWN: int = 0x0104
_WM_SYSKEYUP: int = 0x0105

_MOUSE_DOWN_MAP: dict[int, str] = {
    _WM_LBUTTONDOWN: "left",
    _WM_RBUTTONDOWN: "right",
    _WM_MBUTTONDOWN: "middle",
}
_MOUSE_UP_MAP: dict[int, str] = {
    _WM_LBUTTONUP: "left",
    _WM_RBUTTONUP: "right",
    _WM_MBUTTONUP: "middle",
}

# ── VK 코드 → 키 이름 매핑 ────────────────────────────────────────────────────
_VK_NAMES: dict[int, str] = {
    0x08: "backspace", 0x09: "tab",      0x0D: "enter",
    0x10: "shift",     0x11: "ctrl",     0x12: "alt",
    0x13: "pause",     0x14: "capslock", 0x1B: "escape",
    0x20: "space",
    0x21: "pageup",    0x22: "pagedown", 0x23: "end",    0x24: "home",
    0x25: "left",      0x26: "up",       0x27: "right",  0x28: "down",
    0x2C: "printscreen", 0x2D: "insert", 0x2E: "delete",
    0x5B: "win_left",  0x5C: "win_right",
    0x70: "f1",  0x71: "f2",  0x72: "f3",  0x73: "f4",
    0x74: "f5",  0x75: "f6",  0x76: "f7",  0x77: "f8",
    0x78: "f9",  0x79: "f10", 0x7A: "f11", 0x7B: "f12",
    0xA0: "shift_left", 0xA1: "shift_right",
    0xA2: "ctrl_left",  0xA3: "ctrl_right",
    0xA4: "alt_left",   0xA5: "alt_right",
    0xBB: "equal",    0xBC: "comma",  0xBD: "minus",  0xBE: "period",
    0xBF: "slash",    0xC0: "backtick",
    0xDB: "bracket_left", 0xDC: "backslash",
    0xDD: "bracket_right", 0xDE: "quote",
}


def _vk_to_key(vk_code: int) -> str:
    """VK 코드를 사람이 읽을 수 있는 키 이름으로 변환한다."""
    if vk_code in _VK_NAMES:
        return _VK_NAMES[vk_code]
    if 0x30 <= vk_code <= 0x39:
        return chr(vk_code)          # '0'~'9'
    if 0x41 <= vk_code <= 0x5A:
        return chr(vk_code + 32)     # 'a'~'z'
    return f"vk_{vk_code:#04x}"


# ── 모듈 레벨 상태 ────────────────────────────────────────────────────────────
_recording: bool = False
_raw_queue: deque[tuple[str, int, int, tuple[int, int, int]]] | None = None
_consumer_thread: threading.Thread | None = None
_stop_consumer: threading.Event = threading.Event()
_event_buffer: list[AnyEvent] = []
_rec_start_ns: int = 0
_screen_w: int = 1920
_screen_h: int = 1080


def _convert_raw(
    raw: tuple[str, int, int, tuple[int, int, int]],
) -> AnyEvent | None:
    """원시 Hook 이벤트를 MacroEvent 객체로 변환한다.

    Args:
        raw: hooks.py에서 push한 (kind, ts_ns, wParam, data) 튜플.

    Returns:
        변환된 이벤트. 알 수 없는 wParam이면 None.
    """
    kind, ts_ns, wParam, data = raw
    rel_ts_ns = ts_ns - _rec_start_ns
    eid = secrets.token_hex(4)

    if kind == "m":
        x_px, y_px, _ = data
        x_ratio, y_ratio = pixel_to_ratio(x_px, y_px)

        if wParam == _WM_MOUSEMOVE:
            return MouseMoveEvent(
                id=eid, type="mouse_move",
                timestamp_ns=rel_ts_ns,
                x_ratio=x_ratio, y_ratio=y_ratio,
            )
        if wParam in _MOUSE_DOWN_MAP:
            return MouseButtonEvent(
                id=eid, type="mouse_down",
                timestamp_ns=rel_ts_ns,
                x_ratio=x_ratio, y_ratio=y_ratio,
                button=_MOUSE_DOWN_MAP[wParam],  # type: ignore[arg-type]
            )
        if wParam in _MOUSE_UP_MAP:
            return MouseButtonEvent(
                id=eid, type="mouse_up",
                timestamp_ns=rel_ts_ns,
                x_ratio=x_ratio, y_ratio=y_ratio,
                button=_MOUSE_UP_MAP[wParam],  # type: ignore[arg-type]
            )

    elif kind == "k":
        vk_code, _scan, _flags = data
        # 핫키(F6, F7)는 기록하지 않는다
        if vk_code in _FILTERED_VK_CODES:
            return None
        if wParam in (_WM_KEYDOWN, _WM_SYSKEYDOWN):
            return KeyEvent(
                id=eid, type="key_down",
                timestamp_ns=rel_ts_ns,
                key=_vk_to_key(vk_code), vk_code=vk_code,
            )
        if wParam in (_WM_KEYUP, _WM_SYSKEYUP):
            return KeyEvent(
                id=eid, type="key_up",
                timestamp_ns=rel_ts_ns,
                key=_vk_to_key(vk_code), vk_code=vk_code,
            )

    return None


def _consumer_loop() -> None:
    """deque에서 원시 이벤트를 소비하여 _event_buffer에 쌓는다."""
    while not _stop_consumer.is_set():
        if _raw_queue and len(_raw_queue) > 0:
            raw = _raw_queue.popleft()
            event = _convert_raw(raw)
            if event is not None:
                _event_buffer.append(event)
        else:
            time.sleep(0.001)  # 1ms 폴링

    # 종료 신호 후 잔여 이벤트 처리
    while _raw_queue and len(_raw_queue) > 0:
        raw = _raw_queue.popleft()
        event = _convert_raw(raw)
        if event is not None:
            _event_buffer.append(event)


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────

def start_recording() -> None:
    """LL Hook을 등록하고 이벤트 캡처를 시작한다.

    이미 녹화 중이면 무시된다.
    """
    global _recording, _raw_queue, _consumer_thread
    global _stop_consumer, _event_buffer, _rec_start_ns
    global _screen_w, _screen_h

    if _recording:
        logger.warning("Already recording — start_recording() ignored")
        return

    _screen_w, _screen_h = get_logical_screen_size()
    _event_buffer = []
    _raw_queue = deque()
    _stop_consumer = threading.Event()
    _rec_start_ns = time.perf_counter_ns()

    start_hook(_raw_queue)

    _consumer_thread = threading.Thread(
        target=_consumer_loop, daemon=True, name="RecorderConsumer"
    )
    _consumer_thread.start()
    _recording = True
    logger.debug("Recording started")


def stop_recording() -> MacroData:
    """녹화를 중지하고 캡처된 전체 이벤트를 MacroData로 반환한다.

    Returns:
        raw_events == events (is_edited=False)인 MacroData.

    Raises:
        RuntimeError: 녹화 중이 아닌 상태에서 호출.
    """
    global _recording, _consumer_thread

    if not _recording:
        raise RuntimeError("stop_recording() called while not recording")

    stop_hook()
    _stop_consumer.set()

    if _consumer_thread is not None:
        _consumer_thread.join(timeout=3.0)
        _consumer_thread = None

    _recording = False
    logger.debug(f"Recording stopped — {len(_event_buffer)} events captured")

    raw_events: list[AnyEvent] = list(_event_buffer)
    events: list[AnyEvent] = copy.deepcopy(raw_events)

    return MacroData(
        meta=MacroMeta(
            version="1.0",
            app_version=__version__,
            created_at=datetime.now().isoformat(timespec="seconds"),
            screen_width=_screen_w,
            screen_height=_screen_h,
            dpi_scale=_screen_w / 1920.0,  # 단순 추정; dpi.get_dpi_scale()로 대체 가능
        ),
        settings=MacroSettings(),
        raw_events=raw_events,
        events=events,
    )


def is_recording() -> bool:
    """현재 녹화 중인지 여부를 반환한다."""
    return _recording


def get_event_count() -> int:
    """현재까지 캡처된 이벤트 수를 반환한다 (녹화 중 폴링용)."""
    return len(_event_buffer)
