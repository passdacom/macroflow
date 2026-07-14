"""시퀀서 항목 추가 검증 회귀 테스트."""

from __future__ import annotations

from pathlib import Path

_SOURCE = Path("src/macroflow/ui/sequencer.py").read_text(encoding="utf-8")


def test_add_item_rejects_missing_files_before_append() -> None:
    """존재하지 않는 파일은 시퀀서 목록 append 전에 차단해야 한다."""
    start = _SOURCE.index("def _add_item")
    end = _SOURCE.index("def _refresh_list_item", start)
    method_src = _SOURCE[start:end]

    assert "normalized_path = path.resolve(strict=False)" in method_src
    assert "if not normalized_path.exists():" in method_src
    assert "찾을 수 없습니다" in method_src
    assert method_src.index("if not normalized_path.exists():") < method_src.index("self._items.append")


def test_add_item_rejects_duplicate_paths_before_append() -> None:
    """같은 매크로 경로는 중복 append 전에 차단해야 한다."""
    start = _SOURCE.index("def _add_item")
    end = _SOURCE.index("def _refresh_list_item", start)
    method_src = _SOURCE[start:end]

    assert "existing.path.resolve(strict=False) == normalized_path" in method_src
    assert "이미 목록에 있습니다" in method_src
    assert method_src.index("existing.path.resolve(strict=False) == normalized_path") < method_src.index("self._items.append")
    assert "_MacroItem(normalized_path)" in method_src
