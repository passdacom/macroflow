"""Qt table rendering helpers for the MacroFlow event editor.

This module intentionally contains Qt-dependent rendering helpers only.  Pure
row construction remains in :mod:`macroflow.ui.editor_rows` so it can stay
headless-importable.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QTableWidgetItem, QWidget


def _is_hex_color(value: str | None) -> bool:
    """QSS 색상 박스에 안전하게 사용할 수 있는 #RRGGBB 값인지 검사한다."""
    if value is None or len(value) != 7 or not value.startswith("#"):
        return False
    return all(c in "0123456789abcdefABCDEF" for c in value[1:])


def _color_detail_widget(detail: str, color_hex: str | None) -> QWidget:
    """내용 텍스트와 실제 색상 swatch 박스를 함께 보여주는 셀 위젯."""
    widget = QWidget()
    layout = QHBoxLayout(widget)
    layout.setContentsMargins(4, 0, 4, 0)
    layout.setSpacing(6)

    text_label = QLabel(detail)
    text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(text_label)

    if _is_hex_color(color_hex):
        swatch = QLabel()
        swatch.setFixedSize(18, 18)
        swatch.setToolTip(color_hex)
        swatch.setStyleSheet(
            f"background-color: {color_hex}; border: 1px solid #666; border-radius: 2px;"
        )
        layout.addWidget(swatch)

    layout.addStretch(1)
    return widget


def _cell(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item
