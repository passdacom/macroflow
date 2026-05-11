"""패키지 버전 표시 테스트."""

from __future__ import annotations

import tomllib
from pathlib import Path

import macroflow


def test_package_version_matches_project_metadata() -> None:
    """메인 창 타이틀에 쓰는 __version__은 pyproject 버전과 일치해야 한다."""
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    assert macroflow.__version__ == pyproject["project"]["version"]


def test_qapplication_version_uses_package_version() -> None:
    """QApplication 버전도 하드코딩하지 않고 패키지 버전을 사용해야 한다."""
    main_source = Path("src/macroflow/main.py").read_text(encoding="utf-8")

    assert 'app.setApplicationVersion(__version__)' in main_source
    assert 'app.setApplicationVersion("0.1.0")' not in main_source
