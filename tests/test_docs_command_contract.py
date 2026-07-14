"""개발/검증 명령 문서 계약 테스트."""

from __future__ import annotations

from pathlib import Path


def test_claude_commands_use_project_venv_friendly_uv_run() -> None:
    """CLAUDE 명령 예시는 바깥 active venv와 무관하게 프로젝트 .venv를 사용해야 한다."""
    source = Path("CLAUDE.md").read_text(encoding="utf-8")

    assert "uv sync --extra dev" in source
    assert "uv run pytest -q" in source
    assert "uv run ruff check ." in source
    assert "uv run mypy src/" in source
    assert "uv run --active mypy src/" not in source
    assert "로컬에서 mypy를 실행할 수 없으므로" not in source


def test_linux_side_smoke_docs_use_uv_run_pytest() -> None:
    """RDP smoke 관련 Linux 계약 테스트 문서는 uv run pytest 형태로 통일한다."""
    smoke_doc = Path("docs/rdp-gui-smoke-test.md").read_text(encoding="utf-8")
    target_doc = Path("docs/macroflow-test-target-app.md").read_text(encoding="utf-8")

    expected = "uv run pytest tests/test_test_target_app_contract.py tests/test_rdp_gui_smoke_harness.py -q"
    assert expected in smoke_doc
    assert expected in target_doc
