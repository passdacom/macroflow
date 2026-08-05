"""Pure heterogeneous sequencer model contracts."""

from __future__ import annotations

from pathlib import Path

import pytest

from macroflow.sequence_model import (
    InlineActionItem,
    MacroFileItem,
    SequenceItem,
    WaitItem,
    build_sequence_flow,
    project_sequence_flow,
)
from macroflow.types import MacroSettings, TextInputEvent


def test_builder_rejects_empty_inline_action_before_persistence(tmp_path: Path) -> None:
    item = InlineActionItem(
        step_id="inline",
        label="invalid",
        events=[],
        playback_settings=MacroSettings(),
    )

    with pytest.raises(ValueError, match="인라인"):
        build_sequence_flow(
            [item],
            tmp_path / "invalid.macroflow",
            created_at="2026-08-05T00:00:00",
        )


def test_v11_mixed_sequence_roundtrips_with_duplicate_macro_paths(tmp_path: Path) -> None:
    macro = (tmp_path / "same.json").resolve(strict=False)
    flow_path = tmp_path / "mixed.macroflow"
    items = [
        MacroFileItem(step_id="macro-a", path=macro),
        InlineActionItem(
            step_id="inline-text",
            label="문구 입력: HELLO",
            events=[
                TextInputEvent(
                    id="text-1",
                    type="text_input",
                    timestamp_ns=0,
                    text="HELLO",
                )
            ],
            playback_settings=MacroSettings(click_dist_threshold_px=13),
        ),
        WaitItem(step_id="wait-a", duration_ms=750),
        MacroFileItem(step_id="macro-b", path=macro),
    ]

    flow = build_sequence_flow(
        items,
        flow_path,
        created_at="2026-07-24T00:00:00",
    )
    projected = project_sequence_flow(flow, flow_path)

    assert flow.version == "1.1"
    assert projected == items
    assert [item.step_id for item in projected] == [
        "macro-a",
        "inline-text",
        "wait-a",
        "macro-b",
    ]


def test_v10_macro_wait_flow_projects_without_semantic_change(tmp_path: Path) -> None:
    from macroflow.script_engine import EndNode, MacroFlow, MacroNode, WaitFixedNode

    flow_path = tmp_path / "legacy.macroflow"
    flow = MacroFlow(
        version="1.0",
        name="sequence",
        created_at="2026-07-16T00:00:00",
        start_node_id="macro_000",
        nodes={
            "macro_000": MacroNode(
                id="macro_000",
                label="first.json",
                macro_path="first.json",
                next_on_success="wait_000",
                next_on_failure="end_error",
                position={"x": 100, "y": 100},
            ),
            "wait_000": WaitFixedNode(
                id="wait_000",
                label="500ms 대기",
                duration_ms=500,
                next="macro_001",
                position={"x": 100, "y": 200},
            ),
            "macro_001": MacroNode(
                id="macro_001",
                label="second.json",
                macro_path="second.json",
                next_on_success="end_success",
                next_on_failure="end_error",
                position={"x": 100, "y": 300},
            ),
            "end_success": EndNode(
                id="end_success",
                label="완료",
                status="success",
                position={"x": 100, "y": 500},
            ),
            "end_error": EndNode(
                id="end_error",
                label="오류 종료",
                status="error",
                position={"x": 350, "y": 250},
            ),
        },
    )

    items = project_sequence_flow(flow, flow_path)

    assert items == [
        MacroFileItem(
            step_id="macro_000",
            path=(tmp_path / "first.json").resolve(strict=False),
        ),
        WaitItem(step_id="wait_000", duration_ms=500),
        MacroFileItem(
            step_id="macro_001",
            path=(tmp_path / "second.json").resolve(strict=False),
        ),
    ]


def test_projection_rejects_inline_failure_branch_that_is_not_error_end(
    tmp_path: Path,
) -> None:
    from macroflow.script_engine import EndNode, InlineEventsNode, MacroFlow

    flow_path = tmp_path / "branch.macroflow"
    inline = InlineActionItem(
        step_id="inline",
        label="문구",
        events=[
            TextInputEvent(
                id="text",
                type="text_input",
                timestamp_ns=0,
                text="x",
            )
        ],
        playback_settings=MacroSettings(),
    )
    flow = MacroFlow(
        version="1.1",
        name="branch",
        created_at="2026-07-24T00:00:00",
        start_node_id="inline",
        nodes={
            "inline": InlineEventsNode(
                id="inline",
                label=inline.label,
                events=inline.events,
                playback_settings=inline.playback_settings,
                next_on_success="end_success",
                next_on_failure="end_success",
                position={"x": 100, "y": 100},
            ),
            "end_success": EndNode(id="end_success", label="완료"),
        },
    )

    with pytest.raises(ValueError, match="실패 경로"):
        project_sequence_flow(flow, flow_path)


@pytest.mark.parametrize("duration", [True, 1.5, -1, 30001])
def test_build_rejects_wait_outside_sequencer_contract(
    tmp_path: Path,
    duration: object,
) -> None:
    wait = WaitItem(step_id="wait", duration_ms=duration)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="대기 시간"):
        build_sequence_flow(
            [wait],
            tmp_path / "invalid.macroflow",
            created_at="2026-07-29T00:00:00",
        )


@pytest.mark.parametrize("duration", [True, 1.5, -1, 30001])
def test_projection_rejects_wait_outside_sequencer_contract(
    tmp_path: Path,
    duration: object,
) -> None:
    from macroflow.script_engine import EndNode, MacroFlow, WaitFixedNode

    flow = MacroFlow(
        version="1.0",
        name="invalid wait",
        created_at="2026-07-29T00:00:00",
        start_node_id="wait",
        nodes={
            "wait": WaitFixedNode(
                id="wait",
                label="wait",
                duration_ms=duration,  # type: ignore[arg-type]
                next="end_success",
            ),
            "end_success": EndNode(id="end_success", label="완료"),
        },
    )

    with pytest.raises(ValueError, match="대기 시간"):
        project_sequence_flow(flow, tmp_path / "invalid.macroflow")


@pytest.mark.parametrize("duration", [0, 30000])
def test_wait_contract_boundaries_roundtrip(tmp_path: Path, duration: int) -> None:
    flow_path = tmp_path / "boundary.macroflow"
    items: list[SequenceItem] = [WaitItem(step_id="wait", duration_ms=duration)]

    flow = build_sequence_flow(
        items,
        flow_path,
        created_at="2026-07-29T00:00:00",
    )

    assert project_sequence_flow(flow, flow_path) == items
