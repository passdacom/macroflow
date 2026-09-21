"""Resolve explicit, contiguous display selections without widening semantics."""
from __future__ import annotations

from collections.abc import Sequence

from macroflow.input_boundaries import held_inputs
from macroflow.types import AnyEvent, ConditionEvent, LoopEvent, MouseMoveEvent


def resolve_selection(events: Sequence[AnyEvent], rows: Sequence[Sequence[int]],
                      selected: Sequence[int]) -> tuple[int, int]:
    indices = sorted(selected)
    if (not indices or indices != list(range(indices[0], indices[-1] + 1))
            or indices[0] < 0 or indices[-1] >= len(rows)):
        raise ValueError("하나 또는 연속된 표시 행을 선택하세요.")
    covered = {i for row in indices for i in rows[row]}
    if not covered or min(covered) < 0 or max(covered) >= len(events):
        raise ValueError("선택 범위가 변경되었습니다. 다시 선택하세요.")
    start, end = min(covered), max(covered) + 1
    if any(not isinstance(events[i], MouseMoveEvent) for i in range(start, end)
           if i not in covered):
        raise ValueError("선택하지 않은 동작이 포함됩니다. 전체 조합을 선택하세요.")
    if any(isinstance(event, (ConditionEvent, LoopEvent)) for event in events[:end]):
        raise ValueError("중첩 동작의 부분 실행·복사는 지원하지 않습니다.")
    for boundary in (start, end):
        keys, buttons = held_inputs(events[:boundary])
        if keys or buttons:
            raise ValueError("입력 경계가 열려 있습니다. 키 조합·드래그 전체를 선택하세요.")
    return start, end
