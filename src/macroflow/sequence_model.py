"""Pure linear sequencer items and lossless MacroFlow projection."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from macroflow.macro_file import inline_event_block_valid, settings_types_valid
from macroflow.script_engine import (
    AnyFlowNode,
    EndNode,
    InlineEventsNode,
    MacroFlow,
    MacroNode,
    WaitFixedNode,
)
from macroflow.sequence_limits import MAX_SEQUENCE_WAIT_MS, is_sequence_wait_duration
from macroflow.types import AnyEvent, MacroSettings


@dataclasses.dataclass
class _RuntimeState:
    status: str = dataclasses.field(default="pending", compare=False)
    message: str = dataclasses.field(default="", compare=False)


@dataclasses.dataclass
class MacroFileItem(_RuntimeState):
    step_id: str = ""
    path: Path = Path()


@dataclasses.dataclass
class InlineActionItem(_RuntimeState):
    step_id: str = ""
    label: str = ""
    events: list[AnyEvent] = dataclasses.field(default_factory=list)
    playback_settings: MacroSettings = dataclasses.field(default_factory=MacroSettings)


@dataclasses.dataclass
class WaitItem(_RuntimeState):
    step_id: str = ""
    duration_ms: int = 0


SequenceItem = MacroFileItem | InlineActionItem | WaitItem


def _next_id(items: list[SequenceItem], index: int) -> str:
    return items[index + 1].step_id if index + 1 < len(items) else "end_success"


def build_sequence_flow(
    items: list[SequenceItem],
    save_path: str | Path,
    *,
    created_at: str,
) -> MacroFlow:
    """Build the canonical v1.1 linear flow for heterogeneous sequence items."""
    if not items:
        raise ValueError("시퀀스 단계가 없습니다.")
    ids = [item.step_id for item in items]
    if any(not step_id for step_id in ids) or len(set(ids)) != len(ids):
        raise ValueError("시퀀스 단계 ID는 비어 있지 않고 고유해야 합니다.")
    if {"end_success", "end_error"} & set(ids):
        raise ValueError("예약된 종료 노드 ID는 단계 ID로 사용할 수 없습니다.")
    for index, item in enumerate(items, start=1):
        if isinstance(item, WaitItem) and not is_sequence_wait_duration(item.duration_ms):
            raise ValueError(
                f"{index}번 대기 시간은 0~{MAX_SEQUENCE_WAIT_MS}ms 정수여야 합니다."
            )
        if isinstance(item, InlineActionItem) and (
            not inline_event_block_valid(item.events)
            or not settings_types_valid(item.playback_settings)
        ):
            raise ValueError(f"{index}번 인라인 액션이 정규 형식이 아닙니다.")

    base = Path(save_path).parent
    nodes: dict[str, AnyFlowNode] = {}
    for index, item in enumerate(items):
        node_id = item.step_id
        next_id = _next_id(items, index)
        position = {"x": 100, "y": 100 + index * 150}
        if isinstance(item, MacroFileItem):
            try:
                macro_path = str(item.path.relative_to(base)).replace("\\", "/")
            except ValueError:
                macro_path = str(item.path).replace("\\", "/")
            nodes[node_id] = MacroNode(
                id=node_id,
                label=item.path.name,
                macro_path=macro_path,
                next_on_success=next_id,
                next_on_failure="end_error",
                position=position,
            )
        elif isinstance(item, InlineActionItem):
            nodes[node_id] = InlineEventsNode(
                id=node_id,
                label=item.label,
                events=list(item.events),
                playback_settings=item.playback_settings,
                next_on_success=next_id,
                next_on_failure="end_error",
                position=position,
            )
        else:
            nodes[node_id] = WaitFixedNode(
                id=node_id,
                label=f"{item.duration_ms}ms 대기",
                duration_ms=item.duration_ms,
                next=next_id,
                position=position,
            )

    end_y = 100 + len(items) * 150
    nodes["end_success"] = EndNode(
        id="end_success",
        label="완료",
        status="success",
        position={"x": 100, "y": end_y},
    )
    if any(isinstance(item, (MacroFileItem, InlineActionItem)) for item in items):
        nodes["end_error"] = EndNode(
            id="end_error",
            label="오류 종료",
            status="error",
            position={"x": 350, "y": end_y},
        )
    return MacroFlow(
        version="1.1",
        name="sequence",
        created_at=created_at,
        start_node_id=items[0].step_id,
        nodes=nodes,
    )


def _resolved_macro_path(node: MacroNode, flow_path: Path) -> Path:
    raw = Path(node.macro_path)
    return (
        raw.resolve(strict=False)
        if raw.is_absolute()
        else (flow_path.parent / raw).resolve(strict=False)
    )


def _validate_failure_edge(
    node_id: str | None,
    flow: MacroFlow,
    error_end_ids: set[str],
) -> None:
    if node_id is None:
        return
    target = flow.nodes.get(node_id)
    if not isinstance(target, EndNode) or target.status != "error":
        raise ValueError("단순 시퀀서의 실패 경로는 오류 종료 노드여야 합니다.")
    error_end_ids.add(node_id)


def project_sequence_flow(
    flow: MacroFlow,
    flow_path: str | Path,
) -> list[SequenceItem]:
    """Project a lossless linear v1.0/v1.1 flow into heterogeneous sequence items."""
    if flow.version not in {"1.0", "1.1"}:
        raise ValueError(f"지원하지 않는 플로우 버전: {flow.version!r}")
    path = Path(flow_path)
    current_id: str | None = flow.start_node_id
    visited: set[str] = set()
    error_end_ids: set[str] = set()
    items: list[SequenceItem] = []

    while current_id is not None:
        if current_id in visited:
            raise ValueError("순환 플로우는 단순 시퀀서로 열 수 없습니다.")
        node = flow.nodes.get(current_id)
        if node is None:
            raise ValueError(f"노드 ID를 찾을 수 없습니다: {current_id!r}")
        visited.add(current_id)

        if isinstance(node, MacroNode):
            _validate_failure_edge(node.next_on_failure, flow, error_end_ids)
            items.append(
                MacroFileItem(
                    step_id=node.id,
                    path=_resolved_macro_path(node, path),
                )
            )
            current_id = node.next_on_success
        elif isinstance(node, InlineEventsNode):
            _validate_failure_edge(node.next_on_failure, flow, error_end_ids)
            items.append(
                InlineActionItem(
                    step_id=node.id,
                    label=node.label,
                    events=list(node.events),
                    playback_settings=node.playback_settings,
                )
            )
            current_id = node.next_on_success
        elif isinstance(node, WaitFixedNode):
            if not is_sequence_wait_duration(node.duration_ms):
                raise ValueError(
                    f"대기 시간은 0~{MAX_SEQUENCE_WAIT_MS}ms 정수여야 합니다: {node.id}"
                )
            items.append(WaitItem(step_id=node.id, duration_ms=node.duration_ms))
            current_id = node.next
        elif isinstance(node, EndNode):
            if node.status != "success":
                raise ValueError("성공 경로가 오류 종료 노드로 연결되어 있습니다.")
            current_id = None
        else:
            raise ValueError(
                "분기 또는 지원하지 않는 노드가 있어 단순 시퀀서로 열 수 없습니다."
            )

    if not items:
        raise ValueError("실행 단계가 없는 플로우는 단순 시퀀서로 열 수 없습니다.")
    if visited | error_end_ids != set(flow.nodes):
        raise ValueError("시퀀서에 표시되지 않는 노드가 있어 로드를 거부했습니다.")

    if flow.version == "1.1":
        expected = build_sequence_flow(items, path, created_at=flow.created_at)
        if flow != expected:
            raise ValueError(
                "정규 시퀀서 문서가 아닌 선형 플로우는 원본 정보를 보존할 수 없어 "
                "열 수 없습니다."
            )
    return items
