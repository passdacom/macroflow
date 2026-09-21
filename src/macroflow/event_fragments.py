"""Same-document memory fragments; never use the operating-system clipboard."""
from __future__ import annotations

import copy
import dataclasses
import secrets
from collections.abc import Sequence

from macroflow.input_boundaries import held_inputs, walk_events
from macroflow.types import AnyEvent


@dataclasses.dataclass(frozen=True)
class EventFragment:
    events: tuple[AnyEvent, ...]
    leading_ns: int


def copy_fragment(events: Sequence[AnyEvent], start: int, end: int) -> EventFragment:
    if not 0 <= start < end <= len(events):
        raise ValueError("복사 범위가 올바르지 않습니다.")
    selected = events[start:end]
    if any(b.timestamp_ns < a.timestamp_ns for a, b in zip(events[:end], events[1:end], strict=False)):
        raise ValueError("역행하는 기록 시점은 복사할 수 없습니다.")
    leading = selected[0].timestamp_ns - events[start - 1].timestamp_ns if start else 0
    return EventFragment(tuple(copy.deepcopy(selected)), leading)


def paste_fragment(events: Sequence[AnyEvent], raw_events: Sequence[AnyEvent],
                   fragment: EventFragment, insert_at: int) -> list[AnyEvent]:
    if not 0 <= insert_at <= len(events):
        raise ValueError("붙여넣기 위치가 변경되었습니다.")
    keys, buttons = held_inputs(events[:insert_at])
    if keys or buttons:
        raise ValueError("키 조합·드래그 내부에는 붙여넣을 수 없습니다.")
    inserted = copy.deepcopy(list(fragment.events))
    if not inserted:
        raise ValueError("복사된 동작이 없습니다.")
    used = {event.id for event in walk_events([*events, *raw_events, *inserted])}
    for event in walk_events(inserted):
        candidate = secrets.token_hex(8)
        while candidate in used:
            candidate = secrets.token_hex(8)
        event.id = candidate
        used.add(candidate)
    base = events[insert_at - 1].timestamp_ns if insert_at else 0
    span = inserted[-1].timestamp_ns - inserted[0].timestamp_ns + fragment.leading_ns
    offset = base + fragment.leading_ns - inserted[0].timestamp_ns
    for event in inserted:
        event.timestamp_ns += offset
    result = copy.deepcopy(list(events))
    for event in result[insert_at:]:
        event.timestamp_ns += span
    result[insert_at:insert_at] = inserted
    return result
