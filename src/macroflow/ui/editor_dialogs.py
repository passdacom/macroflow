"""Small widget factories shared by MacroFlow editor dialogs."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDoubleSpinBox, QLabel, QPushButton, QSpinBox

CAPTURE_BUTTON_TEXT = "📍 화면에서 직접 지정 (F6으로 지정)"
CAPTURE_BUTTON_TOOLTIP = "버튼 클릭 후 원하는 위치로 마우스를 이동하고 F6을 누르세요."
CAPTURE_LABEL_STYLE = "color: #c07000; font-weight: bold;"
PERCENT_SUFFIX = " %"
DELAY_SUFFIX = " ms"


def create_percentage_spin(value_percent: float, *, tooltip: str | None = None) -> QDoubleSpinBox:
    """Create a position percentage spin box with the editor's shared bounds."""
    spin = QDoubleSpinBox()
    spin.setRange(-500.0, 500.0)
    spin.setDecimals(2)
    spin.setSuffix(PERCENT_SUFFIX)
    if tooltip is not None:
        spin.setToolTip(tooltip)
    spin.setValue(value_percent)
    return spin


def create_delay_spin(value_ms: int, *, maximum_ms: int = 30000) -> QSpinBox:
    """Create a millisecond delay spin box with the editor's shared suffix."""
    spin = QSpinBox()
    spin.setRange(0, maximum_ms)
    spin.setValue(value_ms)
    spin.setSuffix(DELAY_SUFFIX)
    return spin


def create_capture_controls() -> tuple[QLabel, QPushButton]:
    """Create the standard F6 capture label/button pair used in editor dialogs."""
    label = QLabel("")
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.setStyleSheet(CAPTURE_LABEL_STYLE)

    button = QPushButton(CAPTURE_BUTTON_TEXT)
    button.setToolTip(CAPTURE_BUTTON_TOOLTIP)
    return label, button
