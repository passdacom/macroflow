"""Live Windows RegisterHotKey collision/rollback probe.

Skipped on non-Windows hosts; GitHub's Windows source-test job executes it.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Mapping

import pytest

from macroflow.hotkey_config import DEFAULT_HOTKEY_CONFIG
from macroflow.ui.hotkey_runtime import HotkeyRuntime
from macroflow.win32.hotkeys import (
    MOD_ALT,
    MOD_CONTROL,
    MOD_NOREPEAT,
    NativeHotkeySet,
    User32HotkeyBackend,
    native_hotkeys,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="requires Windows user32")


class _FocusedFallbacks:
    def __init__(self) -> None:
        self.bindings: dict[str, str] = {}

    def replace(
        self,
        bindings: Mapping[str, str],
        callback: Callable[[str], None],
    ) -> None:
        del callback
        self.bindings = dict(bindings)

    def clear(self) -> None:
        self.bindings.clear()


def test_real_quick_run_collision_preserves_runtime_global_hotkeys() -> None:
    import ctypes

    user32 = ctypes.windll.user32
    reserved_id = 0x7001
    ctrl_alt = MOD_CONTROL | MOD_ALT | MOD_NOREPEAT
    if not user32.RegisterHotKey(0, reserved_id, ctrl_alt, 0x31):
        pytest.skip("Ctrl+Alt+1 was already unavailable on this Windows runner")

    registrar = NativeHotkeySet(User32HotkeyBackend(hwnd=0, user32=user32))
    fallbacks = _FocusedFallbacks()
    runtime = HotkeyRuntime(registrar, fallbacks, lambda _action: None)
    try:
        result = runtime.initialize(DEFAULT_HOTKEY_CONFIG)

        assert result.success
        assert result.failed_action_id == "quick_run.slot_1"
        assert runtime.globally_registered
        assert not runtime.quick_run_globally_registered
        assert [item.action_id for item in registrar.current] == [
            "runtime.record_or_capture",
            "runtime.play_or_color_capture",
            "runtime.pause_or_resume",
            "recording.quick_text",
        ]
        assert "quick_run.slot_1" in fallbacks.bindings
    finally:
        runtime.shutdown()
        user32.UnregisterHotKey(0, reserved_id)


def test_real_registerhotkey_collision_restores_previous_complete_set() -> None:
    import ctypes

    user32 = ctypes.windll.user32
    reserved_id = 0x7000
    vk_f24 = 0x87
    if not user32.RegisterHotKey(0, reserved_id, MOD_NOREPEAT, vk_f24):
        pytest.skip("F24 was already unavailable on this Windows runner")

    registrar = NativeHotkeySet(User32HotkeyBackend(hwnd=0, user32=user32))
    old_config = DEFAULT_HOTKEY_CONFIG.with_bindings(
        {
            "runtime.record_or_capture": "F13",
            "runtime.play_or_color_capture": "F14",
            "runtime.pause_or_resume": "F15",
            "recording.quick_text": "F16",
            "quick_run.slot_1": "Ctrl+Alt+F17",
            "quick_run.slot_2": "Ctrl+Alt+F18",
            "quick_run.slot_3": "Ctrl+Alt+F19",
            "quick_run.slot_4": "Ctrl+Alt+F20",
            "quick_run.slot_5": "Ctrl+Alt+F21",
        }
    )
    candidate = old_config.with_bindings(
        {"runtime.record_or_capture": "F24"}
    )
    old_bindings = native_hotkeys(old_config)
    try:
        initialized = registrar.replace(old_bindings)
        if not initialized.success:
            pytest.skip("F13-F21 test chords were unavailable on this Windows runner")

        result = registrar.replace(native_hotkeys(candidate))

        assert not result.success
        assert result.failed_action_id == "runtime.record_or_capture"
        assert result.failed_key == "F24"
        assert result.rollback_succeeded
        assert registrar.current == old_bindings
    finally:
        registrar.replace(())
        user32.UnregisterHotKey(0, reserved_id)
