"""Pure contracts for editor tail deletion and playback ranges."""

from __future__ import annotations

from macroflow.types import MouseButtonEvent, MouseMoveEvent, WaitEvent
from macroflow.ui.editor_actions import delete_after_group, range_from_group_to_end


def _down(event_id: str, timestamp_ns: int) -> MouseButtonEvent:
    return MouseButtonEvent(
        id=event_id,
        type="mouse_down",
        timestamp_ns=timestamp_ns,
        x_ratio=0.5,
        y_ratio=0.5,
        button="left",
    )


def _up(event_id: str, timestamp_ns: int) -> MouseButtonEvent:
    return MouseButtonEvent(
        id=event_id,
        type="mouse_up",
        timestamp_ns=timestamp_ns,
        x_ratio=0.5,
        y_ratio=0.5,
        button="left",
    )


def test_delete_after_group_keeps_selected_click_completion_and_removes_tail() -> None:
    events = [
        WaitEvent(id="before", type="wait", timestamp_ns=10_000_000_000, duration_ms=10),
        _down("click-down", 49_900_000_000),
        _up("click-up", 50_000_000_000),
        MouseMoveEvent(
            id="tail-move",
            type="mouse_move",
            timestamp_ns=50_100_000_000,
            x_ratio=0.6,
            y_ratio=0.6,
        ),
        WaitEvent(id="tail", type="wait", timestamp_ns=100_000_000_000, duration_ms=10),
    ]

    kept = delete_after_group(events, [1, 2])

    assert [event.id for event in kept] == ["before", "click-down", "click-up"]
    assert kept[-1].timestamp_ns == 50_000_000_000
    assert [event.id for event in events][-2:] == ["tail-move", "tail"]


def test_delete_after_last_group_is_noop_without_copy_churn() -> None:
    events = [_down("down", 1), _up("up", 2)]

    assert delete_after_group(events, [0, 1]) is events


def test_range_from_group_to_end_starts_at_complete_semantic_action() -> None:
    assert range_from_group_to_end([20, 21, 22], total_events=100) == (20, 100)
