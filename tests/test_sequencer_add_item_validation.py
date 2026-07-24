"""시퀀서 항목 추가 검증 회귀 테스트."""

from __future__ import annotations

from pathlib import Path

_SOURCE = Path("src/macroflow/ui/sequencer.py").read_text(encoding="utf-8")


def test_add_item_rejects_missing_files_before_insert() -> None:
    """존재하지 않는 파일은 시퀀서 목록 insert 전에 차단해야 한다."""
    start = _SOURCE.index("def _add_item")
    end = _SOURCE.index("def _refresh_list_item", start)
    method_src = _SOURCE[start:end]

    assert "normalized_path = path.resolve(strict=False)" in method_src
    assert "if not normalized_path.exists():" in method_src
    assert "찾을 수 없습니다" in method_src
    assert method_src.index("if not normalized_path.exists():") < method_src.index(
        "self._insert_sequence_item(item)"
    )


def test_add_item_allows_duplicate_paths_as_distinct_steps() -> None:
    """같은 매크로 파일을 여러 단계에서 의도적으로 재실행할 수 있어야 한다."""
    start = _SOURCE.index("def _add_item")
    end = _SOURCE.index("def _refresh_list_item", start)
    method_src = _SOURCE[start:end]

    assert "_MacroItem(normalized_path)" in method_src
    assert "existing.path.resolve(strict=False) == normalized_path" not in method_src
    assert "self._insert_sequence_item(item)" in method_src
