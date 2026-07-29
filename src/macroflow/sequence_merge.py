"""Pure conversion of heterogeneous sequencer rows into one editable macro."""

from __future__ import annotations

import copy
import dataclasses
import secrets
from collections.abc import Callable, Iterable, Iterator
from pathlib import Path

from macroflow.macro_file import (
    inline_event_block_valid,
    merge_macros,
    settings_types_valid,
)
from macroflow.sequence_limits import MAX_SEQUENCE_WAIT_MS, is_sequence_wait_duration
from macroflow.sequence_model import (
    InlineActionItem,
    MacroFileItem,
    SequenceItem,
    WaitItem,
)
from macroflow.types import (
    AnyEvent,
    ConditionEvent,
    LoopEvent,
    MacroData,
    MacroSettings,
    WaitEvent,
)

MacroLoader = Callable[[Path], MacroData]


def _walk_events(events: Iterable[AnyEvent]) -> Iterator[AnyEvent]:
    for event in events:
        yield event
        if isinstance(event, ConditionEvent):
            yield from _walk_events((*event.if_true, *event.if_false))
        elif isinstance(event, LoopEvent):
            yield from _walk_events(event.events)


def _set_source(events: Iterable[AnyEvent], source: str) -> None:
    for event in _walk_events(events):
        event.source_file = source


def _deduplicate_event_ids(events: Iterable[AnyEvent]) -> None:
    seen: set[str] = set()
    for event in _walk_events(events):
        while event.id in seen:
            event.id = secrets.token_hex(8)
        seen.add(event.id)


def _settings_differences(left: MacroSettings, right: MacroSettings) -> list[str]:
    return [
        field.name
        for field in dataclasses.fields(left)
        if getattr(left, field.name) != getattr(right, field.name)
    ]


def merge_sequence_items(
    items: list[SequenceItem],
    *,
    load_macro: MacroLoader,
    macro_gap_ms: int,
) -> MacroData:
    """Merge sequence rows without mutating their files, settings, or events.

    The legacy macro-only route remains byte-for-behavior compatible with
    ``merge_macros``. Mixed sequences use no implicit gap because their runtime flow
    disables the global macro-gap control. Explicit waits become in-macro ``WaitEvent``
    instances and therefore follow normal macro playback-speed scaling.
    """
    seen_step_ids: set[str] = set()
    for position, item in enumerate(items, start=1):
        if type(item.step_id) is not str or not item.step_id:
            raise ValueError(f"{position}번 단계의 step_id가 올바르지 않습니다.")
        if item.step_id in seen_step_ids:
            raise ValueError(f"중복된 step_id는 병합할 수 없습니다: {item.step_id}")
        seen_step_ids.add(item.step_id)

    loaded: dict[str, MacroData] = {}
    for item in items:
        if isinstance(item, MacroFileItem):
            loaded[item.step_id] = load_macro(item.path)
    if not loaded:
        raise ValueError("에디터 병합에는 매크로 파일이 하나 이상 필요합니다.")

    if all(isinstance(item, MacroFileItem) for item in items):
        return merge_macros(
            [
                (loaded[item.step_id], item.path.name)
                for item in items
                if isinstance(item, MacroFileItem)
            ],
            gap_ms=macro_gap_ms,
        )

    base = next(iter(loaded.values()))
    settings_blocks: list[tuple[int, str, MacroSettings]] = []
    for position, item in enumerate(items, start=1):
        if isinstance(item, MacroFileItem):
            macro = loaded[item.step_id]
            if macro.events:
                settings_blocks.append((position, item.path.name, macro.settings))
        elif isinstance(item, InlineActionItem):
            if not inline_event_block_valid(item.events):
                raise ValueError(f"{position}번 인라인 동작 형식이 올바르지 않습니다: {item.label}")
            if not settings_types_valid(item.playback_settings):
                raise ValueError(f"{position}번 인라인 재생 설정 형식이 올바르지 않습니다.")
            settings_blocks.append((position, item.label, item.playback_settings))
        elif not is_sequence_wait_duration(item.duration_ms):
            raise ValueError(
                f"{position}번 대기 시간은 0~{MAX_SEQUENCE_WAIT_MS}ms 정수여야 합니다."
            )

    output_settings = copy.deepcopy(
        settings_blocks[0][2] if settings_blocks else base.settings
    )
    for position, label, settings in settings_blocks[1:]:
        differences = _settings_differences(output_settings, settings)
        if differences:
            fields = ", ".join(differences)
            raise ValueError(
                f"{position}번 단계({label})의 재생 설정이 다른 단계와 다릅니다: {fields}. "
                "단일 매크로로 정확히 병합하려면 단계별 재생 설정을 같게 맞춰주세요."
            )

    parts: list[tuple[MacroData, str]] = []
    for item in items:
        if isinstance(item, MacroFileItem):
            part = copy.deepcopy(loaded[item.step_id])
            part.meta = copy.deepcopy(base.meta)
            part.settings = copy.deepcopy(output_settings)
            _set_source(part.events, item.path.name)
            parts.append((part, item.path.name))
            continue
        if isinstance(item, InlineActionItem):
            events = copy.deepcopy(item.events)
            source = f"시퀀서: {item.label}"
            _set_source(events, source)
            parts.append(
                (
                    MacroData(
                        meta=copy.deepcopy(base.meta),
                        settings=copy.deepcopy(output_settings),
                        raw_events=copy.deepcopy(events),
                        events=events,
                    ),
                    source,
                )
            )
            continue
        assert isinstance(item, WaitItem)
        source = f"시퀀서: {item.duration_ms}ms 대기"
        wait = WaitEvent(
            id=secrets.token_hex(8),
            type="wait",
            timestamp_ns=0,
            duration_ms=item.duration_ms,
            source_file=source,
        )
        parts.append(
            (
                MacroData(
                    meta=copy.deepcopy(base.meta),
                    settings=copy.deepcopy(output_settings),
                    raw_events=[copy.deepcopy(wait)],
                    events=[wait],
                ),
                source,
            )
        )

    merged = merge_macros(parts, gap_ms=0)
    merged.meta = copy.deepcopy(base.meta)
    merged.settings = copy.deepcopy(output_settings)
    _deduplicate_event_ids(merged.events)
    merged.raw_events = copy.deepcopy(merged.events)
    return merged
