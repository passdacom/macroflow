"""Injected events must retain their position in the recorder's capture stream."""

from __future__ import annotations

import threading
import time
from collections.abc import Iterator
from dataclasses import dataclass

import pytest

import macroflow.recorder as recorder
from macroflow.types import AnyEvent, ColorTriggerEvent, MacroData, TextInputEvent


@dataclass
class DelayedCapture:
    release: threading.Event
    last_raw_processed: threading.Event
    now_ns: int = 1_000

    def raw(self, kind: str, at: int, message: int, data: tuple[int, int, int]) -> None:
        assert recorder._raw_queue is not None
        recorder._raw_queue.append((kind, at, message, data))

    def color(self, at: int, color: str = "#112233") -> None:
        self.now_ns = at
        recorder.inject_color_trigger(
            0.25, 0.5, color, timeout_ms=8000, check_interval_ms=25,
        )

    def finish(self, *, drain: bool = True) -> MacroData:
        if drain:
            # Force all queued items through the shutdown drain, without sleeps.
            recorder._stop_consumer.set()
        self.release.set()
        if not drain:
            assert self.last_raw_processed.wait(timeout=3), "consumer did not process tail"
        return recorder.stop_recording()


@pytest.fixture
def capture(monkeypatch: pytest.MonkeyPatch) -> Iterator[DelayedCapture]:
    """Hold the real consumer until the whole capture sequence is queued."""
    state = DelayedCapture(threading.Event(), threading.Event())
    entered = threading.Event()
    consume = recorder._consumer_loop
    process = recorder._process_raw

    def delayed_consumer() -> None:
        entered.set()
        state.release.wait()
        consume()

    def process_with_tail_signal(raw: recorder._RawEvent) -> AnyEvent | None:
        event = process(raw)
        if raw[1] == 2_000:
            state.last_raw_processed.set()
        return event

    monkeypatch.setattr(recorder, "start_hook", lambda _queue: None)
    monkeypatch.setattr(recorder, "stop_hook", lambda: None)
    monkeypatch.setattr(recorder, "get_logical_screen_size", lambda: (1920, 1080))
    monkeypatch.setattr(recorder, "pixel_to_ratio", lambda x, y: (x / 1920, y / 1080))
    monkeypatch.setattr(recorder, "get_pixel_color", lambda x, y: (255, 255, 255))
    monkeypatch.setattr(time, "perf_counter_ns", lambda: state.now_ns)
    monkeypatch.setattr(recorder, "_consumer_loop", delayed_consumer)
    monkeypatch.setattr(recorder, "_process_raw", process_with_tail_signal)
    recorder.start_recording()
    try:
        assert entered.wait(timeout=3), "consumer did not start"
        yield state
    finally:
        state.release.set()
        if recorder.is_recording():
            recorder.stop_recording()


@pytest.mark.parametrize("drain", [False, True], ids=["running-consumer", "stop-drain"])
def test_color_triggers_follow_pending_raw_events(capture: DelayedCapture, drain: bool) -> None:
    capture.raw("k", 1_100, 0x0100, (0x41, 0, 0))
    capture.color(1_200)
    capture.raw("m", 1_300, 0x0200, (960, 540, 0))
    capture.color(1_400, "#445566")
    capture.raw("k", 2_000, 0x0101, (0x41, 0, 0))

    macro = capture.finish(drain=drain)

    assert [event.type for event in macro.events] == [
        "key_down", "color_trigger", "mouse_move", "color_trigger", "key_up",
    ]
    assert [event.timestamp_ns for event in macro.events] == [100, 200, 300, 400, 1000]
    first, second = macro.events[1], macro.events[3]
    assert isinstance(first, ColorTriggerEvent)
    assert isinstance(second, ColorTriggerEvent)
    assert (first.target_color, second.target_color) == ("#112233", "#445566")
    assert (first.x_ratio, first.y_ratio) == (0.25, 0.5)
    assert (first.timeout_ms, first.check_interval_ms) == (8000, 25)
    assert (first.tolerance, first.on_timeout) == (10, "skip")
    assert first.id != second.id
    assert macro.raw_events == macro.events
    assert macro.raw_events is not macro.events
    assert all(raw is not edited for raw, edited in zip(macro.raw_events, macro.events, strict=True))
    assert not macro.is_edited


def test_color_trigger_is_queued_without_publishing_ahead_of_consumer(
    capture: DelayedCapture,
) -> None:
    capture.raw("k", 1_100, 0x0100, (0x41, 0, 0))
    capture.color(1_200)

    assert recorder.get_event_count() == 0
    assert recorder._raw_queue is not None
    assert len(recorder._raw_queue) == 2
    assert isinstance(recorder._raw_queue[-1], ColorTriggerEvent)


def test_equal_timestamps_retain_capture_order(capture: DelayedCapture) -> None:
    capture.raw("k", 1_100, 0x0100, (0x41, 0, 0))
    capture.color(1_100)
    capture.raw("k", 1_100, 0x0101, (0x41, 0, 0))

    macro = capture.finish()

    assert [event.type for event in macro.events] == ["key_down", "color_trigger", "key_up"]
    assert [event.timestamp_ns for event in macro.events] == [100, 100, 100]


def test_color_text_and_pause_gestures_keep_capture_order(capture: DelayedCapture) -> None:
    capture.raw("k", 1_050, 0x0100, (0x41, 0, 0))
    capture.raw("k", 1_075, 0x0101, (0x41, 0, 0))
    capture.color(1_100)
    assert recorder.pause_recording(now_ns=1_200)
    # UI input started during the pause must not leak after resume.
    capture.raw("k", 1_250, 0x0100, (0xA2, 0, 0))
    capture.raw("m", 1_260, 0x0201, (50, 50, 0))
    capture.color(1_300, "#BADBAD")
    assert recorder.inject_text_input("paused text", delay_override_ms=75)
    assert recorder.resume_recording(now_ns=1_500)
    recorder.suppress_next_key_release({0x11, 0xA2, 0xA3})
    capture.raw("k", 1_510, 0x0101, (0xA2, 0, 0))
    capture.raw("m", 1_520, 0x0202, (50, 50, 0))
    capture.color(1_600, "#445566")
    capture.raw("k", 1_650, 0x0100, (0xA2, 0, 0))
    capture.raw("k", 1_700, 0x0101, (0xA2, 0, 0))

    macro = capture.finish()

    assert [event.type for event in macro.events] == [
        "key_down", "key_up", "color_trigger", "text_input", "color_trigger",
        "key_down", "key_up",
    ]
    assert [event.timestamp_ns for event in macro.events] == [50, 75, 100, 200, 300, 350, 400]
    text = macro.events[3]
    assert isinstance(text, TextInputEvent)
    assert (text.text, text.delay_override_ms) == ("paused text", 75)


def test_trigger_keeps_held_input_release_at_pause_boundary(capture: DelayedCapture) -> None:
    capture.raw("k", 1_050, 0x0100, (0x41, 0, 0))
    capture.raw("m", 1_060, 0x0201, (50, 50, 0))
    capture.color(1_100)
    assert recorder.pause_recording(now_ns=1_200)
    capture.raw("k", 1_300, 0x0101, (0x41, 0, 0))
    capture.raw("m", 1_350, 0x0202, (50, 50, 0))
    assert recorder.resume_recording(now_ns=1_500)
    capture.color(1_600)

    macro = capture.finish()

    assert [event.type for event in macro.events] == [
        "key_down", "mouse_down", "color_trigger", "key_up", "mouse_up", "color_trigger",
    ]
    assert [event.timestamp_ns for event in macro.events] == [50, 60, 100, 199, 199, 300]


@pytest.mark.parametrize("recording", [False, True], ids=["idle", "missing-queue"])
def test_color_trigger_requires_active_capture_queue(
    monkeypatch: pytest.MonkeyPatch, recording: bool,
) -> None:
    monkeypatch.setattr(recorder, "_recording", recording)
    monkeypatch.setattr(recorder, "_raw_queue", None)
    monkeypatch.setattr(recorder, "_event_buffer", [])
    monkeypatch.setattr(recorder, "_pause_started_ns", None)
    monkeypatch.setattr(recorder, "_pause_intervals", [])

    recorder.inject_color_trigger(0.25, 0.5, "#112233")
    assert recorder._event_buffer == []
