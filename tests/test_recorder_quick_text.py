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
        assert recorder.inject_text_input("긴 문구를 붙여넣습니다")
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
