"""이어서 녹화 append helper tests."""

from __future__ import annotations

from macroflow.types import KeyEvent, MacroData, MacroMeta, MacroSettings, MouseMoveEvent
from macroflow.ui.append_recording import append_recording, shift_event_timestamps


def _macro(events: list[KeyEvent | MouseMoveEvent]) -> MacroData:
    return MacroData(
        meta=MacroMeta(
            version="1.0",
            app_version="test",
            created_at="2026-05-29T00:00:00",
            screen_width=1920,
            screen_height=1080,
            dpi_scale=1.0,
        ),
        settings=MacroSettings(),
        raw_events=list(events),
        events=list(events),
    )


def _key(event_id: str, timestamp_ns: int) -> KeyEvent:
    return KeyEvent(
        id=event_id,
        type="key_down",
        timestamp_ns=timestamp_ns,
        key="a",
        vk_code=0x41,
    )


def _move(event_id: str, timestamp_ns: int) -> MouseMoveEvent:
    return MouseMoveEvent(
        id=event_id,
        type="mouse_move",
        timestamp_ns=timestamp_ns,
        x_ratio=0.5,
        y_ratio=0.5,
    )


def test_shift_event_timestamps_preserves_relative_deltas_and_original_events() -> None:
    events = [_key("a1", 100_000_000), _key("a2", 350_000_000)]

    shifted = shift_event_timestamps(events, first_timestamp_ns=1_000_000_000)

    assert [event.timestamp_ns for event in shifted] == [1_000_000_000, 1_250_000_000]
    assert [event.timestamp_ns for event in events] == [100_000_000, 350_000_000]


def test_append_recording_places_new_events_after_base_last_event_with_gap() -> None:
    base = _macro([_key("old", 2_000_000_000)])
    recorded = _macro([_move("new1", 100_000_000), _key("new2", 400_000_000)])

    combined = append_recording(base, recorded, gap_ms=250)

    assert [event.id for event in combined.events] == ["old", "new1", "new2"]
    assert [event.timestamp_ns for event in combined.events] == [
        2_000_000_000,
        2_250_000_000,
        2_550_000_000,
    ]
    assert combined.meta is base.meta
    assert combined.settings is base.settings
    assert combined.is_edited is True


def test_append_recording_empty_capture_returns_edited_copy_without_timestamp_error() -> None:
    base = _macro([_key("old", 2_000_000_000)])
    recorded = _macro([])

    combined = append_recording(base, recorded)

    assert [event.id for event in combined.events] == ["old"]
    assert combined.events is not base.events
    assert combined.is_edited is True
