"""Event editor insertion/timestamp helper regression tests."""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from macroflow.types import AnyEvent, ColorTriggerEvent, MouseButtonEvent, TextInputEvent, WaitEvent
from macroflow.ui.editor_insertions import (
    _insert_click_events,
    _insert_color_trigger_event,
    _insert_text_input_event,
    _selected_insert_after_event_idx,
)


def _ids() -> Iterator[str]:
    for i in range(1, 100):
        yield f"id{i:06d}"


def _wait(id_: str, ts_ns: int) -> WaitEvent:
    return WaitEvent(id=id_, type="wait", timestamp_ns=ts_ns, duration_ms=10)


def test_selected_insert_after_event_idx_uses_last_selected_display_row_tail() -> None:
    assert _selected_insert_after_event_idx(
        row_event_indices=[[0], [1, 2, 3], [4]],
        selected_rows=[0, 1],
        events_len=5,
    ) == 3


def test_selected_insert_after_event_idx_defaults_to_last_event_when_no_selection() -> None:
    assert _selected_insert_after_event_idx(
        row_event_indices=[[0], [1]],
        selected_rows=[],
        events_len=2,
    ) == 1
    assert _selected_insert_after_event_idx(
        row_event_indices=[],
        selected_rows=[],
        events_len=0,
    ) == -1


def test_insert_text_input_event_places_text_after_group_and_shifts_following_events() -> None:
    events: list[AnyEvent] = [
        _wait("before", 1_000_000_000),
        _wait("group-a", 2_000_000_000),
        _wait("group-b", 2_100_000_000),
        _wait("after", 3_000_000_000),
    ]

    updated = _insert_text_input_event(
        events,
        insert_after_event_idx=2,
        text="안녕",
        delay_ms=250,
        id_factory=iter(["text001"]).__next__,
    )

    inserted = updated[3]
    assert isinstance(inserted, TextInputEvent)
    assert inserted.id == "text001"
    assert inserted.timestamp_ns == 2_350_000_000
    assert inserted.delay_override_ms == 250
    assert inserted.text == "안녕"
    assert updated[4].id == "after"
    assert updated[4].timestamp_ns == 3_250_000_000
    assert events[3].timestamp_ns == 3_000_000_000


def test_insert_text_input_event_uses_minimum_one_ms_budget_for_zero_delay() -> None:
    updated = _insert_text_input_event(
        [_wait("base", 10_000_000)],
        insert_after_event_idx=0,
        text="x",
        delay_ms=0,
        id_factory=iter(["text002"]).__next__,
    )

    inserted = updated[1]
    assert isinstance(inserted, TextInputEvent)
    assert inserted.timestamp_ns == 11_000_000
    assert inserted.delay_override_ms is None


def test_insert_click_events_creates_double_click_sequence_and_shifts_tail() -> None:
    ids = _ids()
    events: list[AnyEvent] = [
        _wait("base", 1_000_000_000),
        _wait("after", 5_000_000_000),
    ]

    updated = _insert_click_events(
        events,
        insert_after_event_idx=0,
        x_ratio=0.25,
        y_ratio=0.75,
        button="right",
        is_double=True,
        delay_ms=100,
        recorded_color="#112233",
        id_factory=ids.__next__,
    )

    inserted = updated[1:5]
    assert [event.type for event in inserted] == [
        "mouse_down",
        "mouse_up",
        "mouse_down",
        "mouse_up",
    ]
    assert [event.timestamp_ns for event in inserted] == [
        1_100_000_000,
        1_150_000_000,
        1_200_000_000,
        1_250_000_000,
    ]
    assert all(isinstance(event, MouseButtonEvent) for event in inserted)
    first_down = inserted[0]
    second_down = inserted[2]
    assert isinstance(first_down, MouseButtonEvent)
    assert isinstance(second_down, MouseButtonEvent)
    assert first_down.button == "right"
    assert first_down.delay_override_ms == 100
    assert first_down.recorded_color == "#112233"
    assert second_down.delay_override_ms is None
    assert updated[5].id == "after"
    assert updated[5].timestamp_ns == 5_250_000_000


def test_insert_color_trigger_event_uses_one_second_budget_and_infinite_timeout() -> None:
    events: list[AnyEvent] = [
        _wait("base", 1_500_000_000),
        _wait("after", 2_000_000_000),
    ]

    updated = _insert_color_trigger_event(
        events,
        insert_after_event_idx=0,
        x_ratio=0.1,
        y_ratio=0.2,
        target_color="#ABCDEF",
        id_factory=iter(["color01"]).__next__,
    )

    inserted = updated[1]
    assert isinstance(inserted, ColorTriggerEvent)
    assert inserted.id == "color01"
    assert inserted.timestamp_ns == 2_500_000_000
    assert inserted.delay_override_ms is None
    assert inserted.x_ratio == pytest.approx(0.1)
    assert inserted.y_ratio == pytest.approx(0.2)
    assert inserted.target_color == "#ABCDEF"
    assert inserted.tolerance == 10
    assert inserted.timeout_ms == 0
    assert updated[2].timestamp_ns == 3_000_000_000
