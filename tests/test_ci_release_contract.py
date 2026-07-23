"""GitHub Actions release safety contract."""

from __future__ import annotations

from pathlib import Path

WORKFLOW = Path(".github/workflows/build.yml")


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_ci_uses_locked_dependencies_on_linux_and_windows() -> None:
    source = _workflow_text()

    assert source.count("uv sync --locked --extra dev --extra ui-test --python 3.11") == 2


def test_windows_job_runs_source_tests_and_packaged_exe_smoke() -> None:
    source = _workflow_text()

    assert "Run pytest on Windows" in source
    assert "uv run pytest tests/ -v" in source
    assert "Smoke packaged EXE" in source
    assert "MainWindowHandle" in source
    assert "Stop-Process" in source


def test_release_requires_manual_dispatch() -> None:
    source = _workflow_text()

    assert "workflow_dispatch:" in source
    assert "github.event_name == 'workflow_dispatch'" in source
    assert "github.event_name == 'push'" not in source
