"""Pure, fail-fast validation at the playback boundary.

Dataclasses can be constructed or edited without the JSON loader. Validate the
entire executable tree before starting a worker, including unselected branches.
No values are coerced, clamped, or rewritten here. Recorded source events and
metadata are deliberately excluded because playback does not execute them.
"""

from __future__ import annotations

import math
import re
import threading

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

# Millisecond fields cover almost 25 days. Ratios are deliberately not limited
# to [0, 1]: monitors left/above or beyond the primary monitor are supported.
_MAX_TIME_MS = 2**31 - 1
_MAX_TIME_NS = _MAX_TIME_MS * 1_000_000
_MAX_RATIO = 1024
_MAX_DEPTH = 64
_MAX_EVENTS = 1_000_000
# Windows locks have a smaller timeout ceiling than POSIX locks. Leave margin
# for rounding and the active clock's deadline arithmetic on either platform.
_MAX_WAIT_SECONDS = min(threading.TIMEOUT_MAX / 2, _MAX_TIME_MS / 1000)
_COLOR = re.compile(r"#?[0-9a-fA-F]{6}\Z")
_EVENT_TYPES: tuple[tuple[type, tuple[str, ...]], ...] = (
    (MouseButtonEvent, ("mouse_down", "mouse_up")),
    (MouseMoveEvent, ("mouse_move",)),
    (MouseWheelEvent, ("mouse_wheel",)),
    (KeyEvent, ("key_down", "key_up")),
    (WaitEvent, ("wait",)),
    (ColorTriggerEvent, ("color_trigger",)),
    (WindowTriggerEvent, ("window_trigger",)),
    (TextInputEvent, ("text_input",)),
    (ConditionEvent, ("condition",)),
    (LoopEvent, ("loop",)),
)


def _integer(value: object, path: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"{path} must be an integer in [{minimum}, {maximum}]")
    return value


def _number(value: object, path: str) -> float:
    if type(value) not in (int, float):
        raise ValueError(f"{path} must be a finite number")
    try:
        number = float(value)  # type: ignore[arg-type]
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{path} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{path} must be a finite number")
    return number


def _speed(value: object, path: str) -> float:
    number = _number(value, path)
    if number <= 0:
        raise ValueError(f"{path} must be positive")
    return number


def _choice(value: object, path: str, choices: tuple[str, ...]) -> None:
    if not isinstance(value, str) or value not in choices:
        raise ValueError(f"{path} must be one of {', '.join(choices)}")


def _string(value: object, path: str) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{path} must be a string")


def _color(value: object, path: str) -> None:
    if not isinstance(value, str) or _COLOR.fullmatch(value) is None:
        raise ValueError(f"{path} must be a six-digit RGB color (for example #12ABEF)")


def _scaled_wait(seconds: float, speed: float, path: str) -> None:
    scaled = abs(seconds) / speed
    if not math.isfinite(scaled) or scaled > _MAX_WAIT_SECONDS:
        raise ValueError(f"{path} exceeds the safe playback wait limit at this speed")


def _settings(settings: MacroSettings) -> None:
    if not isinstance(settings, MacroSettings):
        raise ValueError("settings must be MacroSettings")
    _speed(settings.default_playback_speed, "settings.default_playback_speed")
    _integer(settings.click_dist_threshold_px, "settings.click_dist_threshold_px", 0, 2**31 - 1)
    _integer(settings.click_time_threshold_ms, "settings.click_time_threshold_ms", 0, _MAX_TIME_MS)
    _integer(settings.color_check_click_tolerance, "settings.color_check_click_tolerance", 0, 255)
    for name in ("color_trigger_check_interval_ms", "color_check_click_interval_ms"):
        _integer(getattr(settings, name), f"settings.{name}", 1, _MAX_TIME_MS)
    for name in (
        "color_trigger_default_timeout_ms",
        "color_check_click_timeout_ms",
        "color_check_click_wait_timeout_ms",
        "color_check_click_skip_timeout_ms",
        "color_check_click_stop_timeout_ms",
    ):
        # Existing color waits treat nonpositive timeouts as unlimited. Do not
        # silently turn these values into a short timeout or reject the sentinel.
        _integer(getattr(settings, name), f"settings.{name}", -_MAX_TIME_MS, _MAX_TIME_MS)


def _event(event: AnyEvent, path: str, speed: float) -> None:
    expected = next((types for cls, types in _EVENT_TYPES if isinstance(event, cls)), None)
    if expected is None:
        raise ValueError(f"{path} is not a supported playback event")
    _choice(event.type, f"{path}.type", expected)
    _integer(event.timestamp_ns, f"{path}.timestamp_ns", 0, _MAX_TIME_NS)
    if event.delay_override_ms is not None:
        delay = _integer(event.delay_override_ms, f"{path}.delay_override_ms", -_MAX_TIME_MS, _MAX_TIME_MS)
        _scaled_wait(delay / 1000, speed, f"{path}.delay_override_ms")
    if isinstance(event, (MouseButtonEvent, MouseMoveEvent, MouseWheelEvent, ColorTriggerEvent)):
        for name in ("x_ratio", "y_ratio"):
            ratio = _number(getattr(event, name), f"{path}.{name}")
            if abs(ratio) > _MAX_RATIO:
                raise ValueError(f"{path}.{name} must be within +/-{_MAX_RATIO} screen widths/heights")
    if isinstance(event, MouseButtonEvent):
        _choice(event.button, f"{path}.button", ("left", "right", "middle"))
        _choice(event.color_check_on_mismatch, f"{path}.color_check_on_mismatch", ("skip", "stop", "wait"))
        if type(event.color_check_enabled) is not bool:
            raise ValueError(f"{path}.color_check_enabled must be a boolean")
        if event.recorded_color is not None:
            _color(event.recorded_color, f"{path}.recorded_color")
    elif isinstance(event, MouseWheelEvent):
        _integer(event.delta, f"{path}.delta", -(2**31), 2**31 - 1)
        _choice(event.axis, f"{path}.axis", ("vertical", "horizontal"))
    elif isinstance(event, KeyEvent):
        _integer(event.vk_code, f"{path}.vk_code", 1, 0xFE)
    elif isinstance(event, WaitEvent):
        duration = _integer(event.duration_ms, f"{path}.duration_ms", 0, _MAX_TIME_MS)
        _scaled_wait(duration / 1000, speed, f"{path}.duration_ms")
    elif isinstance(event, (ColorTriggerEvent, WindowTriggerEvent)):
        _integer(event.timeout_ms, f"{path}.timeout_ms", -_MAX_TIME_MS, _MAX_TIME_MS)
        _choice(event.on_timeout, f"{path}.on_timeout", ("error", "skip", "retry"))
        if isinstance(event, ColorTriggerEvent):
            _color(event.target_color, f"{path}.target_color")
            _integer(event.tolerance, f"{path}.tolerance", 0, 255)
            _integer(event.check_interval_ms, f"{path}.check_interval_ms", 1, _MAX_TIME_MS)
        else:
            _string(event.window_title_contains, f"{path}.window_title_contains")
    elif isinstance(event, TextInputEvent):
        _string(event.text, f"{path}.text")
    elif isinstance(event, ConditionEvent):
        _string(event.expression, f"{path}.expression")
    elif isinstance(event, LoopEvent):
        _integer(event.count, f"{path}.count", -1, 2**31 - 1)
        if event.count == -1 and isinstance(event.events, list) and not event.events:
            raise ValueError(f"{path}.events cannot be empty for an infinite loop")


def validate_playback(macro: MacroData, speed: float = 1.0) -> None:
    """Raise ValueError for unsafe runtime data, without effects or mutation.

    Traverse both condition branches and every loop body, even zero-count loops.
    Ancestor identities detect cycles without rejecting shared acyclic subtrees.
    A depth limit also keeps execution below Python's recursive call-stack limit.
    """
    checked_speed = _speed(speed, "speed")
    if not isinstance(macro, MacroData):
        raise ValueError("macro must be MacroData")
    _settings(macro.settings)
    seen_events = 0

    def visit(events: list[AnyEvent], path: str, ancestors: frozenset[int], depth: int) -> None:
        nonlocal seen_events
        if not isinstance(events, list):
            raise ValueError(f"{path} must be an event list")
        if depth > _MAX_DEPTH:
            raise ValueError(f"{path} exceeds the maximum nesting depth of {_MAX_DEPTH}")
        base_timestamp = 0
        for index, event in enumerate(events):
            event_path = f"{path}[{index}]"
            seen_events += 1
            if seen_events > _MAX_EVENTS:
                raise ValueError(f"{path} exceeds the maximum event count of {_MAX_EVENTS}")
            if id(event) in ancestors:
                raise ValueError(f"{event_path} contains a cyclic event reference")
            _event(event, event_path, checked_speed)
            if index == 0:
                base_timestamp = event.timestamp_ns
            _scaled_wait((event.timestamp_ns - base_timestamp) / 1_000_000_000,
                         checked_speed, f"{event_path}.timestamp_ns")
            if isinstance(event, (ConditionEvent, LoopEvent)):
                child_ancestors = ancestors | {id(event)}
                if isinstance(event, ConditionEvent):
                    visit(event.if_true, f"{event_path}.if_true", child_ancestors, depth + 1)
                    visit(event.if_false, f"{event_path}.if_false", child_ancestors, depth + 1)
                else:
                    visit(event.events, f"{event_path}.events", child_ancestors, depth + 1)

    visit(macro.events, "events", frozenset(), 0)
