"""Recorder quick-text capture contracts."""

from __future__ import annotations

import time

import pytest

import macroflow.recorder as recorder
from macroflow.types import MouseMoveEvent, TextInputEvent


def _mock_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(recorder, "start_hook", lambda _queue: None)
    monkeypatch.setattr(recorder, "stop_hook", lambda: None)
    monkeypatch.setattr(recorder, "get_logical_screen_size", lambda: (1920, 1080))
    monkeypatch.setattr(recorder, "pixel_to_ratio", lambda x, y: (x / 1920, y / 1080))


def test_quick_text_discards_all_pause_activity_and_excludes_pause_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_platform(monkeypatch)
    recorder.start_recording()
    start_ns = recorder._rec_start_ns
    try:
        assert recorder._raw_queue is not None
        recorder._raw_queue.append(
            ("m", start_ns + 49_900_000_000, 0x0200, (400, 300, 0))
        )
        assert recorder.pause_recording(now_ns=start_ns + 50_000_000_000)

        # F9 composer 동안 다른 창 이동·복사·붙여넣기에 해당하는 입력은 모두 폐기된다.
        recorder._raw_queue.append(
            ("m", start_ns + 55_000_000_000, 0x0200, (800, 600, 0))
        )
        recorder._raw_queue.append(
            ("k", start_ns + 60_000_000_000, 0x0100, (0x43, 0, 0))
        )
        assert recorder.inject_text_input(
            "긴 문구를 붙여넣습니다",
            delay_override_ms=100,
        )
        recorder._raw_queue.append(
            ("k", start_ns + 70_000_000_000, 0x0101, (0x43, 0, 0))
        )

        assert recorder.resume_recording(now_ns=start_ns + 80_000_000_000)
        recorder._raw_queue.append(
            ("m", start_ns + 81_000_000_000, 0x0200, (960, 540, 0))
        )
        time.sleep(0.05)
    finally:
        macro = recorder.stop_recording()

    assert [event.type for event in macro.events] == [
        "mouse_move",
        "text_input",
        "mouse_move",
    ]
    assert isinstance(macro.events[0], MouseMoveEvent)
    text = macro.events[1]
    assert isinstance(text, TextInputEvent)
    assert text.text == "긴 문구를 붙여넣습니다"
    assert text.delay_override_ms == 100
    assert text.timestamp_ns == 50_000_000_000
    assert macro.events[2].timestamp_ns == 51_000_000_000
    assert macro.raw_events == macro.events
    assert macro.is_edited is False


def test_quick_text_requires_recording_pause(monkeypatch: pytest.MonkeyPatch) -> None:
    _mock_platform(monkeypatch)
    assert not recorder.inject_text_input("idle")

    recorder.start_recording()
    try:
        assert not recorder.inject_text_input("active")
        assert recorder.pause_recording()
        assert not recorder.inject_text_input("")
        assert recorder.inject_text_input("paused")
    finally:
        macro = recorder.stop_recording()

    assert [event.text for event in macro.events if isinstance(event, TextInputEvent)] == [
        "paused"
    ]


def test_f9_hotkey_is_never_converted_to_raw_key_event() -> None:
    recorder._rec_start_ns = 0
    recorder._pause_intervals = []
    recorder._pause_started_ns = None

    assert recorder._convert_raw(("k", 100, 0x0100, (0x78, 0, 0))) is None
    assert recorder._convert_raw(("k", 200, 0x0101, (0x78, 0, 0))) is None


def test_quick_text_commit_suppresses_late_ctrl_release_only() -> None:
    """Ctrl+Enter 완료 후 pause 밖에서 도착한 Ctrl key-up만 폐기한다."""
    recorder._rec_start_ns = 0
    recorder._pause_intervals = [(100, 200)]
    recorder._pause_started_ns = None
    recorder._recording_pressed_keys.clear()
    recorder._suppressed_pause_keys.clear()

    # Composer 안의 Ctrl-down은 이미 pause suppression 상태로 처리된 경우도 있다.
    assert recorder._process_raw(("k", 150, 0x0100, (0xA2, 0, 0))) is None
    assert 0xA2 in recorder._suppressed_pause_keys

    recorder.suppress_next_key_release({0x11, 0xA2, 0xA3})

    assert recorder._process_raw(("k", 210, 0x0101, (0xA2, 0, 0))) is None
    assert 0xA2 not in recorder._suppressed_pause_keys

    next_down = recorder._process_raw(("k", 300, 0x0100, (0xA2, 0, 0)))
    next_up = recorder._process_raw(("k", 310, 0x0101, (0xA2, 0, 0)))
    assert next_down is not None and next_down.type == "key_down"
    assert next_up is not None and next_up.type == "key_up"


def test_quick_text_release_fence_preserves_ctrl_held_before_pause() -> None:
    """F9 전에 기록된 Ctrl-down은 release fence가 짝 key-up을 삼키면 안 된다."""
    recorder._rec_start_ns = 0
    recorder._pause_intervals = [(100, 200)]
    recorder._pause_started_ns = None
    recorder._recording_pressed_keys.clear()
    recorder._suppressed_pause_keys.clear()

    ctrl_down = recorder._process_raw(("k", 50, 0x0100, (0xA2, 0, 0)))
    assert ctrl_down is not None and ctrl_down.type == "key_down"

    recorder.suppress_next_key_release({0x11, 0xA2, 0xA3})
    ctrl_up = recorder._process_raw(("k", 150, 0x0101, (0xA2, 0, 0)))

    assert ctrl_up is not None and ctrl_up.type == "key_up"
    assert ctrl_up.timestamp_ns == 99
    assert 0xA2 not in recorder._recording_pressed_keys
