"""Resizable composer for recording one semantic text-input event."""

from __future__ import annotations

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class QuickTextDialog(QDialog):
    """Large paste-friendly editor; ordinary Enter remains a newline."""

    def __init__(self, parent: QWidget | None = None, *, trigger_label: str = "F9") -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{trigger_label} 빠른 텍스트 기록")
        self.resize(720, 480)

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel(
                "문구를 입력하거나 다른 창에서 복사해 붙여넣으세요.\n"
                "저장하거나 취소할 때까지 시간과 마우스·키보드 동작은 기록되지 않습니다."
            )
        )
        self._editor = QPlainTextEdit(self)
        self._editor.setPlaceholderText("긴 문구와 줄바꿈을 그대로 입력할 수 있습니다.")
        layout.addWidget(self._editor)
        layout.addWidget(QLabel("비밀번호·OTP·토큰 등 비밀값은 매크로에 저장하지 마세요."))

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        assert save_button is not None and cancel_button is not None
        save_button.setText("저장 (Ctrl+Enter)")
        cancel_button.setText("취소")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.accept)
        QShortcut(QKeySequence("Ctrl+Enter"), self).activated.connect(self.accept)
        self._editor.setFocus()

    def text(self) -> str:
        return self._editor.toPlainText()
