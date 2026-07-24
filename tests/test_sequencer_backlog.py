"""시퀀서 백로그 항목 회귀 테스트."""

from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import macroflow
import macroflow.ui.sequencer as sequencer_module
from macroflow.script_engine import (
    EndNode,
    MacroFlow,
    MacroNode,
    WaitFixedNode,
    iter_linear_macro_paths,
)


def _ui_source(module_name: str) -> str:
    module_path = Path(macroflow.__file__).parent
    for part in module_name.split(".")[1:]:
        module_path /= part
    module_path = module_path.with_suffix(".py")
    with module_path.open(encoding="utf-8") as f:
        return f.read()


def test_linear_macro_paths_walks_through_wait_nodes(tmp_path: Path) -> None:
    """매크로 사이 대기 노드가 있어도 모든 MacroNode 경로를 순서대로 추출한다."""
    base = tmp_path / "flows"
    base.mkdir()
    flow_path = base / "sequence.macroflow"
    outside = tmp_path / "outside.json"

    flow = MacroFlow(
        version="1.0",
        name="sequence",
        created_at="2026-05-01T00:00:00",
        start_node_id="macro_000",
        nodes={
            "macro_000": MacroNode(
                id="macro_000",
                label="first.json",
                macro_path="first.json",
                next_on_success="wait_000",
            ),
            "wait_000": WaitFixedNode(
                id="wait_000",
                label="500ms 대기",
                duration_ms=500,
                next="macro_001",
            ),
            "macro_001": MacroNode(
                id="macro_001",
                label="outside.json",
                macro_path=str(outside),
                next_on_success="end_success",
            ),
            "end_success": EndNode(id="end_success", label="완료"),
        },
    )

    assert list(iter_linear_macro_paths(flow, flow_path)) == [
        base / "first.json",
        outside,
    ]


def test_linear_flow_reports_saved_uniform_gap() -> None:
    """선형 플로우의 균일한 대기 노드는 저장된 매크로 사이 대기로 복원된다."""
    flow = MacroFlow(
        version="1.0",
        name="sequence",
        created_at="2026-07-14T00:00:00",
        start_node_id="macro_000",
        nodes={
            "macro_000": MacroNode(
                id="macro_000",
                label="first.json",
                macro_path="first.json",
                next_on_success="wait_000",
            ),
            "wait_000": WaitFixedNode(
                id="wait_000",
                label="4321ms 대기",
                duration_ms=4321,
                next="macro_001",
            ),
            "macro_001": MacroNode(
                id="macro_001",
                label="second.json",
                macro_path="second.json",
                next_on_success="end_success",
            ),
            "end_success": EndNode(id="end_success", label="완료"),
        },
    )

    assert sequencer_module._linear_gap_ms(flow) == 4321


def test_sequencer_exposes_save_and_save_as_actions() -> None:
    """시퀀서 툴바는 덮어쓰기 저장과 다른 이름 저장 액션을 분리한다."""
    src = _ui_source("macroflow.ui.sequencer")

    assert "_act_save_flow =" in src
    assert "_act_save_flow_as =" in src
    assert "triggered.connect(self._save_flow)" in src
    assert "triggered.connect(self._save_flow_as)" in src


def test_gap_tooltip_distinguishes_runtime_and_merged_timeline_speed() -> None:
    """시퀀스 실제 대기와 병합 timestamp 간격의 speed 의미를 구분한다."""
    src = _ui_source("macroflow.ui.sequencer")

    assert "시퀀스 실행:" in src
    assert "재생 속도는 적용되지 않습니다" in src
    assert "에디터 병합:" in src
    assert "병합 후 재생 속도가 적용됩니다" in src


def test_main_save_shortcuts_route_to_sequencer_on_sequencer_tab() -> None:
    """메인 창 Ctrl+S/다른 이름 저장은 시퀀서 탭에서 플로우 저장으로 위임한다."""
    src = _ui_source("macroflow.ui.main_window")
    save_start = src.index("def _save_file")
    save_end = src.index("def _save_file_as", save_start)
    save_src = src[save_start:save_end]
    save_as_start = save_end
    save_as_end = src.index("def _do_save", save_as_start)
    save_as_src = src[save_as_start:save_as_end]

    assert "self._is_sequencer_tab()" in save_src
    assert "self._sequencer.save_flow()" in save_src
    assert "self._is_sequencer_tab()" in save_as_src
    assert "self._sequencer.save_flow_as()" in save_as_src


def test_favorite_add_to_sequencer_does_not_switch_tabs() -> None:
    """즐겨찾기에서 시퀀서에 추가해도 현재 즐겨찾기 탭을 유지한다."""
    src = _ui_source("macroflow.ui.main_window")
    start = src.index("def _add_favorite_to_sequencer")
    end = src.index("def _restore_prev_macro", start)
    method_src = src[start:end]

    assert "setCurrentWidget(self._sequencer)" not in method_src


def test_favorites_tab_disables_play_toolbar_action() -> None:
    """즐겨찾기 탭에서는 일반 매크로 재생 버튼도 비활성화한다."""
    src = _ui_source("macroflow.ui.main_window")
    start = src.index("def _update_toolbar")
    end = src.index("def _update_range_spinboxes", start)
    method_src = src[start:end]

    assert "elif is_fav_tab:" in method_src
    assert "_act_play.setEnabled(False)" in method_src


def test_sequencer_status_mapping_ignores_wait_and_end_nodes() -> None:
    """대기/종료 노드는 매크로 목록 행 상태를 덮어쓰면 안 된다."""
    src = _ui_source("macroflow.ui.sequencer")
    start = src.index("def _node_id_to_idx")
    end = src.index("# ── 병합", start)
    method_src = src[start:end]

    assert 'node_id.startswith("macro_")' in method_src
    assert 'return -1' in method_src
    assert method_src.index('node_id.startswith("macro_")') < method_src.index('return int(node_id.split("_")[-1])')


def test_sequencer_allows_duplicate_files_with_distinct_step_ids() -> None:
    """같은 파일도 별도 단계 ID로 반복 실행할 수 있어야 한다."""
    src = _ui_source("macroflow.ui.sequencer")
    start = src.index("def _add_item")
    end = src.index("def _refresh_list_item", start)
    method_src = src[start:end]

    assert "normalized_path = path.resolve(strict=False)" in method_src
    assert "existing.path.resolve(strict=False) == normalized_path" not in method_src
    assert "_MacroItem(normalized_path)" in method_src
    assert "step_id" in src
