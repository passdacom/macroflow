"""Isolated linear snapshots for a contiguous visible flow range."""
from __future__ import annotations

import copy
from pathlib import Path

from macroflow.script_engine import MacroFlow, MacroNode, WaitFixedNode
from macroflow.sequence_model import MacroFileItem, SequenceItem, build_sequence_flow


def selected_flow(items: list[SequenceItem], selected: list[int], path: Path,
                  *, macro_gap_ms: int) -> MacroFlow:
    indices = sorted(selected)
    if (not indices or indices != list(range(indices[0], indices[-1] + 1))
            or indices[0] < 0 or indices[-1] >= len(items)):
        raise ValueError("하나 또는 연속된 플로우 행을 선택하세요.")
    subset = copy.deepcopy(items[indices[0]:indices[-1] + 1])
    flow = build_sequence_flow(subset, path, created_at="")
    if all(isinstance(item, MacroFileItem) for item in items) and macro_gap_ms > 0:
        for index, item in enumerate(subset[:-1]):
            node = flow.nodes[item.step_id]
            assert isinstance(node, MacroNode)
            gap_id = f"__selected_gap_{index}"
            while gap_id in flow.nodes:
                gap_id += "_"
            flow.nodes[gap_id] = WaitFixedNode(id=gap_id, label="단계 사이 대기",
                duration_ms=macro_gap_ms, next=node.next_on_success)
            node.next_on_success = gap_id
    return flow
