"""Runtime validation covers constructed data, not only JSON loader output."""

from __future__ import annotations

import copy
from dataclasses import replace

import pytest

from macroflow.playback_validation import validate_playback
from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    ConditionEvent,
    KeyEvent,
    LoopEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    TextInputEvent,
    WaitEvent,
    WindowTriggerEvent,
)


def _macro(*events: AnyEvent) -> MacroData:
    return MacroData(
        meta=MacroMeta(version="1.0", app_version="1.0", created_at="",
                       screen_width=1920, screen_height=1080, dpi_scale=1.0),
        settings=MacroSettings(), raw_events=[], events=list(events),
    )


def _wait(**changes: object) -> WaitEvent:
    return replace(WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=10), **changes)


def _color(**changes: object) -> ColorTriggerEvent:
    return replace(ColorTriggerEvent(id="color", type="color_trigger", timestamp_ns=0,
                                    x_ratio=0.2, y_ratio=0.3, target_color="#aAbBcC"), **changes)


@pytest.mark.parametrize("speed", [0, -1, float("inf"), -float("inf"), float("nan"), True, "1", 10**1000])
def test_rejects_invalid_speed(speed: float) -> None:
    with pytest.raises(ValueError, match="speed"):
        validate_playback(_macro(_wait()), speed)


@pytest.mark.parametrize("changes", [
    {"timestamp_ns": -1}, {"timestamp_ns": float("nan")},
    {"timestamp_ns": 0.5}, {"timestamp_ns": True}, {"timestamp_ns": 10**100},
    {"duration_ms": -1}, {"duration_ms": float("inf")}, {"duration_ms": "10"},
    {"delay_override_ms": float("nan")}, {"delay_override_ms": -(10**100)},
    {"type": "key_down"},
])
def test_rejects_invalid_time_and_discriminants(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="events\\[0\\]"):
        validate_playback(_macro(_wait(**changes)))


@pytest.mark.parametrize("event", [
    _wait(duration_ms=1), _wait(duration_ms=0, delay_override_ms=-1),
])
def test_rejects_scaled_wait_overflow(event: AnyEvent) -> None:
    with pytest.raises(ValueError, match="safe playback wait limit"):
        validate_playback(_macro(event), 5e-324)


def test_rejects_scaled_timestamp_overflow() -> None:
    with pytest.raises(ValueError, match="timestamp_ns.*safe playback wait limit"):
        validate_playback(_macro(_wait(duration_ms=0), _wait(duration_ms=0, timestamp_ns=1)), 5e-324)


@pytest.mark.parametrize("vk", [-1, 0, 255, 65537, True, 65.5, float("nan")])
def test_rejects_key_codes_that_would_wrap_or_are_not_virtual_keys(vk: int) -> None:
    key = KeyEvent(id="key", type="key_down", timestamp_ns=0, key="a", vk_code=vk)
    with pytest.raises(ValueError, match="vk_code"):
        validate_playback(_macro(key))


@pytest.mark.parametrize("changes", [
    {"x_ratio": float("nan")}, {"y_ratio": float("inf")}, {"x_ratio": 1e20},
    {"target_color": "#12345z"}, {"target_color": None}, {"tolerance": -1},
    {"tolerance": 256}, {"check_interval_ms": 0}, {"check_interval_ms": -1},
    {"timeout_ms": float("inf")}, {"on_timeout": "anything"},
])
def test_rejects_unsafe_color_trigger(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="events\\[0\\]"):
        validate_playback(_macro(_color(**changes)))


@pytest.mark.parametrize("name,value", [
    ("default_playback_speed", 0), ("default_playback_speed", float("nan")),
    ("click_dist_threshold_px", -1), ("click_time_threshold_ms", float("inf")),
    ("color_check_click_tolerance", 256), ("color_trigger_check_interval_ms", 0),
    ("color_check_click_interval_ms", -1), ("color_check_click_timeout_ms", "10"),
    ("color_check_click_wait_timeout_ms", float("nan")),
    ("color_check_click_skip_timeout_ms", 10**100),
    ("color_check_click_stop_timeout_ms", True),
    ("color_trigger_default_timeout_ms", float("inf")),
])
def test_validates_all_runtime_settings(name: str, value: object) -> None:
    macro = _macro(_wait())
    setattr(macro.settings, name, value)
    with pytest.raises(ValueError, match=f"settings.{name}"):
        validate_playback(macro)


def test_preserves_supported_sentinels_coordinates_and_all_event_types() -> None:
    events = [
        MouseButtonEvent(id="down", type="mouse_down", timestamp_ns=0,
                         x_ratio=-1.5, y_ratio=2.5, delay_override_ms=-100,
                         recorded_color="ff00AA"),
        MouseMoveEvent(id="move", type="mouse_move", timestamp_ns=1, x_ratio=-2, y_ratio=3),
        MouseWheelEvent(id="wheel", type="mouse_wheel", timestamp_ns=2,
                        x_ratio=0, y_ratio=1, delta=-120, axis="horizontal"),
        KeyEvent(id="key", type="key_up", timestamp_ns=3, key="a", vk_code=65),
        _wait(), _color(timeout_ms=0), _color(timeout_ms=-10),
        WindowTriggerEvent(id="window", type="window_trigger", timestamp_ns=0,
                           window_title_contains="", timeout_ms=-10),
        TextInputEvent(id="text", type="text_input", timestamp_ns=0, text="한글"),
        ConditionEvent(id="condition", type="condition", timestamp_ns=0,
                       expression="True", if_true=[_wait()], if_false=[_wait()]),
        LoopEvent(id="loop", type="loop", timestamp_ns=0, count=-1, events=[_wait()]),
        LoopEvent(id="zero", type="loop", timestamp_ns=0, count=0),
    ]
    macro = _macro(*events)
    macro.settings.color_check_click_wait_timeout_ms = -1
    original = copy.deepcopy(macro)
    validate_playback(macro, 2)
    assert macro == original


@pytest.mark.parametrize("branch", ["if_true", "if_false"])
def test_checks_both_condition_branches_and_zero_count_loop_children(branch: str) -> None:
    event = ConditionEvent(id="condition", type="condition", timestamp_ns=0, expression="True")
    loop = LoopEvent(id="loop", type="loop", timestamp_ns=0, count=0,
                     events=[_wait(duration_ms=-1)])
    setattr(event, branch, [loop])
    with pytest.raises(ValueError, match=rf"{branch}.*duration_ms"):
        validate_playback(_macro(event))


def test_rejects_cycles_but_allows_shared_subtrees() -> None:
    loop = LoopEvent(id="loop", type="loop", timestamp_ns=0, count=2, events=[_wait()])
    validate_playback(_macro(loop, loop))
    loop.events.append(loop)
    with pytest.raises(ValueError, match="cyclic"):
        validate_playback(_macro(loop))


def test_rejects_excessive_depth_without_recursion_error() -> None:
    event: AnyEvent = _wait()
    for _ in range(70):
        event = LoopEvent(id="loop", type="loop", timestamp_ns=0, count=1, events=[event])
    with pytest.raises(ValueError, match="nesting depth"):
        validate_playback(_macro(event))


@pytest.mark.parametrize("count", [-2, True, 1.5, float("inf"), 10**100])
def test_rejects_invalid_loop_counts(count: int) -> None:
    loop = LoopEvent(id="loop", type="loop", timestamp_ns=0, count=count, events=[_wait()])
    with pytest.raises(ValueError, match="count"):
        validate_playback(_macro(loop))


def test_rejects_empty_infinite_loop() -> None:
    loop = LoopEvent(id="loop", type="loop", timestamp_ns=0, count=-1)
    with pytest.raises(ValueError, match="empty.*infinite loop"):
        validate_playback(_macro(loop))


@pytest.mark.parametrize("event", [
    MouseButtonEvent(id="mouse", type="mouse_down", timestamp_ns=0,
                     x_ratio=0, y_ratio=0, button="unknown"),
    MouseButtonEvent(id="mouse", type="mouse_down", timestamp_ns=0,
                     x_ratio=0, y_ratio=0, color_check_on_mismatch="unknown"),
    MouseWheelEvent(id="wheel", type="mouse_wheel", timestamp_ns=0,
                    x_ratio=0, y_ratio=0, delta=2**32 + 120, axis="vertical"),
    MouseWheelEvent(id="wheel", type="mouse_wheel", timestamp_ns=0,
                    x_ratio=0, y_ratio=0, delta=120, axis="unknown"),
    TextInputEvent(id="text", type="text_input", timestamp_ns=0, text=None),
])
def test_rejects_native_input_enum_and_payload_errors(event: AnyEvent) -> None:
    with pytest.raises(ValueError):
        validate_playback(_macro(event))


def test_rejects_invalid_tree_shape() -> None:
    loop = LoopEvent(id="loop", type="loop", timestamp_ns=0, count=1)
    loop.events = None  # type: ignore[assignment]
    with pytest.raises(ValueError, match="event list"):
        validate_playback(_macro(loop))


def test_does_not_validate_unexecuted_recording_source() -> None:
    macro = _macro(_wait())
    macro.raw_events = [_wait(duration_ms=-1)]
    validate_playback(macro)
