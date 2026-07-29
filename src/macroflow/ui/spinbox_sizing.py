"""Font-aware sizing for compact toolbar spin boxes."""

from __future__ import annotations

from collections.abc import Iterable

from PyQt6.QtWidgets import QAbstractSpinBox

_COMPACT_BUTTON_WIDTH_PX = 14
_COMPACT_SPIN_STYLE = """
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    width: 14px;
}
"""


def fit_compact_spinbox(
    spin: QAbstractSpinBox,
    samples: Iterable[str],
    *,
    minimum_width: int,
) -> None:
    """Fit representative values while retaining vertically stacked compact arrows."""
    spin.setStyleSheet(_COMPACT_SPIN_STYLE)
    text_width = max(spin.fontMetrics().horizontalAdvance(sample) for sample in samples)
    frame_and_padding = 24
    spin.setFixedWidth(
        max(minimum_width, text_width + _COMPACT_BUTTON_WIDTH_PX + frame_and_padding)
    )
