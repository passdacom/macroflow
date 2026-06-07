"""Contract tests for the Windows RDP GUI smoke harness."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from macroflow.types import (
    ColorTriggerEvent,
    MouseButtonEvent,
    TextInputEvent,
    WindowTriggerEvent,
)

_SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "rdp_gui_smoke.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location("rdp_gui_smoke", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_smoke_macro_exercises_windows_input_and_color_wait_paths():
    harness = _load_harness()

    macro = harness.build_smoke_macro(
        screen_size=(1800, 1200),
        button_xy=(276, 291),
        entry_xy=(350, 375),
        color_xy=(598, 331),
        drag_xy=(280, 500),
        wheel_xy=(520, 500),
        color_hex="#22AA55",
        text="rdp-ok",
    )

    assert [event.type for event in macro.events] == [
        "window_trigger",
        "mouse_down",
        "mouse_up",
        "wait",
        "mouse_down",
        "mouse_up",
        "text_input",
        "color_trigger",
        "mouse_down",
        "mouse_up",
        "mouse_down",
        "mouse_move",
        "mouse_up",
        "mouse_wheel",
    ]
    assert isinstance(macro.events[0], WindowTriggerEvent)
    assert macro.events[0].window_title_contains == "MacroFlow RDP Smoke Target"

    color_wait_click = macro.events[1]
    assert isinstance(color_wait_click, MouseButtonEvent)
    assert color_wait_click.color_check_enabled is True
    assert color_wait_click.color_check_on_mismatch == "wait"
    assert color_wait_click.recorded_color == "#000000"

    text_input = macro.events[6]
    assert isinstance(text_input, TextInputEvent)
    assert text_input.text == "rdp-ok"

    color_trigger = macro.events[7]
    assert isinstance(color_trigger, ColorTriggerEvent)
    assert color_trigger.target_color == "#22AA55"
    assert color_trigger.timeout_ms == 1000

    assert macro.settings.color_check_click_wait_timeout_ms == 300
    assert macro.settings.color_check_click_tolerance == 0
    assert macro.events[1].x_ratio == 276 / 1800
    assert macro.events[7].y_ratio == 331 / 1200
