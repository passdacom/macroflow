"""UI package import boundaries."""

from __future__ import annotations

import subprocess
import sys


def test_editor_rows_import_does_not_eagerly_import_pyqt_widgets() -> None:
    """순수 표시 row 모듈은 PyQt 런타임 의존성 없이 import 가능해야 한다."""
    code = "from macroflow.ui.editor_rows import _build_rows; print(_build_rows.__name__)"

    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "_build_rows"
