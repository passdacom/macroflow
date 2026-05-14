"""Pure event insertion helpers for the MacroFlow event editor.

This module intentionally stays free of Qt widget dependencies so insertion timing
semantics can be regression-tested on headless CI.
"""

from __future__ import annotations

import dataclasses
import secrets
from collections.abc import Callable, Sequence
from typing import Literal

from macroflow.types import AnyEvent, ColorTriggerEvent, MouseButtonEvent, TextInputEvent

IdFactory = Callable[[], str]

_MIN_INSERT_BUDGET_NS = 1_000_000
_CLICK_UP_OFFSET_NS = 100_000_000
_DOUBLE_CLICK_SECOND_DOWN_OFFSET_NS = 100_000_000
_DOUBLE_CLICK_UP_OFFSET_NS = 50_000_000
_COLOR_TRIGGER_BUDGET_NS = 1_000_000_000


def _default_id() -> str:
    return secrets.token_hex(4)


def _selected_insert_after_event_idx(
    row_event_indices: Sequence[Sequence[int]],
    selected_rows: Sequence[int],
    events_len: int,
) -> int:
    """Return the source event index after which an editor insertion should occur."""
    if selected_rows:
        last_row_idx = selected_rows[-1]
        if 0 <= last_row_idx < len(row_event_indices):
            return max(row_event_indices[last_row_idx])
    return events_len - 1


def _base_timestamp_ns(events: Sequence[AnyEvent], insert_after_event_idx: int) -> int:
    if 0 <= insert_after_event_idx < len(events):
        return events[insert_after_event_idx].timestamp_ns
    if events:
        return events[-1].timestamp_ns
    return 0


def _insert_and_shift_events(
    events: Sequence[AnyEvent],
    insert_after_event_idx: int,
    new_events: Sequence[AnyEvent],
    shift_budget_ns: int,
) -> list[AnyEvent]:
    """Insert events after an index and shift following timestamps to preserve timing."""
    updated = list(events)
    insert_at = insert_after_event_idx + 1
    for offset, new_event in enumerate(new_events):
        updated.insert(insert_at + offset, new_event)

    shift_start = insert_at + len(new_events)
    for idx in range(shift_start, len(updated)):
        event = updated[idx]
        updated[idx] = dataclasses.replace(
            event,
            timestamp_ns=event.timestamp_ns + shift_budget_ns,
        )
    return updated


def _insert_text_input_event(
    events: Sequence[AnyEvent],
    insert_after_event_idx: int,
    text: str,
    delay_ms: int,
    id_factory: IdFactory = _default_id,
) -> list[AnyEvent]:
    """Return events with one TextInputEvent inserted and later timestamps shifted."""
    budget_ns = max(delay_ms * 1_000_000, _MIN_INSERT_BUDGET_NS)
    delay_override_ms = delay_ms if delay_ms > 0 else None
    base_ts_ns = _base_timestamp_ns(events, insert_after_event_idx)
    new_event = TextInputEvent(
        id=id_factory(),
        type="text_input",
        timestamp_ns=base_ts_ns + budget_ns,
        delay_override_ms=delay_override_ms,
        text=text,
    )
    return _insert_and_shift_events(
        events,
        insert_after_event_idx,
        [new_event],
        budget_ns,
    )


def _insert_click_events(
    events: Sequence[AnyEvent],
    insert_after_event_idx: int,
    x_ratio: float,
    y_ratio: float,
    button: Literal["left", "right", "middle"],
    is_double: bool,
    delay_ms: int,
    recorded_color: str | None,
    id_factory: IdFactory = _default_id,
) -> list[AnyEvent]:
    """Return events with click or double-click MouseButtonEvents inserted."""
    budget_ns = max(delay_ms * 1_000_000, _MIN_INSERT_BUDGET_NS)
    delay_override_ms = delay_ms if delay_ms > 0 else None
    base_ts_ns = _base_timestamp_ns(events, insert_after_event_idx)

    def _make_down(ts_ns: int, dly: int | None) -> MouseButtonEvent:
        return MouseButtonEvent(
            id=id_factory(),
            type="mouse_down",
            timestamp_ns=ts_ns,
            x_ratio=x_ratio,
            y_ratio=y_ratio,
            button=button,
            delay_override_ms=dly,
            recorded_color=recorded_color,
        )

    def _make_up(ts_ns: int) -> MouseButtonEvent:
        return MouseButtonEvent(
            id=id_factory(),
            type="mouse_up",
            timestamp_ns=ts_ns,
            x_ratio=x_ratio,
            y_ratio=y_ratio,
            button=button,
        )

    if is_double:
        new_events: list[AnyEvent] = [
            _make_down(base_ts_ns + budget_ns, delay_override_ms),
            _make_up(base_ts_ns + budget_ns + _DOUBLE_CLICK_UP_OFFSET_NS),
            _make_down(base_ts_ns + budget_ns + _DOUBLE_CLICK_SECOND_DOWN_OFFSET_NS, None),
            _make_up(
                base_ts_ns
                + budget_ns
                + _DOUBLE_CLICK_SECOND_DOWN_OFFSET_NS
                + _DOUBLE_CLICK_UP_OFFSET_NS
            ),
        ]
        total_budget = budget_ns + _DOUBLE_CLICK_SECOND_DOWN_OFFSET_NS + _DOUBLE_CLICK_UP_OFFSET_NS
    else:
        new_events = [
            _make_down(base_ts_ns + budget_ns, delay_override_ms),
            _make_up(base_ts_ns + budget_ns + _CLICK_UP_OFFSET_NS),
        ]
        total_budget = budget_ns + _CLICK_UP_OFFSET_NS

    return _insert_and_shift_events(events, insert_after_event_idx, new_events, total_budget)


def _insert_color_trigger_event(
    events: Sequence[AnyEvent],
    insert_after_event_idx: int,
    x_ratio: float,
    y_ratio: float,
    target_color: str,
    id_factory: IdFactory = _default_id,
) -> list[AnyEvent]:
    """Return events with one infinite-wait ColorTriggerEvent inserted."""
    base_ts_ns = _base_timestamp_ns(events, insert_after_event_idx)
    new_event = ColorTriggerEvent(
        id=id_factory(),
        type="color_trigger",
        timestamp_ns=base_ts_ns + _COLOR_TRIGGER_BUDGET_NS,
        delay_override_ms=None,
        x_ratio=x_ratio,
        y_ratio=y_ratio,
        target_color=target_color,
        tolerance=10,
        timeout_ms=0,
    )
    return _insert_and_shift_events(
        events,
        insert_after_event_idx,
        [new_event],
        _COLOR_TRIGGER_BUDGET_NS,
    )
