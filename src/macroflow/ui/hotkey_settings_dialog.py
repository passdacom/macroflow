"""Dialog for editing MacroFlow runtime and editor hotkeys."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QKeySequenceEdit,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from macroflow.hotkey_config import (
    DEFAULT_HOTKEY_CONFIG,
    HOTKEY_SPECS,
    HotkeyConfig,
    HotkeyValidationError,
    validate_hotkey_config,
)

_ERROR_TRANSLATIONS = {
    "runtime binding is required": "글로벌 운영 단축키는 비워둘 수 없습니다.",
    "must be a single chord": "한 번에 누르는 단일 조합만 사용할 수 있습니다.",
    "invalid key sequence": "올바른 키 조합이 아닙니다.",
    "duplicate modifier": "같은 수정 키가 중복되었습니다.",
    "must contain exactly one key": "수정 키 외에 정확히 한 개의 키가 필요합니다.",
    "Windows-key combinations are reserved": "Windows 키 조합은 시스템 충돌 때문에 사용할 수 없습니다.",
    "shortcut is reserved for safety": "안전 또는 시스템 예약 단축키이므로 사용할 수 없습니다.",
    "function key must be F1..F24": "기능 키는 F1부터 F24까지만 사용할 수 있습니다.",
    "runtime binding must be a bare F1..F24 key": "글로벌 운영 단축키는 수정 키 없는 F1~F24만 지원합니다.",
    "shortcut conflicts with a fixed shortcut": "MacroFlow의 고정 편집 단축키와 충돌합니다.",
    "non-function editor keys require a modifier": "일반 키는 Ctrl, Alt 또는 Shift와 함께 지정해야 합니다.",
}


def _error_text(error: HotkeyValidationError) -> str:
    if error.message.startswith("duplicate configurable binding:"):
        key = error.message.partition(":")[2].strip()
        return f"다른 설정 항목과 {key} 단축키가 중복됩니다."
    return _ERROR_TRANSLATIONS.get(error.message, error.message)


class HotkeySettingsDialog(QDialog):
    """Edit a candidate config; registration and persistence stay in MainWindow."""

    def __init__(
        self,
        config: HotkeyConfig,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("단축키 설정")
        self.setMinimumWidth(560)
        self._base_config = config
        self._edits: dict[str, QKeySequenceEdit] = {}

        root = QVBoxLayout(self)
        guidance = QLabel(
            "글로벌 운영 단축키는 녹화 이벤트 누락을 방지하기 위해 수정 키 없는 "
            "F1~F24만 지원합니다. 다른 프로그램이 사용 중인 글로벌 키는 적용 시 감지되며, "
            "충돌하면 기존 설정을 유지합니다. ESC×3 긴급 중지는 변경되지 않습니다."
        )
        guidance.setWordWrap(True)
        root.addWidget(guidance)

        for scope, title in (("runtime", "글로벌 운영"), ("editor", "매크로 에디터 내부")):
            group = QGroupBox(title, self)
            form = QFormLayout(group)
            for spec in HOTKEY_SPECS:
                if spec.scope != scope:
                    continue
                edit = QKeySequenceEdit(QKeySequence(config.binding_for(spec.action_id)), group)
                edit.setObjectName(f"hotkey-{spec.action_id}")
                edit.setClearButtonEnabled(scope == "editor")
                form.addRow(f"{spec.label}:", edit)
                self._edits[spec.action_id] = edit
            root.addWidget(group)

        footer = QLabel("에디터 내부 단축키는 해당 탭이 활성화되고 편집 가능한 상태에서만 실행됩니다.")
        footer.setWordWrap(True)
        footer.setAlignment(Qt.AlignmentFlag.AlignLeft)
        root.addWidget(footer)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        reset = QPushButton("기본값 복원", self)
        reset.clicked.connect(self._restore_defaults)
        self._buttons.addButton(reset, QDialogButtonBox.ButtonRole.ResetRole)
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)
        root.addWidget(self._buttons)

    def _restore_defaults(self) -> None:
        for spec in HOTKEY_SPECS:
            self._edits[spec.action_id].setKeySequence(
                QKeySequence(DEFAULT_HOTKEY_CONFIG.binding_for(spec.action_id))
            )

    def candidate_config(self) -> HotkeyConfig:
        replacements = {
            action_id: edit.keySequence().toString(QKeySequence.SequenceFormat.PortableText)
            for action_id, edit in self._edits.items()
        }
        return self._base_config.with_bindings(replacements)

    def accept(self) -> None:
        candidate = self.candidate_config()
        result = validate_hotkey_config(candidate)
        if not result.is_valid:
            error = result.errors[0]
            spec = next(spec for spec in HOTKEY_SPECS if spec.action_id == error.action_id)
            QMessageBox.warning(
                self,
                "단축키 설정 오류",
                f"{spec.label}: {_error_text(error)}",
            )
            self._edits[error.action_id].setFocus()
            return
        super().accept()
