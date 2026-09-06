"""Explicit shortcut chooser: no physical chord capture or keyboard hooks."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from macroflow.ui.editor_dialogs import create_delay_spin
from macroflow.ui.editor_keys import NAME_TO_VK
from macroflow.ui.shortcut_events import SHORTCUT_PRESETS


class ShortcutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("키 / 단축키 동작 추가")
        layout = QVBoxLayout(self)
        hint = QLabel("키를 직접 누르지 말고 목록에서 선택하세요.\n"
                      "실제 입력 없이 매크로에 key_down / key_up 동작만 추가합니다.")
        layout.addWidget(hint)
        form = QFormLayout()
        self.preset = QComboBox()
        self.preset.addItems([label for label, _, _ in SHORTCUT_PRESETS])
        self.preset.addItem("직접 지정 (Custom)")
        form.addRow("자주 쓰는 동작:", self.preset)
        modifier_layout = QHBoxLayout()
        self.modifiers = {}
        for name, label in (("ctrl", "Ctrl"), ("alt", "Alt"),
                            ("shift", "Shift"), ("lwin", "Win")):
            checkbox = QCheckBox(label)
            self.modifiers[name] = checkbox
            modifier_layout.addWidget(checkbox)
        form.addRow("수식 키:", modifier_layout)
        self.key = QComboBox()
        self.key.addItems(sorted(NAME_TO_VK))
        form.addRow("키 이름:", self.key)
        self.delay = create_delay_spin(1000)
        form.addRow("실행 전 대기:", self.delay)
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.preset.currentIndexChanged.connect(self._select_preset)
        self._select_preset(0)

    def _select_preset(self, index: int) -> None:
        if not 0 <= index < len(SHORTCUT_PRESETS):
            return
        _, key, modifiers = SHORTCUT_PRESETS[index]
        self.key.setCurrentText(key)
        for name, checkbox in self.modifiers.items():
            checkbox.setChecked(name in modifiers)

    def shortcut(self) -> tuple[str, tuple[str, ...], int]:
        return (self.key.currentText(),
                tuple(name for name, box in self.modifiers.items() if box.isChecked()),
                self.delay.value())
