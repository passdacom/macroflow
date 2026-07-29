"""Live Windows RegisterHotKey collision/rollback probe.

Skipped on non-Windows hosts; GitHub's Windows source-test job executes it.
"""

from __future__ import annotations

import sys

import pytest

from macroflow.hotkey_config import DEFAULT_HOTKEY_CONFIG
from macroflow.win32.hotkeys import (
    MOD_NOREPEAT,
    NativeHotkeySet,
    User32HotkeyBackend,
    native_hotkeys,
)

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="requires Windows user32")


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
            "runtime.record_or_capture": "F16",
            "runtime.play_or_color_capture": "F17",
            "runtime.pause_or_resume": "F18",
            "recording.quick_text": "F19",
        }
    )
    candidate = old_config.with_bindings(
        {"runtime.record_or_capture": "F24"}
    )
    old_bindings = native_hotkeys(old_config)
    try:
        initialized = registrar.replace(old_bindings)
        if not initialized.success:
            pytest.skip("F16-F19 were unavailable on this Windows runner")

        result = registrar.replace(native_hotkeys(candidate))

        assert not result.success
        assert result.failed_action_id == "runtime.record_or_capture"
        assert result.failed_key == "F24"
        assert result.rollback_succeeded
        assert registrar.current == old_bindings
    finally:
        registrar.replace(())
        user32.UnregisterHotKey(0, reserved_id)
