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
    MouseWheelEvent,
    TextInputEvent,
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
    send_mouse_wheel,
    send_paste,
    set_clipboard_text,
)

logger = logging.getLogger(__name__)


class PlaybackError(Exception):
    """재생 중 복구 불가 오류."""


@dataclasses.dataclass(frozen=True)
class PlaybackSession:
    """Opaque ownership handle for one player worker."""

    _token: object = dataclasses.field(default_factory=object, repr=False)


class _PlaybackClock:
    """일시중지 시간을 제외한 재생 active-time 시계와 interruptible wait."""

    def __init__(self) -> None:
        self._condition = threading.Condition()
        self._paused = False
        self._pause_started_ns: int | None = None
        self._total_paused_ns = 0

    def reset(self) -> None:
        with self._condition:
            self._paused = False
            self._pause_started_ns = None
            self._total_paused_ns = 0
            self._condition.notify_all()

    def pause(self) -> bool:
        with self._condition:
            if self._paused:
                return False
            self._paused = True
            self._pause_started_ns = time.perf_counter_ns()
            self._condition.notify_all()
            return True

    def resume(self) -> bool:
        with self._condition:
            if not self._paused or self._pause_started_ns is None:
                return False
            self._total_paused_ns += time.perf_counter_ns() - self._pause_started_ns
            self._pause_started_ns = None
            self._paused = False
            self._condition.notify_all()
            return True

    def is_paused(self) -> bool:
        with self._condition:
            return self._paused

    def _active_now_locked(self, wall_now_ns: int) -> int:
        current_pause_ns = 0
        if self._paused and self._pause_started_ns is not None:
            current_pause_ns = wall_now_ns - self._pause_started_ns
        return wall_now_ns - self._total_paused_ns - current_pause_ns

    def active_now_ns(self) -> int:
        with self._condition:
            return self._active_now_locked(time.perf_counter_ns())

    def wait_until_resumed(self) -> bool:
        """resume까지 기다린다. stop이면 False를 반환한다."""
        with self._condition:
            while self._paused and not _stop_flag.is_set():
                self._condition.wait()
            return not _stop_flag.is_set()

    def wait_until(self, active_deadline_ns: int) -> bool:
        """active-time deadline까지 기다린다. stop이면 False를 반환한다."""
        with self._condition:
            while not _stop_flag.is_set():
                if self._paused:
                    self._condition.wait()
                    continue
                remaining_ns = active_deadline_ns - self._active_now_locked(
                    time.perf_counter_ns()
                )
                if remaining_ns <= 0:
                    return True
                self._condition.wait(timeout=remaining_ns / 1_000_000_000)
            return False

    def wait_for(self, active_seconds: float) -> bool:
        """지정 active 시간만큼 기다린다. stop이면 False를 반환한다."""
        deadline_ns = self.active_now_ns() + max(0, int(active_seconds * 1_000_000_000))
        return self.wait_until(deadline_ns)

    def notify_stop(self) -> None:
        with self._condition:
            self._condition.notify_all()


# ── 재생 상태 추적 ────────────────────────────────────────────────────────────

@dataclasses.dataclass
class _PlayState:
    """재생 중 클릭/드래그 판별에 사용하는 상태."""

    pending_down: MouseButtonEvent | None = None
    pending_down_real_x: int = 0
    pending_down_real_y: int = 0
    has_moves_since_down: bool = False
    # 색 체크 불일치로 down을 스킵한 경우, 대응하는 up도 스킵하기 위한 버튼명
    color_check_skip_button: str | None = None
    speed: float = 1.0
    pressed_keys: set[int] = dataclasses.field(default_factory=set)
    pressed_mouse: dict[str, tuple[int, int]] = dataclasses.field(default_factory=dict)


# ── 모듈 레벨 상태 ────────────────────────────────────────────────────────────
_playback_thread: threading.Thread | None = None
_playback_session: PlaybackSession | None = None
_playback_lifecycle_lock = threading.RLock()
_playback_stop_in_progress = False
_stop_flag: threading.Event = threading.Event()
_playback_clock = _PlaybackClock()
_input_state_lock = threading.RLock()
_active_play_state: _PlayState | None = None
_pause_pending = False
_current_event_idx: int = 0
_current_event_position: int = 0
_total_events: int = 0
_COLOR_WAIT_NUDGE_AFTER_NS = 1_000_000_000
_COLOR_WAIT_NUDGE_INTERVAL_NS = 1_000_000_000
_COLOR_WAIT_NUDGE_DISTANCE_PX = 8
_COLOR_WAIT_NUDGE_DWELL_S = 0.05


def _active_now_ns() -> int:
    return _playback_clock.active_now_ns()


def _wait_active(seconds: float) -> bool:
    """active 시간 대기 후 True, stop으로 중단되면 False를 반환한다."""
    return _playback_clock.wait_for(seconds)


def _release_active_inputs() -> None:
    """stop/error/종료 시 열린 SendInput key/button을 정확히 한 번 release한다."""
    state = _active_play_state
    if state is None:
        return
    with _input_state_lock:
        for vk_code in tuple(state.pressed_keys):
            send_key(vk_code, is_down=False)
        state.pressed_keys.clear()
        for button, (x, y) in tuple(state.pressed_mouse.items()):
            send_mouse_button(x, y, button, down=False)
        state.pressed_mouse.clear()
        state.pending_down = None


def _apply_pending_pause_if_safe(state: _PlayState) -> None:
    """열린 입력 gesture가 모두 닫힌 경계에서 pending pause를 활성화한다."""
    global _pause_pending
    with _input_state_lock:
        if _pause_pending and not state.pressed_keys and not state.pressed_mouse:
            _pause_pending = False
            _playback_clock.pause()


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
    if _stop_flag.is_set():
        return
    if isinstance(event, MouseButtonEvent):
        x, y = ratio_to_pixel(event.x_ratio, event.y_ratio)

        if event.type == "mouse_down":
            # 색 체크 활성화된 클릭: 마우스 이동 → hover 대기 → 픽셀 색 비교
            if event.color_check_enabled and event.recorded_color is not None:
                if _stop_flag.is_set():
                    return
                send_mouse_move(x, y)
                if not _wait_active(0.05):  # hover 효과 대기
                    return
                target = _hex_to_rgb(event.recorded_color)

                matched = _wait_for_click_color_check(
                    x,
                    y,
                    target,
                    settings,
                    event.color_check_on_mismatch,
                )
                if not matched:
                    if _stop_flag.is_set():
                        return
                    actual = get_pixel_color(x, y)
                    actual_hex = f"#{actual[0]:02X}{actual[1]:02X}{actual[2]:02X}"
                    if event.color_check_on_mismatch == "stop":
                        # stop 모드: 설정 시간 동안 기다린 후에도 불일치하면 재생 중단
                        raise PlaybackError(
                            f"색 체크 불일치 → 재생 중단 "
                            f"at ({x},{y}) 실제={actual_hex} 기록={event.recorded_color}"
                        )
                    if event.color_check_on_mismatch == "skip":
                        # skip 모드: 설정 시간 동안 기다린 후에도 불일치하면 클릭 스킵
                        state.color_check_skip_button = event.button
                        logger.debug(
                            f"[color_check] skip click at ({x},{y}): "
                            f"actual={actual_hex} target={event.recorded_color}"
                        )
                        return
                    logger.warning(
                        f"[color_check wait] timeout at ({x},{y}), proceeding with click anyway"
                    )
            if _stop_flag.is_set():
                return
            send_mouse_move(x, y)
            if _stop_flag.is_set():
                return
            with _input_state_lock:
                if _playback_clock.is_paused():
                    return
                send_mouse_button(x, y, event.button, down=True)
                state.pressed_mouse[event.button] = (x, y)
                state.pending_down = event
                state.pending_down_real_x = x
                state.pending_down_real_y = y
                state.has_moves_since_down = False

        else:  # mouse_up
            # 색 체크 불일치로 down이 스킵된 경우 up도 스킵
            if state.color_check_skip_button == event.button:
                state.color_check_skip_button = None
                return
            if state.pending_down is not None and not state.has_moves_since_down:
                dist = math.hypot(
                    x - state.pending_down_real_x,
                    y - state.pending_down_real_y,
                )
                elapsed_ms = max(
                    0.0,
                    (event.timestamp_ns - state.pending_down.timestamp_ns) / 1_000_000,
                )
                if (
                    dist >= settings.click_dist_threshold_px
                    or elapsed_ms >= settings.click_time_threshold_ms
                ):
                    # RAW down/up의 기록 거리 또는 기록 시간 초과 → 드래그로 판별
                    if _stop_flag.is_set():
                        return
                    send_mouse_drag(
                        state.pending_down_real_x,
                        state.pending_down_real_y,
                        x, y,
                        event.button,
                    )
                    with _input_state_lock:
                        state.pressed_mouse.pop(event.button, None)
                        state.pending_down = None
                    return

            if _stop_flag.is_set():
                return
            send_mouse_move(x, y)
            if _stop_flag.is_set():
                return
            with _input_state_lock:
                send_mouse_button(x, y, event.button, down=False)
                state.pressed_mouse.pop(event.button, None)
                state.pending_down = None

    elif isinstance(event, MouseMoveEvent):
        x, y = ratio_to_pixel(event.x_ratio, event.y_ratio)
        if _stop_flag.is_set():
            return
        send_mouse_move(x, y)
        state.has_moves_since_down = True

    elif isinstance(event, MouseWheelEvent):
        x, y = ratio_to_pixel(event.x_ratio, event.y_ratio)
        if _stop_flag.is_set():
            return
        send_mouse_wheel(x, y, event.delta, horizontal=(event.axis == "horizontal"))

    elif isinstance(event, KeyEvent):
        if _stop_flag.is_set():
            return
        with _input_state_lock:
            if _playback_clock.is_paused():
                return
            is_down = event.type == "key_down"
            send_key(event.vk_code, is_down=is_down)
            if is_down:
                state.pressed_keys.add(event.vk_code)
            else:
                state.pressed_keys.discard(event.vk_code)

    elif isinstance(event, TextInputEvent):
        if event.text and not _stop_flag.is_set():
            if not set_clipboard_text(event.text) or not send_paste():
                raise PlaybackError("텍스트 입력을 대상 창에 붙여넣지 못했습니다")

    elif isinstance(event, WaitEvent):
        _wait_active(event.duration_ms / state.speed / 1000.0)

    elif isinstance(event, ColorTriggerEvent):
        _wait_for_color(event)

    elif isinstance(event, WindowTriggerEvent):
        _wait_for_window(event)

    elif isinstance(event, ConditionEvent):
        from macroflow.script_engine import execute_condition
        execute_condition(
            event,
            _stop_flag,
            lambda e: _execute_event(e, settings, state),
            lambda events: _execute_event_sequence(events, settings, state),
            wait_fn=_wait_active,
        )

    elif isinstance(event, LoopEvent):
        from macroflow.script_engine import execute_loop
        execute_loop(
            event,
            _stop_flag,
            lambda e: _execute_event(e, settings, state),
            lambda events: _execute_event_sequence(events, settings, state),
        )


def _execute_event_sequence(
    events: list[AnyEvent],
    settings: MacroSettings,
    state: _PlayState,
) -> None:
    """Condition/Loop 내부 이벤트를 top-level과 같은 시간 규칙으로 실행한다."""
    if not events:
        return

    sequence_start_ns = _active_now_ns()
    timeline_shift_ns = 0
    last_event_end_ns = sequence_start_ns
    last_significant_event_end_ns = sequence_start_ns
    base_ts_ns = events[0].timestamp_ns

    for event in events:
        if not _playback_clock.wait_until_resumed():
            return

        recorded_target_ns = (
            sequence_start_ns
            + int((event.timestamp_ns - base_ts_ns) / state.speed)
            + timeline_shift_ns
        )
        if event.delay_override_ms is not None:
            target_ns = last_event_end_ns + int(
                event.delay_override_ms * 1_000_000 / state.speed
            )
            if not isinstance(event, MouseMoveEvent):
                target_ns = max(target_ns, last_significant_event_end_ns)
        else:
            target_ns = recorded_target_ns

        sleep_ns = target_ns - _active_now_ns()
        if sleep_ns > 1_000_000 and not _playback_clock.wait_until(target_ns):
            return

        execute_start_ns = _active_now_ns()
        _execute_event(event, settings, state)
        _apply_pending_pause_if_safe(state)
        if _stop_flag.is_set():
            return

        last_event_end_ns = _active_now_ns()
        if not isinstance(event, MouseMoveEvent):
            last_significant_event_end_ns = last_event_end_ns

        if event.delay_override_ms is not None:
            raw_target_ns = sequence_start_ns + int(
                (event.timestamp_ns - base_ts_ns) / state.speed
            )
            timeline_shift_ns = last_event_end_ns - raw_target_ns
        else:
            timing_compensation_ns = _event_timing_compensation_ns(
                event,
                execute_start_ns,
                last_event_end_ns,
            )
            if timing_compensation_ns > 0:
                sequence_start_ns += timing_compensation_ns


def _color_check_timeout_ms_for_action(
    settings: MacroSettings,
    action: str,
) -> int:
    """클릭 색 체크 mismatch action에 대응하는 timeout(ms)을 반환한다."""
    if action == "wait":
        selected = settings.color_check_click_wait_timeout_ms
    elif action == "stop":
        selected = settings.color_check_click_stop_timeout_ms
    else:
        selected = settings.color_check_click_skip_timeout_ms
    # 모든 action timeout이 기본값으로 그대로인 경우에만 legacy 단일 timeout을 fallback 한다.
    if (
        selected == 10000
        and settings.color_check_click_wait_timeout_ms == 10000
        and settings.color_check_click_skip_timeout_ms == 10000
        and settings.color_check_click_stop_timeout_ms == 10000
        and settings.color_check_click_timeout_ms != 10000
    ):
        return settings.color_check_click_timeout_ms
    return selected


def _event_timing_compensation_ns(
    event: AnyEvent,
    execute_start_ns: int,
    last_event_end_ns: int,
) -> int:
    """이벤트 자체 대기 시간 때문에 이후 timestamp가 따라잡혀 버리지 않도록 보정값을 반환한다."""
    if isinstance(
        event,
        (WaitEvent, ColorTriggerEvent, WindowTriggerEvent, ConditionEvent, LoopEvent),
    ):
        return max(0, last_event_end_ns - execute_start_ns)
    if (
        isinstance(event, MouseButtonEvent)
        and event.type == "mouse_down"
        and event.color_check_enabled
        and event.recorded_color is not None
    ):
        return max(0, last_event_end_ns - execute_start_ns)
    return 0


def _wait_for_color_check(
    x: int, y: int,
    target: tuple[int, int, int],
    settings: MacroSettings,
) -> None:
    """색 체크 wait 모드: 지정 픽셀 색이 일치할 때까지 폴링한다.

    타임아웃 시 경고 로그만 남기고 클릭을 계속 진행한다 (skip과 달리 클릭은 실행).

    Args:
        x: 검사할 픽셀 X 좌표.
        y: 검사할 픽셀 Y 좌표.
        target: 기다릴 목표 RGB 색.
        settings: color_trigger_check_interval_ms, color_trigger_default_timeout_ms 사용.
    """
    deadline_ns = (
        _active_now_ns()
        + settings.color_trigger_default_timeout_ms * 1_000_000
    )
    interval_s = max(1, int(settings.color_trigger_check_interval_ms)) / 1000.0

    while _active_now_ns() < deadline_ns:
        if _stop_flag.is_set():
            return
        actual = get_pixel_color(x, y)
        if _color_matches(actual, target, settings.color_check_click_tolerance):
            return
        if not _wait_active(interval_s):
            return

    logger.warning(
        f"[color_check wait] timeout at ({x},{y}), proceeding with click anyway"
    )


def _wait_for_click_color_check(
    x: int,
    y: int,
    target: tuple[int, int, int],
    settings: MacroSettings,
    action: str = "skip",
) -> bool:
    """클릭 색 체크: action별 설정 시간 동안 목표 색이 나타나는지 폴링한다.

    Returns:
        목표 색이 timeout 전에 감지되면 True, timeout 또는 stop이면 False.
    """
    timeout_ms = max(0, _color_check_timeout_ms_for_action(settings, action))
    start_ns = _active_now_ns()
    deadline_ns = start_ns + timeout_ms * 1_000_000 if timeout_ms > 0 else None
    next_nudge_ns = start_ns + _COLOR_WAIT_NUDGE_AFTER_NS
    interval_s = max(1, settings.color_check_click_interval_ms) / 1000.0

    while True:
        if _stop_flag.is_set():
            return False
        now_ns = _active_now_ns()
        if deadline_ns is not None and now_ns >= deadline_ns:
            return False
        actual = get_pixel_color(x, y)
        checked_ns = _active_now_ns()
        if _stop_flag.is_set():
            return False
        if deadline_ns is not None and checked_ns >= deadline_ns:
            return False
        if _color_matches(actual, target, settings.color_check_click_tolerance):
            return True
        previous_nudge_ns = next_nudge_ns
        next_nudge_ns = _nudge_cursor_if_due(x, y, checked_ns, next_nudge_ns)
        if next_nudge_ns != previous_nudge_ns:
            checked_ns = _active_now_ns()
            if _stop_flag.is_set():
                return False
            if deadline_ns is not None and checked_ns >= deadline_ns:
                return False
        wait_s = interval_s
        if deadline_ns is not None:
            remaining_s = (deadline_ns - checked_ns) / 1_000_000_000
            if remaining_s <= 0:
                return False
            wait_s = min(wait_s, remaining_s)
        if not _wait_active(wait_s):
            return False


def _nudge_cursor_if_due(x: int, y: int, now_ns: int, next_nudge_ns: int) -> int:
    """색 대기 중 hover 영역 밖으로 잠시 이동 후 원위치한다."""
    if now_ns < next_nudge_ns:
        return next_nudge_ns
    adjacent_x = (
        x - _COLOR_WAIT_NUDGE_DISTANCE_PX
        if x >= _COLOR_WAIT_NUDGE_DISTANCE_PX
        else x + _COLOR_WAIT_NUDGE_DISTANCE_PX
    )
    send_mouse_move(adjacent_x, y)
    _stop_flag.wait(_COLOR_WAIT_NUDGE_DWELL_S)
    send_mouse_move(x, y)
    return now_ns + _COLOR_WAIT_NUDGE_INTERVAL_NS


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

    마우스를 해당 위치로 먼저 이동한다. hover로 색이 변하는 UI 요소
    (버튼 활성화 표시 등)에서도 올바르게 트리거하기 위함.

    Raises:
        PlaybackError: on_timeout=="error"이고 타임아웃 발생 시.
    """
    x, y = ratio_to_pixel(event.x_ratio, event.y_ratio)
    # hover 효과 트리거: 색 체크 전 마우스를 해당 위치로 이동
    send_mouse_move(x, y)
    if not _wait_active(0.05):
        return
    target = _hex_to_rgb(event.target_color)
    start_ns = _active_now_ns()
    deadline_ns = (
        None if event.timeout_ms <= 0
        else start_ns + event.timeout_ms * 1_000_000
    )
    next_nudge_ns = start_ns + _COLOR_WAIT_NUDGE_AFTER_NS
    interval_s = max(1, int(event.check_interval_ms)) / 1000.0

    while True:
        if _stop_flag.is_set():
            return
        now_ns = _active_now_ns()
        if deadline_ns is not None and now_ns >= deadline_ns:
            break
        actual = get_pixel_color(x, y)
        checked_ns = _active_now_ns()
        if _stop_flag.is_set():
            return
        if deadline_ns is not None and checked_ns >= deadline_ns:
            break
        if _color_matches(actual, target, event.tolerance):
            return
        previous_nudge_ns = next_nudge_ns
        next_nudge_ns = _nudge_cursor_if_due(x, y, checked_ns, next_nudge_ns)
        if next_nudge_ns != previous_nudge_ns:
            checked_ns = _active_now_ns()
            if _stop_flag.is_set():
                return
            if deadline_ns is not None and checked_ns >= deadline_ns:
                break
        wait_s = interval_s
        if deadline_ns is not None:
            remaining_s = (deadline_ns - checked_ns) / 1_000_000_000
            if remaining_s <= 0:
                break
            wait_s = min(wait_s, remaining_s)
        if not _wait_active(wait_s):
            return

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
    deadline_ns = _active_now_ns() + event.timeout_ms * 1_000_000
    interval_s = 0.1

    while _active_now_ns() < deadline_ns:
        if _stop_flag.is_set():
            return
        if find_window(event.window_title_contains) is not None:
            return
        if not _wait_active(interval_s):
            return

    msg = f"window_trigger timeout waiting for '{event.window_title_contains}'"
    if event.on_timeout == "error":
        raise PlaybackError(msg)
    elif event.on_timeout == "skip":
        logger.warning(f"[skip] {msg}")


# ── 재생 루프 ─────────────────────────────────────────────────────────────────

def _play_loop(
    macro: MacroData,
    speed: float,
    on_event: Callable[[int, AnyEvent], None] | None,
    on_complete: Callable[[], None] | None,
    on_error: Callable[[Exception], None] | None,
    event_range: tuple[int, int] | None,
    on_event_start: Callable[[int, AnyEvent], None] | None = None,
    start_pause_requested: Callable[[], bool] | None = None,
) -> None:
    """실제 재생을 수행하는 스레드 함수.

    core-beliefs.md 원칙 3: 절대 타임스탬프 기준 + 드리프트 보정.

    Args:
        macro: 재생할 MacroData (events 배열만 사용).
        speed: 재생 속도 배율 (0.5~10.0).
        on_event: 각 이벤트 실행 완료 후 호출되는 콜백 (idx, event).
        on_complete: 재생 완료 시 콜백.
        on_error: 오류 발생 시 콜백.
        event_range: (start_idx, end_idx) 구간 재생. None이면 전체 재생.
            end_idx는 exclusive (Python slice 규칙).
        on_event_start: 각 이벤트 실행 직전에 호출되는 콜백 (idx, event).
    """
    global _current_event_idx, _current_event_position, _total_events, _active_play_state
    state = _PlayState(speed=speed)
    _active_play_state = state
    if start_pause_requested is not None and start_pause_requested():
        _playback_clock.pause()
    play_start_ns = _active_now_ns()
    timeline_shift_ns = 0
    last_event_end_ns = play_start_ns
    # 음수 딜레이 플로어: 마우스 이동을 제외한 마지막 이벤트 종료 시각.
    # 음수 delay_override_ms 로 target_ns 가 이 시각보다 앞서면 이 시각으로 클램프한다.
    last_significant_event_end_ns = play_start_ns

    # 구간 재생 범위 결정
    all_events = macro.events
    start = 0
    end = len(all_events)
    if event_range is not None:
        start = max(0, event_range[0])
        end = min(len(all_events), event_range[1])
    events_to_play = list(enumerate(all_events))[start:end]

    _total_events = len(events_to_play)
    _current_event_idx = start
    _current_event_position = 0

    # 구간 재생 시 첫 이벤트의 타임스탬프를 기준점으로 (즉시 시작)
    base_ts_ns = events_to_play[0][1].timestamp_ns if events_to_play else 0

    for play_idx, (orig_idx, event) in enumerate(events_to_play):
        _current_event_idx = orig_idx

        # 일시중지 시간은 active clock에서 제외되므로 resume 뒤 catch-up하지 않는다.
        if not _playback_clock.wait_until_resumed():
            logger.debug("Playback stopped by flag")
            return

        # 목표 실행 시각 계산. override 뒤에는 이후 녹화 간격이 유지되도록
        # 전체 녹화 timeline을 실제 실행 시점에 맞춰 이동한다.
        recorded_target_ns = (
            play_start_ns
            + int((event.timestamp_ns - base_ts_ns) / speed)
            + timeline_shift_ns
        )
        if event.delay_override_ms is not None:
            target_ns = last_event_end_ns + int(
                event.delay_override_ms * 1_000_000 / speed
            )
            # 음수 딜레이 플로어: 마우스 이동이 아닌 이벤트는 직전 유의미한 이벤트
            # 종료 시각보다 앞서 실행될 수 없다 (이벤트 순서 역전 방지).
            if not isinstance(event, MouseMoveEvent):
                target_ns = max(target_ns, last_significant_event_end_ns)
        else:
            target_ns = recorded_target_ns

        # 대기 (1ms 이상일 때만 sleep — 오버슛 보정은 다음 이벤트가 처리)
        now_ns = _active_now_ns()
        sleep_ns = target_ns - now_ns
        if sleep_ns > 1_000_000:
            if not _playback_clock.wait_until(target_ns):
                return

        # UI에는 이벤트 완료가 아니라 실제 실행 시작 시점을 알린다. 색 체크·대기처럼
        # 한 이벤트가 오래 막히거나 오류로 중단되어도 현재 행이 정확히 남아야 한다.
        try:
            if on_event_start:
                on_event_start(orig_idx, event)
        except Exception as e:
            logger.exception(f"Playback start callback error: {e}")
            _release_active_inputs()
            if on_error:
                on_error(e)
            return
        if _stop_flag.is_set():
            return

        execute_start_ns = _active_now_ns()
        try:
            _execute_event(event, macro.settings, state)
        except PlaybackError as e:
            logger.error(f"Playback error: {e}")
            _release_active_inputs()
            if on_error:
                on_error(e)
            return
        except Exception as e:
            logger.exception(f"Unexpected error during playback: {e}")
            _release_active_inputs()
            if on_error:
                on_error(e)
            return

        _apply_pending_pause_if_safe(state)
        if _stop_flag.is_set():
            return

        _current_event_position = play_idx + 1
        if on_event:
            try:
                on_event(orig_idx, event)
            except Exception as e:
                logger.exception(f"Playback completion callback error: {e}")
                _release_active_inputs()
                if on_error:
                    on_error(e)
                return

        last_event_end_ns = _active_now_ns()

        # 마우스 이동이 아닌 이벤트만 유의미한 이벤트 종료 시각 갱신
        if not isinstance(event, MouseMoveEvent):
            last_significant_event_end_ns = last_event_end_ns

        if event.delay_override_ms is not None:
            # override는 이 이벤트의 실행 전 대기만 바꾼다. 이후 이벤트는
            # 이 이벤트 뒤에서 원래 녹화 간격을 유지하도록 timeline을 이동한다.
            raw_target_ns = play_start_ns + int(
                (event.timestamp_ns - base_ts_ns) / speed
            )
            timeline_shift_ns = last_event_end_ns - raw_target_ns
        else:
            # ── 이벤트 자체 대기 타이머 보정 ─────────────────────────────────
            # 색·창 트리거뿐 아니라 클릭 내부 색 체크도 실제 로딩/대기 시간만큼
            # 오래 걸릴 수 있다. 보정하지 않으면 이후 이벤트가 몰려 실행된다.
            timing_compensation_ns = _event_timing_compensation_ns(
                event,
                execute_start_ns,
                last_event_end_ns,
            )
            if timing_compensation_ns > 0:
                play_start_ns += timing_compensation_ns
                logger.debug(
                    f"Event timer compensated: +{timing_compensation_ns / 1_000_000:.1f}ms"
                )

    if not _stop_flag.is_set():
        _release_active_inputs()
        if on_complete:
            on_complete()


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────

def play(
    macro: MacroData,
    speed: float = 1.0,
    on_event: Callable[[int, AnyEvent], None] | None = None,
    on_complete: Callable[[], None] | None = None,
    on_error: Callable[[Exception], None] | None = None,
    event_range: tuple[int, int] | None = None,
    on_event_start: Callable[[int, AnyEvent], None] | None = None,
    start_pause_requested: Callable[[], bool] | None = None,
) -> PlaybackSession:
    """Start MacroData playback and return an ownership handle for this worker."""
    global _playback_thread, _playback_session, _pause_pending
    with _playback_lifecycle_lock:
        if _playback_stop_in_progress:
            raise PlaybackError("이전 재생 중지 정리가 진행 중입니다.")
        previous_thread = _playback_thread
        if previous_thread is not None and previous_thread.is_alive():
            if previous_thread is not threading.current_thread():
                previous_thread.join(timeout=0.1)
            if previous_thread.is_alive():
                raise PlaybackError("이미 재생 중입니다")

        _stop_flag.clear()
        _playback_clock.reset()
        with _input_state_lock:
            _pause_pending = False

        session = PlaybackSession()
        worker = threading.Thread(
            target=_play_loop,
            args=(
                macro,
                speed,
                on_event,
                on_complete,
                on_error,
                event_range,
                on_event_start,
                start_pause_requested,
            ),
            daemon=True,
            name="PlaybackThread",
        )
        _playback_thread = worker
        _playback_session = session
        try:
            worker.start()
        except Exception:
            _playback_thread = None
            _playback_session = None
            raise
        return session


def stop(session: PlaybackSession | None = None) -> bool:
    """Stop the current worker, optionally only when the caller owns its session."""
    global _playback_session, _pause_pending, _playback_stop_in_progress
    with _playback_lifecycle_lock:
        if _playback_stop_in_progress:
            return False
        if session is not None and session != _playback_session:
            return False
        worker = _playback_thread
        if session is not None and (worker is None or not worker.is_alive()):
            return False
        _playback_stop_in_progress = True
        _stop_flag.set()
    try:
        _playback_clock.notify_stop()
        with _input_state_lock:
            _pause_pending = False
        _release_active_inputs()
        if worker is not None and worker is not threading.current_thread():
            worker.join(timeout=3.0)
    finally:
        # 종료되지 않은 worker의 stop 신호는 유지한다. 다음 play()가 살아 있는
        # worker를 거부하므로 old worker가 stop clear 후 재개되는 race를 막는다.
        with _playback_lifecycle_lock:
            if worker is None or not worker.is_alive():
                if session is None or session == _playback_session:
                    _playback_session = None
                _stop_flag.clear()
                _playback_clock.reset()
            _playback_stop_in_progress = False
    return True


def pause() -> bool:
    """안전한 입력 경계에서 재생을 일시정지하도록 요청한다."""
    global _pause_pending
    if not is_playing():
        return False
    with _input_state_lock:
        if _pause_pending or _playback_clock.is_paused():
            return False
        state = _active_play_state
        if state is not None and (state.pressed_keys or state.pressed_mouse):
            _pause_pending = True
            return True
        return _playback_clock.pause()


def resume() -> bool:
    """일시정지된 재생을 재개한다. 상태가 바뀌면 True를 반환한다."""
    global _pause_pending
    if not is_playing():
        return False
    with _input_state_lock:
        if _pause_pending:
            _pause_pending = False
            return True
        return _playback_clock.resume()


def is_playing() -> bool:
    """현재 재생 중인지 여부를 반환한다."""
    return _playback_thread is not None and _playback_thread.is_alive()


def is_paused() -> bool:
    """재생 worker가 살아 있고 pause 요청 또는 실제 pause 상태인지 반환한다."""
    with _input_state_lock:
        paused = _pause_pending or _playback_clock.is_paused()
    return is_playing() and paused


def get_progress() -> float:
    """선택된 재생 구간에서 실행 완료된 이벤트 비율을 반환한다 (0.0~1.0)."""
    if _total_events == 0:
        return 0.0
    return min(1.0, _current_event_position / _total_events)


def get_current_event_idx() -> int:
    """현재 재생 중인 이벤트의 원본 인덱스를 반환한다."""
    return _current_event_idx
