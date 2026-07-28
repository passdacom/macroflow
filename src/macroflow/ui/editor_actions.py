"""Pure editor tail-action helpers."""

from __future__ import annotations

from macroflow.types import AnyEvent


def delete_after_group(events: list[AnyEvent], event_indices: list[int]) -> list[AnyEvent]:
    """Keep a complete selected semantic group and remove every later event."""
    if not event_indices:
        return events
    cut_after = max(event_indices)
    if cut_after >= len(events) - 1:
        return events
    return events[: cut_after + 1]


def range_from_group_to_end(
    event_indices: list[int],
    *,
    total_events: int,
) -> tuple[int, int]:
    """Return an end-exclusive playback range from a complete display group."""
    if not event_indices or total_events <= 0:
        raise ValueError("재생할 동작 범위가 없습니다")
    start = min(event_indices)
    if start < 0 or start >= total_events:
        raise ValueError("재생 시작 동작이 범위를 벗어났습니다")
    return start, total_events