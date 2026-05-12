"""Qt table rendering helpers for the MacroFlow event editor.

This module intentionally contains Qt-dependent rendering helpers only.  Pure
row construction remains in :mod:`macroflow.ui.editor_rows` so it can stay
headless-importable.
"""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QTableWidgetItem, QWidget

COL_INDEX = 0
COL_TYPE = 1
COL_CONTENT = 2
COL_REMARK = 3
COL_TIME = 4
COL_DELAY = 5
COL_SOURCE = 6
COLUMNS = ["#", "타입", "내용", "비고", "시간(ms)", "딜레이(ms)", "출처"]
CONTENT_COLUMN_REFERENCE_TEXT = "(00.0%, 00.0%) [#000000] 색깔"
CONTENT_COLUMN_MIN_WIDTH = len(CONTENT_COLUMN_REFERENCE_TEXT) * 9


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


def _table_row_items(
    row: Any,
    *,
    row_number: int,
    relative_time: bool,
    kind_color: QColor,
) -> list[QTableWidgetItem]:
    """표시 row 하나를 QTableWidgetItem 목록으로 렌더링한다."""
    source_item = _cell(row.source_file)
    source_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    content_item = _cell("" if _is_hex_color(row.color_hex) else row.detail)
    items = [
        _cell(str(row_number)),
        _cell(row.label),
        content_item,
        _cell(f"📝 {row.remark}" if row.remark else ""),
        _cell(f"{row.time_ms_rel:.0f}" if relative_time else f"{row.time_ms:.0f}"),
        _cell(row.delay_str),
        source_item,
    ]

    items[COL_TYPE].setBackground(QBrush(kind_color))
    items[COL_TYPE].setForeground(QBrush(QColor(255, 255, 255)))

    for col, item in enumerate(items):
        if col != COL_SOURCE:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    return items
