"""Lossless sequencer-to-editor merge contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from macroflow.macro_file import load, merge_macros, save
from macroflow.sequence_merge import merge_sequence_items
from macroflow.sequence_model import InlineActionItem, MacroFileItem, SequenceItem, WaitItem
from macroflow.types import (
    AnyEvent,
    ConditionEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    TextInputEvent,
    WaitEvent,
)


def _macro(*events: object) -> MacroData:
    return MacroData(
        meta=MacroMeta(
            version="1.0",
            app_version="test",
            created_at="2026-07-29T00:00:00",
            screen_width=1920,
            screen_height=1080,
            dpi_scale=1.0,
        ),
        settings=MacroSettings(),
        raw_events=list(events),  # type: ignore[arg-type]
        events=list(events),  # type: ignore[arg-type]
    )


def test_mixed_sequence_merges_files_inline_actions_and_wait_without_implicit_gaps(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    first = _macro(
        MouseMoveEvent(
            id="same-id",
            type="mouse_move",
            timestamp_ns=100_000_000,
            x_ratio=0.1,
            y_ratio=0.1,
        )
    )
    second = _macro(
        MouseMoveEvent(
            id="same-id",
            type="mouse_move",
            timestamp_ns=300_000_000,
            x_ratio=0.9,
            y_ratio=0.9,
        )
    )
    macros = {first_path: first, second_path: second}
    text = TextInputEvent(id="text", type="text_input", timestamp_ns=0, text="HELLO")
    click: list[AnyEvent] = [
        MouseButtonEvent(
            id="down",
            type="mouse_down",
            timestamp_ns=0,
            x_ratio=0.5,
            y_ratio=0.5,
        ),
        MouseButtonEvent(
            id="up",
            type="mouse_up",
            timestamp_ns=50_000_000,
            x_ratio=0.5,
            y_ratio=0.5,
        ),
    ]
    items: list[SequenceItem] = [
        MacroFileItem(step_id="m1", path=first_path),
        InlineActionItem(step_id="text", label="문구 입력: HELLO", events=[text]),
        WaitItem(step_id="wait", duration_ms=750),
        InlineActionItem(step_id="click", label="left 클릭", events=click),
        MacroFileItem(step_id="m2", path=second_path),
    ]

    merged = merge_sequence_items(
        items,
        load_macro=lambda path: macros[path],
        macro_gap_ms=500,
    )

    assert [type(event) for event in merged.events] == [
        MouseMoveEvent,
        TextInputEvent,
        WaitEvent,
        MouseButtonEvent,
        MouseButtonEvent,
        MouseMoveEvent,
    ]
    assert [event.source_file for event in merged.events] == [
        "first.json",
        "시퀀서: 문구 입력: HELLO",
        "시퀀서: 750ms 대기",
        "시퀀서: left 클릭",
        "시퀀서: left 클릭",
        "second.json",
    ]
    assert isinstance(merged.events[2], WaitEvent)
    assert merged.events[2].duration_ms == 750
    assert merged.events[1].timestamp_ns == merged.events[0].timestamp_ns
    assert merged.events[2].timestamp_ns == merged.events[1].timestamp_ns
    assert merged.events[3].timestamp_ns == merged.events[2].timestamp_ns
    assert merged.events[-1].timestamp_ns == merged.events[4].timestamp_ns
    assert len({event.id for event in merged.events}) == len(merged.events)
    assert merged.raw_events == merged.events
    assert merged.raw_events is not merged.events
    assert merged.is_edited is True
    assert first.events[0].id == "same-id"
    assert first.events[0].source_file == ""
    assert second.events[0].id == "same-id"

    output_path = tmp_path / "merged.json"
    save(merged, str(output_path))
    reloaded = load(str(output_path))
    assert reloaded.events == merged.events
    assert len({event.id for event in reloaded.events}) == len(reloaded.events)


def test_macro_only_sequence_keeps_configured_gap(tmp_path: Path) -> None:
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    macros = {
        first_path: _macro(
            MouseMoveEvent(
                id="first",
                type="mouse_move",
                timestamp_ns=100_000_000,
                x_ratio=0.1,
                y_ratio=0.1,
            )
        ),
        second_path: _macro(
            MouseMoveEvent(
                id="second",
                type="mouse_move",
                timestamp_ns=900_000_000,
                x_ratio=0.2,
                y_ratio=0.2,
            )
        ),
    }

    items: list[SequenceItem] = [
        MacroFileItem(step_id="m1", path=first_path),
        MacroFileItem(step_id="m2", path=second_path),
    ]
    expected = merge_macros(
        [(macros[first_path], "first.json"), (macros[second_path], "second.json")],
        gap_ms=500,
    )
    merged = merge_sequence_items(
        items,
        load_macro=lambda path: macros[path],
        macro_gap_ms=500,
    )

    assert merged.events[1].timestamp_ns - merged.events[0].timestamp_ns == 500_000_000
    assert merged == expected


def test_mixed_merge_rejects_different_step_playback_settings(tmp_path: Path) -> None:
    macro_path = tmp_path / "base.json"
    macro = _macro(
        TextInputEvent(id="base", type="text_input", timestamp_ns=0, text="BASE")
    )
    inline = InlineActionItem(
        step_id="text",
        label="문구 입력: HELLO",
        events=[TextInputEvent(id="text", type="text_input", timestamp_ns=0, text="HELLO")],
    )
    inline.playback_settings.default_playback_speed = 2.0

    with pytest.raises(ValueError, match="default_playback_speed"):
        merge_sequence_items(
            [MacroFileItem(step_id="m1", path=macro_path), inline],
            load_macro=lambda _path: macro,
            macro_gap_ms=0,
        )


def test_mixed_merge_normalizes_nested_source_and_duplicate_ids(tmp_path: Path) -> None:
    macro_path = tmp_path / "nested.json"
    nested = TextInputEvent(id="duplicate", type="text_input", timestamp_ns=0, text="A")
    condition = ConditionEvent(
        id="condition",
        type="condition",
        timestamp_ns=0,
        expression="True",
        if_true=[nested],
        if_false=[],
    )
    macro = _macro(condition)
    inline = InlineActionItem(
        step_id="text",
        label="문구 입력: B",
        events=[
            TextInputEvent(
                id="duplicate",
                type="text_input",
                timestamp_ns=0,
                text="B",
            )
        ],
    )

    merged = merge_sequence_items(
        [MacroFileItem(step_id="m1", path=macro_path), inline],
        load_macro=lambda _path: macro,
        macro_gap_ms=0,
    )

    merged_condition = merged.events[0]
    assert isinstance(merged_condition, ConditionEvent)
    assert merged_condition.if_true[0].source_file == "nested.json"
    assert merged.events[1].id != merged_condition.if_true[0].id
    assert nested.id == "duplicate"
    assert nested.source_file == ""


def test_mixed_merge_requires_at_least_one_macro_for_document_metadata() -> None:
    item = InlineActionItem(
        step_id="text",
        label="문구 입력: HELLO",
        events=[TextInputEvent(id="text", type="text_input", timestamp_ns=0, text="HELLO")],
    )

    with pytest.raises(ValueError, match="매크로 파일이 하나 이상"):
        merge_sequence_items([item, WaitItem(step_id="wait", duration_ms=100)], load_macro=lambda _path: _macro(), macro_gap_ms=0)


def test_merge_rejects_duplicate_step_ids_before_loading(tmp_path: Path) -> None:
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    load_calls: list[Path] = []

    def loader(path: Path) -> MacroData:
        load_calls.append(path)
        return _macro(
            TextInputEvent(id=path.stem, type="text_input", timestamp_ns=0, text=path.stem)
        )

    with pytest.raises(ValueError, match="중복.*step_id"):
        merge_sequence_items(
            [
                MacroFileItem(step_id="duplicate", path=first_path),
                MacroFileItem(step_id="duplicate", path=second_path),
            ],
            load_macro=loader,
            macro_gap_ms=0,
        )
    assert load_calls == []


@pytest.mark.parametrize("duration", [True, 1.5, -1, 30001])
def test_merge_rejects_invalid_wait_duration(
    tmp_path: Path,
    duration: object,
) -> None:
    macro_path = tmp_path / "base.json"
    macro = _macro(
        TextInputEvent(id="base", type="text_input", timestamp_ns=0, text="BASE")
    )
    wait = WaitItem(step_id="wait", duration_ms=duration)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="대기 시간"):
        merge_sequence_items(
            [MacroFileItem(step_id="macro", path=macro_path), wait],
            load_macro=lambda _path: macro,
            macro_gap_ms=0,
        )
