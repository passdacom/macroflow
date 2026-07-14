"""선형 플로우 경로 정규화 회귀 테스트."""

from __future__ import annotations

from pathlib import Path

from macroflow.script_engine import (
    EndNode,
    MacroFlow,
    MacroNode,
    WaitFixedNode,
    iter_linear_macro_paths,
)


def test_iter_linear_macro_paths_normalizes_relative_dot_segments(tmp_path: Path) -> None:
    """../ 가 섞인 상대 경로도 같은 실제 파일 경로로 정규화해야 한다."""
    base = tmp_path / "flows"
    macros = tmp_path / "macros"
    base.mkdir()
    macros.mkdir()
    flow_path = base / "sequence.macroflow"

    flow = MacroFlow(
        version="1.0",
        name="sequence",
        created_at="2026-06-22T00:00:00",
        start_node_id="macro_000",
        nodes={
            "macro_000": MacroNode(
                id="macro_000",
                label="first.json",
                macro_path="../macros/first.json",
                next_on_success="wait_000",
            ),
            "wait_000": WaitFixedNode(
                id="wait_000",
                label="250ms 대기",
                duration_ms=250,
                next="macro_001",
            ),
            "macro_001": MacroNode(
                id="macro_001",
                label="second.json",
                macro_path="../macros/../macros/second.json",
                next_on_success="end_success",
            ),
            "end_success": EndNode(id="end_success", label="완료"),
        },
    )

    assert list(iter_linear_macro_paths(flow, flow_path)) == [
        (macros / "first.json").resolve(strict=False),
        (macros / "second.json").resolve(strict=False),
    ]
