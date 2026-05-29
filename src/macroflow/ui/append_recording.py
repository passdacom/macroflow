"""Helpers for appending a fresh recording to an existing macro.

This module is intentionally PyQt-free so timestamp merge semantics can be
unit-tested without constructing the MainWindow.
"""

from __future__ import annotations

import dataclasses

from macroflow.types import AnyEvent, MacroData

_DEFAULT_APPEND_GAP_MS = 250
_NS_PER_MS = 1_000_000


def shift_event_timestamps(
    events: list[AnyEvent],
    *,
    first_timestamp_ns: int,
) -> list[AnyEvent]:
    """Return copies of ``events`` shifted so the first event starts at a timestamp.

    Relative delays between the appended events are preserved. The input events are
    never mutated.
    """
    if not events:
        return []

    first_original_timestamp_ns = events[0].timestamp_ns
    return [
        dataclasses.replace(
            event,
            timestamp_ns=first_timestamp_ns + event.timestamp_ns - first_original_timestamp_ns,
        )
        for event in events
    ]


def append_recording(
    base_macro: MacroData,
    recorded_macro: MacroData,
    *,
    gap_ms: int = _DEFAULT_APPEND_GAP_MS,
) -> MacroData:
    """Append a newly recorded macro to ``base_macro`` and return a new MacroData.

    The first newly recorded event is placed after the latest existing event plus
    ``gap_ms``. Existing metadata/settings are preserved so the current file keeps
    its identity and compatibility settings.
    """
    base_events = list(base_macro.events)
    recorded_events = list(recorded_macro.events)
    if not recorded_events:
        return MacroData(
            meta=base_macro.meta,
            settings=base_macro.settings,
            raw_events=base_macro.raw_events,
            events=base_events,
            is_edited=True,
        )

    last_base_timestamp_ns = max((event.timestamp_ns for event in base_events), default=0)
    append_start_ns = last_base_timestamp_ns + max(0, gap_ms) * _NS_PER_MS
    shifted_events = shift_event_timestamps(
        recorded_events,
        first_timestamp_ns=append_start_ns,
    )
    return MacroData(
        meta=base_macro.meta,
        settings=base_macro.settings,
        raw_events=base_macro.raw_events,
        events=base_events + shifted_events,
        is_edited=True,
    )
