"""Conservative, Qt-free analysis of raw input boundaries.

Provenance labels are never execution boundaries. Callers supply placements.
"""
from __future__ import annotations

import secrets
from collections.abc import Iterable, Iterator

from macroflow.types import AnyEvent, ConditionEvent, KeyEvent, LoopEvent, MouseButtonEvent


def walk_events(events: Iterable[AnyEvent]) -> Iterator[AnyEvent]:
    for event in events:
        yield event
        if isinstance(event, ConditionEvent):
            yield from walk_events((*event.if_true, *event.if_false))
        elif isinstance(event, LoopEvent):
            yield from walk_events(event.events)


def held_inputs(events: Iterable[AnyEvent]) -> tuple[dict[int, KeyEvent], set[str]]:
    """Reject branch-dependent input state rather than inventing releases."""
    keys: dict[int, KeyEvent] = {}
    buttons: set[str] = set()
    for event in events:
        if isinstance(event, (ConditionEvent, LoopEvent)):
            if any(isinstance(child, (KeyEvent, MouseButtonEvent))
                   for child in walk_events([event])):
                raise ValueError("중첩 입력 경계를 확정할 수 없습니다. 플로우를 사용하세요.")
        elif isinstance(event, KeyEvent):
            if event.type == "key_down":
                keys[event.vk_code] = event
            else:
                if event.vk_code not in keys:
                    raise ValueError("짝이 없는 키 해제입니다. 전체 조합을 확인하거나 플로우를 사용하세요.")
                keys.pop(event.vk_code, None)
        elif isinstance(event, MouseButtonEvent):
            if event.type == "mouse_down":
                buttons.add(event.button)
            else:
                if event.button not in buttons:
                    raise ValueError("짝이 없는 마우스 해제입니다. 플로우를 사용하세요.")
                buttons.discard(event.button)
    return keys, buttons


def placement_releases(events: list[AnyEvent]) -> list[AnyEvent]:
    """Append only still-held keys at the original placement's last timestamp."""
    keys, buttons = held_inputs(events)
    if buttons:
        raise ValueError("열린 마우스 버튼은 자동 병합할 수 없습니다. 플로우를 사용하세요.")
    if not events:
        return []
    return [KeyEvent(id=secrets.token_hex(8), type="key_up",
                     timestamp_ns=events[-1].timestamp_ns, key=event.key, vk_code=vk,
                     source_file=events[-1].source_file,
                     remark="병합 경계에서 열린 키 해제")
            for vk, event in reversed(list(keys.items()))]


def deduplicate_event_ids(events: Iterable[AnyEvent]) -> None:
    """Keep the first occurrence; remap only later collisions recursively."""
    seen: set[str] = set()
    for event in walk_events(events):
        while event.id in seen:
            event.id = secrets.token_hex(8)
        seen.add(event.id)
