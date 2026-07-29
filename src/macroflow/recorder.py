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
from collections.abc import Callable, Iterable
from datetime import datetime

from macroflow import __version__
from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    KeyEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    TextInputEvent,
)
from macroflow.win32 import (
    get_logical_screen_size,
    get_pixel_color,
    pixel_to_ratio,
    start_hook,
    stop_hook,
)

logger = logging.getLogger(__name__)

# ── 핫키 VK 코드 — 활성 운영 단축키는 raw_events에 기록하지 않는다 ────────────
_DEFAULT_FILTERED_VK_CODES: frozenset[int] = frozenset({0x75, 0x76, 0x77, 0x78})
_filtered_hotkey_vk_codes: frozenset[int] = _DEFAULT_FILTERED_VK_CODES


def configure_filtered_hotkey_vk_codes(vk_codes: set[int] | frozenset[int]) -> None:
    """Atomically replace the runtime hotkeys excluded from recording."""
    normalized = frozenset(vk_codes)
    if any(not isinstance(vk, int) or isinstance(vk, bool) or not 0 <= vk <= 0xFF for vk in normalized):
        raise ValueError("hotkey virtual-key codes must be integers in 0..255")
    global _filtered_hotkey_vk_codes
    _filtered_hotkey_vk_codes = normalized


def filtered_hotkey_vk_codes() -> frozenset[int]:
    """Return the currently active recorder hotkey filter."""
    return _filtered_hotkey_vk_codes

# ── ESC×3 긴급 중지 상수 ─────────────────────────────────────────────────────
_VK_ESCAPE: int = 0x1B
_ESC_WINDOW_SEC: float = 0.5  # 3번 ESC를 0.5초 이내에 누르면 긴급 중지

# ── Win32 메시지 상수 (hooks.py와 동기화) ─────────────────────────────────────
_WM_MOUSEMOVE: int = 0x0200
_WM_LBUTTONDOWN: int = 0x0201
_WM_LBUTTONUP: int = 0x0202
_WM_RBUTTONDOWN: int = 0x0204
_WM_RBUTTONUP: int = 0x0205
_WM_MBUTTONDOWN: int = 0x0207
_WM_MBUTTONUP: int = 0x0208
_WM_MOUSEWHEEL: int = 0x020A   # 수직 휠
_WM_MOUSEHWHEEL: int = 0x020E  # 수평 휠

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
    0x5B: "lwin",      0x5C: "rwin",
    # 숫자패드 (VK_NUMPAD0~9 = 0x60~0x69)
    0x60: "num0", 0x61: "num1", 0x62: "num2", 0x63: "num3", 0x64: "num4",
    0x65: "num5", 0x66: "num6", 0x67: "num7", 0x68: "num8", 0x69: "num9",
    0x6A: "num*", 0x6B: "num+", 0x6D: "num-", 0x6E: "num.", 0x6F: "num/",
    0x90: "numlock", 0x91: "scrolllock",
    0x70: "f1",  0x71: "f2",  0x72: "f3",  0x73: "f4",
    0x74: "f5",  0x75: "f6",  0x76: "f7",  0x77: "f8",
    0x78: "f9",  0x79: "f10", 0x7A: "f11", 0x7B: "f12",
    0x7C: "f13", 0x7D: "f14", 0x7E: "f15", 0x7F: "f16",
    0xA0: "lshift", 0xA1: "rshift",
    0xA2: "lctrl",  0xA3: "rctrl",
    0xA4: "lalt",   0xA5: "ralt",
    # OEM 특수문자 (US 표준 키보드 — ui/editor_keys.py NAME_TO_VK 와 동일한 이름 사용)
    0xBA: ";",   0xBB: "=",   0xBC: ",",   0xBD: "-",   0xBE: ".",
    0xBF: "/",   0xC0: "`",
    0xDB: "[",   0xDC: "\\",  0xDD: "]",   0xDE: "'",
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
_RawEvent = tuple[str, int, int, tuple[int, int, int]]
_CaptureItem = _RawEvent | AnyEvent
_raw_queue: deque[_CaptureItem] | None = None
_consumer_thread: threading.Thread | None = None
_stop_consumer: threading.Event = threading.Event()
_event_buffer: list[AnyEvent] = []
_event_buffer_lock: threading.Lock = threading.Lock()  # _event_buffer 동시 접근 보호
_rec_start_ns: int = 0
_pause_lock: threading.Lock = threading.Lock()
_pause_intervals: list[tuple[int, int]] = []
_pause_started_ns: int | None = None
_recording_pressed_keys: set[int] = set()
_recording_pressed_mouse: set[str] = set()
_suppressed_pause_keys: set[int] = set()
_suppressed_pause_mouse: set[str] = set()
_suppressed_release_groups: list[frozenset[int]] = []
_screen_w: int = 1920
_screen_h: int = 1080
_esc_press_times: deque[float] = deque(maxlen=3)
_on_emergency_stop: Callable[[], None] | None = None


def _project_recording_timestamp_ns(captured_ns: int) -> int | None:
    """캡처 시각을 pause 구간이 제거된 녹화 상대시각으로 변환한다.

    consumer 처리 시각이 아니라 Hook이 기록한 ``captured_ns``를 사용하므로,
    pause 직전 queue에 들어온 이벤트는 consumer가 늦게 처리해도 보존된다.
    pause 구간 안에서 캡처된 이벤트는 ``None``을 반환한다.
    """
    paused_before_ns = 0
    with _pause_lock:
        intervals = tuple(_pause_intervals)
        open_pause_start_ns = _pause_started_ns

    for start_ns, end_ns in intervals:
        if captured_ns < start_ns:
            break
        if captured_ns < end_ns:
            return None
        paused_before_ns += end_ns - start_ns

    if open_pause_start_ns is not None and captured_ns >= open_pause_start_ns:
        return None
    return max(0, captured_ns - _rec_start_ns - paused_before_ns)


def _pause_boundary_for(captured_ns: int) -> int | None:
    """captured_ns가 속한 pause interval의 시작 시각을 반환한다."""
    with _pause_lock:
        for start_ns, end_ns in _pause_intervals:
            if start_ns <= captured_ns < end_ns:
                return start_ns
        if _pause_started_ns is not None and captured_ns >= _pause_started_ns:
            return _pause_started_ns
    return None


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
    rel_ts_ns = _project_recording_timestamp_ns(ts_ns)
    if rel_ts_ns is None:
        return None
    eid = secrets.token_hex(4)

    if kind == "m":
        x_px, y_px, mouse_data = data
        x_ratio, y_ratio = pixel_to_ratio(x_px, y_px)

        if wParam == _WM_MOUSEMOVE:
            return MouseMoveEvent(
                id=eid, type="mouse_move",
                timestamp_ns=rel_ts_ns,
                x_ratio=x_ratio, y_ratio=y_ratio,
            )
        if wParam in _MOUSE_DOWN_MAP:
            # 클릭 시 해당 픽셀 색을 함께 저장 (색 체크 기능에 활용)
            r, g, b = get_pixel_color(x_px, y_px)
            recorded_color = f"#{r:02X}{g:02X}{b:02X}"
            return MouseButtonEvent(
                id=eid, type="mouse_down",
                timestamp_ns=rel_ts_ns,
                x_ratio=x_ratio, y_ratio=y_ratio,
                button=_MOUSE_DOWN_MAP[wParam],  # type: ignore[arg-type]
                recorded_color=recorded_color,
            )
        if wParam in _MOUSE_UP_MAP:
            return MouseButtonEvent(
                id=eid, type="mouse_up",
                timestamp_ns=rel_ts_ns,
                x_ratio=x_ratio, y_ratio=y_ratio,
                button=_MOUSE_UP_MAP[wParam],  # type: ignore[arg-type]
            )
        if wParam in (_WM_MOUSEWHEEL, _WM_MOUSEHWHEEL):
            # mouseData 상위 16비트 = 휠 델타 (부호 있는 short)
            raw_word = (mouse_data >> 16) & 0xFFFF
            delta = raw_word if raw_word < 0x8000 else raw_word - 0x10000
            axis = "vertical" if wParam == _WM_MOUSEWHEEL else "horizontal"
            return MouseWheelEvent(
                id=eid, type="mouse_wheel",
                timestamp_ns=rel_ts_ns,
                delta=delta,
                axis=axis,
                x_ratio=x_ratio, y_ratio=y_ratio,
            )

    elif kind == "k":
        vk_code, _scan, _flags = data
        # 핫키(F6, F7, F8)는 기록하지 않는다
        if vk_code in _filtered_hotkey_vk_codes:
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


def _check_esc_triple(raw: tuple[str, int, int, tuple[int, int, int]]) -> bool:
    """ESC key_down 3번 연속(0.5초 이내) 감지 시 True를 반환한다."""
    kind, _ts_ns, wParam, data = raw
    if kind != "k":
        return False
    vk_code = data[0]
    if vk_code != _VK_ESCAPE:
        return False
    if wParam not in (_WM_KEYDOWN, _WM_SYSKEYDOWN):
        return False
    _esc_press_times.append(time.monotonic())
    if (len(_esc_press_times) == 3
            and _esc_press_times[-1] - _esc_press_times[0] <= _ESC_WINDOW_SEC):
        _esc_press_times.clear()
        return True
    return False


def _consumer_loop() -> None:
    """deque에서 원시 이벤트를 소비하여 _event_buffer에 쌓는다."""
    while not _stop_consumer.is_set():
        if _raw_queue and len(_raw_queue) > 0:
            raw = _raw_queue.popleft()
            if not isinstance(raw, tuple):
                with _event_buffer_lock:
                    _event_buffer.append(raw)
                continue
            # ESC×3 긴급 중지 감지 (포커스 무관)
            if _check_esc_triple(raw):
                logger.info("ESC×3 긴급 중지 감지 (LL Hook)")
                if _on_emergency_stop is not None:
                    _on_emergency_stop()
                continue
            event = _process_raw(raw)
            if event is not None:
                with _event_buffer_lock:
                    _event_buffer.append(event)
        else:
            time.sleep(0.001)  # 1ms 폴링

    # 종료 신호 후 잔여 이벤트 처리
    while _raw_queue and len(_raw_queue) > 0:
        raw = _raw_queue.popleft()
        event = raw if not isinstance(raw, tuple) else _process_raw(raw)
        if event is not None:
            with _event_buffer_lock:
                _event_buffer.append(event)


def _process_raw(
    raw: tuple[str, int, int, tuple[int, int, int]],
) -> AnyEvent | None:
    """pause 경계의 열린 입력 쌍을 보존하면서 raw 이벤트를 변환한다."""
    kind, captured_ns, w_param, data = raw
    pause_boundary_ns = _pause_boundary_for(captured_ns)

    if kind == "k":
        vk_code = data[0]
        is_down = w_param in (_WM_KEYDOWN, _WM_SYSKEYDOWN)
        is_up = w_param in (_WM_KEYUP, _WM_SYSKEYUP)
        with _pause_lock:
            release_group = next(
                (group for group in _suppressed_release_groups if vk_code in group),
                None,
            )
            if release_group is not None:
                _suppressed_release_groups.remove(release_group)
        if (
            release_group is not None
            and is_up
            and not any(code in _recording_pressed_keys for code in release_group)
        ):
            _suppressed_pause_keys.difference_update(release_group)
            return None
        if pause_boundary_ns is not None:
            if is_down:
                if vk_code not in _recording_pressed_keys:
                    _suppressed_pause_keys.add(vk_code)
                return None
            if is_up:
                if vk_code in _suppressed_pause_keys:
                    _suppressed_pause_keys.discard(vk_code)
                    return None
                if vk_code in _recording_pressed_keys:
                    forced = (kind, pause_boundary_ns - 1, w_param, data)
                    _recording_pressed_keys.discard(vk_code)
                    return _convert_raw(forced)
                return None
        if (is_down or is_up) and vk_code in _suppressed_pause_keys:
            if is_up:
                _suppressed_pause_keys.discard(vk_code)
            return None
        event = _convert_raw(raw)
        if event is not None:
            if is_down:
                _recording_pressed_keys.add(vk_code)
            elif is_up:
                _recording_pressed_keys.discard(vk_code)
        return event

    if kind == "m":
        button = _MOUSE_DOWN_MAP.get(w_param) or _MOUSE_UP_MAP.get(w_param)
        is_down = w_param in _MOUSE_DOWN_MAP
        is_up = w_param in _MOUSE_UP_MAP
        if pause_boundary_ns is not None and button is not None:
            if is_down:
                if button not in _recording_pressed_mouse:
                    _suppressed_pause_mouse.add(button)
                return None
            if is_up:
                if button in _suppressed_pause_mouse:
                    _suppressed_pause_mouse.discard(button)
                    return None
                if button in _recording_pressed_mouse:
                    forced = (kind, pause_boundary_ns - 1, w_param, data)
                    _recording_pressed_mouse.discard(button)
                    return _convert_raw(forced)
                return None
        if button is not None and (is_down or is_up) and button in _suppressed_pause_mouse:
            if is_up:
                _suppressed_pause_mouse.discard(button)
            return None
        event = _convert_raw(raw)
        if event is not None and button is not None:
            if is_down:
                _recording_pressed_mouse.add(button)
            elif is_up:
                _recording_pressed_mouse.discard(button)
        return event

    return _convert_raw(raw)


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────

def start_recording(
    on_emergency_stop: Callable[[], None] | None = None,
) -> None:
    """LL Hook을 등록하고 이벤트 캡처를 시작한다.

    Args:
        on_emergency_stop: ESC×3 감지 시 호출할 콜백.
            consumer 스레드에서 호출되므로 Qt Signal 등 스레드 안전한 방법을 사용할 것.

    이미 녹화 중이면 무시된다.
    """
    global _recording, _raw_queue, _consumer_thread
    global _stop_consumer, _event_buffer, _rec_start_ns
    global _screen_w, _screen_h, _on_emergency_stop
    global _pause_intervals, _pause_started_ns

    if _recording:
        logger.warning("Already recording — start_recording() ignored")
        return

    _on_emergency_stop = on_emergency_stop
    _esc_press_times.clear()
    _screen_w, _screen_h = get_logical_screen_size()
    _event_buffer = []
    _raw_queue = deque()
    _stop_consumer = threading.Event()
    _rec_start_ns = time.perf_counter_ns()
    with _pause_lock:
        _pause_intervals = []
        _pause_started_ns = None
        _suppressed_release_groups.clear()
    _recording_pressed_keys.clear()
    _recording_pressed_mouse.clear()
    _suppressed_pause_keys.clear()
    _suppressed_pause_mouse.clear()

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
    global _recording, _consumer_thread, _on_emergency_stop

    if not _recording:
        raise RuntimeError("stop_recording() called while not recording")

    _on_emergency_stop = None
    stop_hook()
    # Hook이 완전히 해제된 뒤 열린 pause를 닫아 stop 과정에서 캡처될 수 있는
    # 마지막 이벤트까지 pause 구간으로 분류한다.
    if is_paused():
        resume_recording(now_ns=time.perf_counter_ns())
    _stop_consumer.set()

    if _consumer_thread is not None:
        _consumer_thread.join(timeout=3.0)
        _consumer_thread = None

    _recording = False
    with _event_buffer_lock:
        captured = list(_event_buffer)
    logger.debug(f"Recording stopped — {len(captured)} events captured")

    raw_events: list[AnyEvent] = captured
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


def inject_color_trigger(
    x_ratio: float,
    y_ratio: float,
    color_hex: str,
    *,
    timeout_ms: int = 0,
    check_interval_ms: int = 50,
) -> None:
    """녹화 중 현재 시각에 ColorTriggerEvent를 이벤트 버퍼에 직접 삽입한다.

    녹화 중이 아니면 무시된다.

    Args:
        x_ratio: 감지할 픽셀의 X 좌표 비율 (0.0~1.0).
        y_ratio: 감지할 픽셀의 Y 좌표 비율 (0.0~1.0).
        color_hex: 기다릴 목표 색상 (#RRGGBB 형식).
        timeout_ms: 최대 대기 시간. 0 이하면 무제한 대기.
        check_interval_ms: 픽셀 색 폴링 주기.
    """
    if not _recording:
        return
    ts_ns = _project_recording_timestamp_ns(time.perf_counter_ns())
    if ts_ns is None:
        return
    event = ColorTriggerEvent(
        id=secrets.token_hex(4),
        type="color_trigger",
        timestamp_ns=ts_ns,
        x_ratio=x_ratio,
        y_ratio=y_ratio,
        target_color=color_hex,
        tolerance=10,
        timeout_ms=timeout_ms,
        check_interval_ms=check_interval_ms,
        on_timeout="skip",
    )
    with _event_buffer_lock:
        _event_buffer.append(event)
    logger.info(f"ColorTriggerEvent 삽입: {color_hex} @ ({x_ratio:.3f}, {y_ratio:.3f})")


def inject_text_input(
    text: str,
    *,
    delay_override_ms: int | None = None,
) -> bool:
    """열린 pause 경계에 TextInputEvent를 ordered capture stream으로 삽입한다."""
    if not _recording or not text or _raw_queue is None:
        return False
    with _pause_lock:
        pause_started_ns = _pause_started_ns
        intervals = tuple(_pause_intervals)
    if pause_started_ns is None:
        return False

    paused_before_ns = sum(end_ns - start_ns for start_ns, end_ns in intervals)
    timestamp_ns = max(0, pause_started_ns - _rec_start_ns - paused_before_ns)
    _raw_queue.append(
        TextInputEvent(
            id=secrets.token_hex(4),
            type="text_input",
            timestamp_ns=timestamp_ns,
            delay_override_ms=delay_override_ms,
            text=text,
        )
    )
    logger.info("TextInputEvent 삽입")
    return True


def suppress_next_key_release(vk_codes: Iterable[int]) -> None:
    """Suppress one trailing key-up from a just-finished paused UI gesture.

    ``vk_codes`` may contain generic/left/right variants of the same modifier.
    The first matching transition consumes the whole group: a key-up is dropped,
    while a new key-down merely clears the fence and is recorded normally.
    """
    group = frozenset(vk_codes)
    if not group:
        return
    with _pause_lock:
        if group not in _suppressed_release_groups:
            _suppressed_release_groups.append(group)


def is_recording() -> bool:
    """현재 녹화 중인지 여부를 반환한다."""
    return _recording


def pause_recording(*, now_ns: int | None = None) -> bool:
    """현재 녹화를 일시중지한다.

    Hook은 유지하고 캡처 timestamp가 pause 구간에 속한 이벤트만 폐기한다.
    이미 중지됐거나 pause 상태이면 ``False``를 반환한다.
    """
    global _pause_started_ns
    if not _recording:
        return False
    with _pause_lock:
        if _pause_started_ns is not None:
            return False
        boundary_ns = time.perf_counter_ns() if now_ns is None else now_ns
        _pause_started_ns = boundary_ns
    logger.debug("Recording paused")
    return True


def resume_recording(*, now_ns: int | None = None) -> bool:
    """일시중지된 녹화를 재개하고 닫힌 pause interval을 기록한다."""
    global _pause_started_ns
    with _pause_lock:
        if _pause_started_ns is None:
            return False
        boundary_ns = time.perf_counter_ns() if now_ns is None else now_ns
        end_ns = max(boundary_ns, _pause_started_ns)
        _pause_intervals.append((_pause_started_ns, end_ns))
        _pause_started_ns = None
    logger.debug("Recording resumed")
    return True


def is_paused() -> bool:
    """녹화가 현재 일시중지 상태인지 반환한다."""
    with _pause_lock:
        return _recording and _pause_started_ns is not None


def get_event_count() -> int:
    """현재까지 캡처된 이벤트 수를 반환한다 (녹화 중 폴링용)."""
    return len(_event_buffer)
