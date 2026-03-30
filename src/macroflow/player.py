"""MacroFlow 재생 엔진.

절대 타임스탬프 기준 재생과 드리프트 보정을 구현한다.
click/drag 판별은 settings 임계값으로 재생 시점에 수행한다.

core-beliefs.md 원칙 1: 클릭/드래그 판별은 재생 시점에.
core-beliefs.md 원칙 3: time.sleep(delta) 반복 금지 — 절대 타임스탬프 기준.
core-beliefs.md 원칙 5: SendInput 직접 호출.
"""

from __future__ import annotations

import dataclasses
import logging
import math
import threading
import time
from collections.abc import Callable

from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    ConditionEvent,
    KeyEvent,
    LoopEvent,
    MacroData,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    WaitEvent,
    WindowTriggerEvent,
)
from macroflow.win32 import (
    find_window,
    get_pixel_color,
    ratio_to_pixel,
    send_key,
    send_mouse_button,
    send_mouse_drag,
    send_mouse_move,
)

logger = logging.getLogger(__name__)


class PlaybackError(Exception):
    """재생 중 복구 불가 오류."""


# ── 재생 상태 추적 ────────────────────────────────────────────────────────────

@dataclasses.dataclass
class _PlayState:
    """재생 중 클릭/드래그 판별에 사용하는 상태."""

    pending_down: MouseButtonEvent | None = None
    pending_down_real_x: int = 0
    pending_down_real_y: int = 0
    pending_down_time_ns: int = 0
    has_moves_since_down: bool = False


# ── 모듈 레벨 상태 ────────────────────────────────────────────────────────────
_playback_thread: threading.Thread | None = None
_stop_flag: threading.Event = threading.Event()
_pause_flag: threading.Event = threading.Event()
_current_event_idx: int = 0
_total_events: int = 0


# ── 이벤트 실행 ───────────────────────────────────────────────────────────────

def _execute_event(
    event: AnyEvent,
    settings: MacroSettings,
    state: _PlayState,
) -> None:
    """단일 이벤트를 실행한다.

    Args:
        event: 실행할 이벤트.
        settings: click/drag 판별 임계값.
        state: 클릭/드래그 판별용 재생 상태.
    """
    if isinstance(event, MouseButtonEvent):
        x, y = ratio_to_pixel(event.x_ratio, event.y_ratio)

        if event.type == "mouse_down":
            send_mouse_move(x, y)
            send_mouse_button(x, y, event.button, down=True)
            state.pending_down = event
            state.pending_down_real_x = x
            state.pending_down_real_y = y
            state.pending_down_time_ns = time.perf_counter_ns()
            state.has_moves_since_down = False

        else:  # mouse_up
            if state.pending_down is not None and not state.has_moves_since_down:
                dist = math.hypot(
                    x - state.pending_down_real_x,
                    y - state.pending_down_real_y,
                )
                elapsed_ms = (
                    (time.perf_counter_ns() - state.pending_down_time_ns)
                    / 1_000_000
                )
                if (
                    dist >= settings.click_dist_threshold_px
                    or elapsed_ms >= settings.click_time_threshold_ms
                ):
                    # 이동 없이 거리/시간 초과 → 드래그로 판별
                    send_mouse_drag(
                        state.pending_down_real_x,
                        state.pending_down_real_y,
                        x, y,
                        event.button,
                    )
                    state.pending_down = None
                    return

            send_mouse_move(x, y)
            send_mouse_button(x, y, event.button, down=False)
            state.pending_down = None

    elif isinstance(event, MouseMoveEvent):
        x, y = ratio_to_pixel(event.x_ratio, event.y_ratio)
        send_mouse_move(x, y)
        state.has_moves_since_down = True

    elif isinstance(event, KeyEvent):
        send_key(event.vk_code, is_down=(event.type == "key_down"))

    elif isinstance(event, WaitEvent):
        time.sleep(event.duration_ms / 1000.0)

    elif isinstance(event, ColorTriggerEvent):
        _wait_for_color(event)

    elif isinstance(event, WindowTriggerEvent):
        _wait_for_window(event)

    elif isinstance(event, (ConditionEvent, LoopEvent)):
        # script_engine.py에서 처리 (M5 이후)
        logger.warning(f"ConditionEvent/LoopEvent not yet implemented: {event.type}")


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """#RRGGBB 문자열을 (R, G, B) 튜플로 변환한다."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _color_matches(
    actual: tuple[int, int, int],
    target: tuple[int, int, int],
    tolerance: int,
) -> bool:
    """실제 색과 목표 색의 각 채널 차이가 tolerance 이내인지 확인한다."""
    return all(abs(a - t) <= tolerance for a, t in zip(actual, target, strict=False))


def _wait_for_color(event: ColorTriggerEvent) -> None:
    """목표 픽셀 색이 나타날 때까지 폴링한다.

    Raises:
        PlaybackError: on_timeout=="error"이고 타임아웃 발생 시.
    """
    x, y = ratio_to_pixel(event.x_ratio, event.y_ratio)
    target = _hex_to_rgb(event.target_color)
    deadline_ns = time.perf_counter_ns() + event.timeout_ms * 1_000_000
    interval_s = event.check_interval_ms / 1000.0

    while time.perf_counter_ns() < deadline_ns:
        if _stop_flag.is_set():
            return
        actual = get_pixel_color(x, y)
        if _color_matches(actual, target, event.tolerance):
            return
        time.sleep(interval_s)

    # 타임아웃
    msg = f"color_trigger timeout at ({x},{y}) waiting for {event.target_color}"
    if event.on_timeout == "error":
        raise PlaybackError(msg)
    elif event.on_timeout == "skip":
        logger.warning(f"[skip] {msg}")
    elif event.on_timeout == "retry":
        logger.warning(f"[retry not implemented] {msg}")
        raise PlaybackError(msg)


def _wait_for_window(event: WindowTriggerEvent) -> None:
    """지정 제목을 포함한 창이 나타날 때까지 폴링한다.

    Raises:
        PlaybackError: on_timeout=="error"이고 타임아웃 발생 시.
    """
    deadline_ns = time.perf_counter_ns() + event.timeout_ms * 1_000_000
    interval_s = 0.1

    while time.perf_counter_ns() < deadline_ns:
        if _stop_flag.is_set():
            return
        if find_window(event.window_title_contains) is not None:
            return
        time.sleep(interval_s)

    msg = f"window_trigger timeout waiting for '{event.window_title_contains}'"
    if event.on_timeout == "error":
        raise PlaybackError(msg)
    elif event.on_timeout == "skip":
        logger.warning(f"[skip] {msg}")


# ── 재생 루프 ─────────────────────────────────────────────────────────────────

def _play_loop(
    macro: MacroData,
    speed: float,
    on_event: Callable[[AnyEvent], None] | None,
    on_complete: Callable[[], None] | None,
    on_error: Callable[[Exception], None] | None,
) -> None:
    """실제 재생을 수행하는 스레드 함수.

    core-beliefs.md 원칙 3: 절대 타임스탬프 기준 + 드리프트 보정.

    Args:
        macro: 재생할 MacroData (events 배열만 사용).
        speed: 재생 속도 배율 (0.5~10.0).
        on_event: 각 이벤트 실행 후 호출되는 콜백.
        on_complete: 재생 완료 시 콜백.
        on_error: 오류 발생 시 콜백.
    """
    global _current_event_idx, _total_events
    play_start_ns = time.perf_counter_ns()
    last_event_end_ns = play_start_ns
    state = _PlayState()
    _total_events = len(macro.events)
    _current_event_idx = 0

    for idx, event in enumerate(macro.events):
        _current_event_idx = idx

        # 일시정지 대기
        while _pause_flag.is_set() and not _stop_flag.is_set():
            time.sleep(0.05)

        if _stop_flag.is_set():
            logger.debug("Playback stopped by flag")
            return

        # 목표 실행 시각 계산 (core-beliefs 원칙 3)
        if event.delay_override_ms is not None:
            target_ns = last_event_end_ns + int(event.delay_override_ms * 1_000_000)
        else:
            target_ns = play_start_ns + int(event.timestamp_ns / speed)

        # 대기 (1ms 이상일 때만 sleep — 오버슛 보정은 다음 이벤트가 처리)
        now_ns = time.perf_counter_ns()
        sleep_ns = target_ns - now_ns
        if sleep_ns > 1_000_000:
            time.sleep(sleep_ns / 1_000_000_000)

        try:
            _execute_event(event, macro.settings, state)
        except PlaybackError as e:
            logger.error(f"Playback error: {e}")
            if on_error:
                on_error(e)
            return
        except Exception as e:
            logger.exception(f"Unexpected error during playback: {e}")
            if on_error:
                on_error(e)
            return

        if on_event:
            on_event(event)

        last_event_end_ns = time.perf_counter_ns()

    if not _stop_flag.is_set() and on_complete:
        on_complete()


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────

def play(
    macro: MacroData,
    speed: float = 1.0,
    on_event: Callable[[AnyEvent], None] | None = None,
    on_complete: Callable[[], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
) -> None:
    """MacroData를 별도 스레드에서 재생 시작한다.

    Args:
        macro: 재생할 MacroData. events 배열 사용.
        speed: 재생 속도 배율. 기본 1.0.
        on_event: 각 이벤트 실행 후 UI에 알릴 콜백.
        on_complete: 재생 완료 시 UI에 알릴 콜백.
        on_error: 오류 발생 시 UI에 알릴 콜백.
    """
    global _playback_thread

    _stop_flag.clear()
    _pause_flag.clear()

    _playback_thread = threading.Thread(
        target=_play_loop,
        args=(macro, speed, on_event, on_complete, on_error),
        daemon=True,
        name="PlaybackThread",
    )
    _playback_thread.start()


def stop() -> None:
    """재생을 중단한다. 현재 이벤트 완료 후 루프를 종료한다."""
    _stop_flag.set()
    _pause_flag.clear()
    if _playback_thread is not None:
        _playback_thread.join(timeout=3.0)


def pause() -> None:
    """재생을 일시정지한다."""
    _pause_flag.set()


def resume() -> None:
    """일시정지된 재생을 재개한다."""
    _pause_flag.clear()


def is_playing() -> bool:
    """현재 재생 중인지 여부를 반환한다."""
    return _playback_thread is not None and _playback_thread.is_alive()


def get_progress() -> float:
    """현재 재생 진행률 (0.0~1.0)을 반환한다."""
    if _total_events == 0:
        return 0.0
    return _current_event_idx / _total_events
