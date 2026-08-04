"""Fourth-tab UI for five persistent one-shot macro slots."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFocusEvent, QKeySequence
from PyQt6.QtWidgets import (
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QKeySequenceEdit,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from macroflow.hotkey_config import HotkeyConfig
from macroflow.quick_run import QuickRunSlot


class _SafeKeySequenceEdit(QKeySequenceEdit):
    """Report focus ownership so global automation keys can be suspended."""

    editing_changed = pyqtSignal(bool)

    def focusInEvent(self, event: QFocusEvent | None) -> None:  # noqa: N802
        self.editing_changed.emit(True)
        super().focusInEvent(event)

    def focusOutEvent(self, event: QFocusEvent | None) -> None:  # noqa: N802
        super().focusOutEvent(event)
        self.editing_changed.emit(False)


class QuickRunWidget(QWidget):
    """Edit and invoke five explicit human-gated quick-run slots."""

    configuration_requested = pyqtSignal(object, object)
    run_requested = pyqtSignal(object)
    hotkey_editing_changed = pyqtSignal(bool)

    def __init__(
        self,
        slots: tuple[QuickRunSlot, ...],
        hotkey_config: HotkeyConfig,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._name_edits: list[QLineEdit] = []
        self._path_edits: list[QLineEdit] = []
        self._speed_spins: list[QDoubleSpinBox] = []
        self._hotkey_edits: list[QKeySequenceEdit] = []
        self._run_buttons: list[QPushButton] = []

        root = QVBoxLayout(self)
        intro = QLabel(
            "자주 쓰는 매크로를 슬롯에 연결하면 글로벌 단축키로 한 번만 실행합니다. "
            "한 슬롯이 끝난 뒤 다음 슬롯은 사용자가 직접 실행해야 합니다."
        )
        intro.setWordWrap(True)
        root.addWidget(intro)

        scroll = QScrollArea(self)
        scroll.setObjectName("quick-run-scroll")
        scroll.setWidgetResizable(True)
        slot_container = QWidget(scroll)
        slot_layout = QVBoxLayout(slot_container)

        for slot in slots:
            group = QGroupBox(f"슬롯 {slot.index}", self)
            grid = QGridLayout(group)
            grid.addWidget(QLabel("이름:"), 0, 0)
            name_edit = QLineEdit(slot.name, group)
            name_edit.setObjectName(f"quick-run-name-{slot.index}")
            grid.addWidget(name_edit, 0, 1, 1, 3)

            grid.addWidget(QLabel("매크로:"), 1, 0)
            path_edit = QLineEdit(
                str(slot.macro_path) if slot.macro_path is not None else "",
                group,
            )
            path_edit.setObjectName(f"quick-run-path-{slot.index}")
            path_edit.setReadOnly(True)
            path_edit.setPlaceholderText("연결된 매크로 없음")
            grid.addWidget(path_edit, 1, 1)
            choose = QPushButton("매크로 선택...", group)
            choose.clicked.connect(
                lambda _checked=False, index=slot.index: self._choose_macro(index)
            )
            grid.addWidget(choose, 1, 2)
            clear = QPushButton("연결 해제", group)
            clear.clicked.connect(
                lambda _checked=False, index=slot.index: self._path_edits[index - 1].clear()
            )
            grid.addWidget(clear, 1, 3)

            grid.addWidget(QLabel("재생 속도:"), 2, 0)
            speed_spin = QDoubleSpinBox(group)
            speed_spin.setObjectName(f"quick-run-speed-{slot.index}")
            speed_spin.setRange(0.1, 10.0)
            speed_spin.setSingleStep(0.1)
            speed_spin.setDecimals(1)
            speed_spin.setSuffix("x")
            speed_spin.setValue(slot.speed)
            speed_spin.setToolTip("이 슬롯만 재생할 때 적용할 속도 배율")
            grid.addWidget(speed_spin, 2, 1)

            grid.addWidget(QLabel("단축키:"), 3, 0)
            hotkey_edit = _SafeKeySequenceEdit(
                QKeySequence(hotkey_config.binding_for(slot.action_id)),
                group,
            )
            hotkey_edit.setObjectName(f"quick-run-hotkey-{slot.index}")
            hotkey_edit.editing_changed.connect(self.hotkey_editing_changed)
            grid.addWidget(hotkey_edit, 3, 1)
            run = QPushButton(f"슬롯 {slot.index} 지금 실행", group)
            run.clicked.connect(
                lambda _checked=False, index=slot.index: self._request_run(index)
            )
            grid.addWidget(run, 3, 2, 1, 2)

            self._name_edits.append(name_edit)
            self._path_edits.append(path_edit)
            self._speed_spins.append(speed_spin)
            self._hotkey_edits.append(hotkey_edit)
            self._run_buttons.append(run)
            slot_layout.addWidget(group)

        slot_layout.addStretch(1)
        scroll.setWidget(slot_container)
        root.addWidget(scroll, 1)

        controls = QHBoxLayout()
        controls.addStretch(1)
        apply_button = QPushButton("빠른 실행 설정 적용", self)
        apply_button.setObjectName("quick-run-apply")
        apply_button.clicked.connect(self._apply_changes)
        controls.addWidget(apply_button)
        root.addLayout(controls)

    def _choose_macro(self, index: int) -> None:
        current = self._path_edits[index - 1].text().strip()
        start_dir = str(Path(current).parent) if current else str(Path.cwd())
        path, _ = QFileDialog.getOpenFileName(
            self,
            f"빠른 실행 슬롯 {index} 매크로 선택",
            start_dir,
            "Macro JSON (*.json);;모든 파일 (*)",
        )
        if path:
            self._path_edits[index - 1].setText(path)

    def _apply_changes(self) -> None:
        try:
            slots = tuple(self._slot_from_inputs(index) for index in range(1, 6))
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "빠른 실행 설정 오류", str(exc))
            return
        bindings = {
            slot.action_id: self._hotkey_edits[slot.index - 1]
            .keySequence()
            .toString(QKeySequence.SequenceFormat.PortableText)
            for slot in slots
        }
        self.configuration_requested.emit(slots, bindings)

    def _slot_from_inputs(self, index: int) -> QuickRunSlot:
        raw_path = self._path_edits[index - 1].text().strip()
        return QuickRunSlot(
            index=index,
            name=self._name_edits[index - 1].text(),
            macro_path=Path(raw_path) if raw_path else None,
            speed=self._speed_spins[index - 1].value(),
        )

    def _request_run(self, index: int) -> None:
        try:
            slot = self._slot_from_inputs(index)
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            QMessageBox.warning(self, "빠른 실행 설정 오류", str(exc))
            return
        self.run_requested.emit(slot)

    def set_configuration(
        self,
        slots: tuple[QuickRunSlot, ...],
        hotkey_config: HotkeyConfig,
    ) -> None:
        for slot in slots:
            index = slot.index - 1
            self._name_edits[index].setText(slot.name)
            self._path_edits[index].setText(
                str(slot.macro_path) if slot.macro_path is not None else ""
            )
            self._speed_spins[index].setValue(slot.speed)
            self._hotkey_edits[index].setKeySequence(
                QKeySequence(hotkey_config.binding_for(slot.action_id))
            )

    def set_busy(self, busy: bool) -> None:
        for button in self._run_buttons:
            button.setEnabled(not busy)
