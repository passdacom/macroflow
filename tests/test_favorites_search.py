"""즐겨찾기 검색 필터 존재 여부 테스트."""

from __future__ import annotations

import importlib.util
import sys
import unittest.mock

# PyQt6 는 Linux CI 환경에서 libEGL 없이 import 불가 — 사전 mocking 처리
for _mod in [
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
]:
    if _mod not in sys.modules:
        sys.modules[_mod] = unittest.mock.MagicMock()  # type: ignore[assignment]


def _get_favorites_source() -> str:
    """favorites.py 소스 코드를 직접 읽어 반환한다."""
    spec = importlib.util.find_spec("macroflow.ui.favorites")
    assert spec is not None and spec.origin is not None
    with open(spec.origin, encoding="utf-8") as f:
        return f.read()


def test_favorites_widget_has_apply_search_filter() -> None:
    """FavoritesWidget에 _apply_search_filter 메서드가 정의되어야 한다."""
    src = _get_favorites_source()
    assert "def _apply_search_filter" in src


def test_favorites_widget_has_search_box_in_setup_ui() -> None:
    """FavoritesWidget._setup_ui에 _search_box와 QLineEdit이 있어야 한다."""
    src = _get_favorites_source()
    assert "_search_box" in src
    assert "QLineEdit" in src
