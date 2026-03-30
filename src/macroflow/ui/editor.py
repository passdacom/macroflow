"""MacroFlow 이벤트 에디터 위젯.

QTableWidget으로 MacroData.events를 표시하고
딜레이 수정·이벤트 삭제·마우스이동 제거·원본 복원 기능을 제공한다.
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QFont
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from macroflow.macro_file import delete_mouse_moves, reset_to_raw, set_delay_all
from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    ConditionEvent,
    KeyEvent,
    LoopEvent,
    MacroData,
    MouseButtonEvent,
    MouseMoveEvent,
    WaitEvent,
    WindowTriggerEvent,
)

logger = logging.getLogger(__name__)

# ── 이벤트 타입별 색상 ──────────────────────────────────────────────────────────
_TYPE_COLORS: dict[str, QColor] = {
    "mouse_down":     QColor(60,  110, 200),
    "mouse_up":       QColor(80,  140, 220),
    "mouse_move":     QColor(90,  90,  90),
    "key_down":       QColor(60,  145, 85),
    "key_up":         QColor(90,  170, 110),
    "wait":           QColor(190, 120, 50),
    "color_trigger":  QColor(140, 80,  170),
    "window_trigger": QColor(140, 80,  170),
    "condition":      QColor(170, 140, 40),
    "loop":           QColor(170, 140, 40),
}

_COLUMNS = ["#", "타입", "시간(ms)", "X%", "Y%", "키/버튼", "딜레이(ms)"]


def _cell(text: str, editable: bool = False) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    if not editable:
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


def _event_detail(event: AnyEvent) -> tuple[str, str, str, str]:
    """(x%, y%, key_button, time_ms) 문자열 반환."""
    x_s = y_s = key_btn = ""
    if isinstance(event, (MouseButtonEvent, MouseMoveEvent)):
        x_s = f"{event.x_ratio * 100:.1f}"
        y_s = f"{event.y_ratio * 100:.1f}"
        if isinstance(event, MouseButtonEvent):
            key_btn = event.button
    elif isinstance(event, KeyEvent):
        key_btn = event.key
    elif isinstance(event, WaitEvent):
        key_btn = f"{event.duration_ms}ms"
    elif isinstance(event, ColorTriggerEvent):
        x_s = f"{event.x_ratio * 100:.1f}"
        y_s = f"{event.y_ratio * 100:.1f}"
        key_btn = event.target_color
    elif isinstance(event, WindowTriggerEvent):
        key_btn = event.window_title_contains
    elif isinstance(event, ConditionEvent):
        key_btn = event.expression[:20]
    elif isinstance(event, LoopEvent):
        key_btn = f"×{event.count}"
    return x_s, y_s, key_btn


class EventEditorWidget(QWidget):
    """이벤트 목록을 표·편집하는 위젯."""

    macro_changed = pyqtSignal(object)  # MacroData

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._macro: MacroData | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 편집 도구바
        toolbar = QToolBar("편집 도구", self)
        toolbar.setMovable(False)

        self._act_del_moves = QAction("마우스 이동 제거", self)
        self._act_del_moves.setToolTip("events에서 mouse_move 이벤트를 모두 삭제합니다.")
        self._act_del_moves.triggered.connect(self._delete_mouse_moves)
        self._act_del_moves.setEnabled(False)
        toolbar.addAction(self._act_del_moves)

        self._act_set_delay = QAction("딜레이 일괄 설정", self)
        self._act_set_delay.setToolTip("모든 이벤트의 딜레이를 동일한 값으로 설정합니다.")
        self._act_set_delay.triggered.connect(self._set_delay_all)
        self._act_set_delay.setEnabled(False)
        toolbar.addAction(self._act_set_delay)

        self._act_reset = QAction("원본 복원", self)
        self._act_reset.setToolTip("raw_events 기준으로 events를 초기화합니다.")
        self._act_reset.triggered.connect(self._reset_to_raw)
        self._act_reset.setEnabled(False)
        toolbar.addAction(self._act_reset)

        layout.addWidget(toolbar)

        # 이벤트 테이블
        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(_COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._table.setAlternatingRowColors(True)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)

        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self._table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._context_menu)
        self._table.cellDoubleClicked.connect(self._on_double_click)

        layout.addWidget(self._table)

        # 하단 요약
        self._summary = QLabel("이벤트 없음")
        self._summary.setContentsMargins(8, 4, 8, 4)
        font = QFont()
        font.setPointSize(8)
        self._summary.setFont(font)
        layout.addWidget(self._summary)

    # ── 공개 인터페이스 ───────────────────────────────────────────────────────

    def load_macro(self, macro: MacroData) -> None:
        """MacroData를 테이블에 로드한다."""
        self._macro = macro
        self._refresh_table()
        self._act_del_moves.setEnabled(True)
        self._act_set_delay.setEnabled(True)
        self._act_reset.setEnabled(True)

    def current_macro(self) -> MacroData | None:
        """현재 로드된 MacroData를 반환한다."""
        return self._macro

    # ── 테이블 갱신 ───────────────────────────────────────────────────────────

    def _refresh_table(self) -> None:
        if self._macro is None:
            self._table.setRowCount(0)
            self._summary.setText("이벤트 없음")
            return

        events = self._macro.events
        self._table.setRowCount(len(events))

        for row, event in enumerate(events):
            x_s, y_s, key_btn = _event_detail(event)
            ts_ms = f"{event.timestamp_ns / 1_000_000:.0f}"
            delay_s = str(event.delay_override_ms) if event.delay_override_ms is not None else ""

            items = [
                _cell(str(row + 1)),
                _cell(event.type),
                _cell(ts_ms),
                _cell(x_s),
                _cell(y_s),
                _cell(key_btn),
                _cell(delay_s, editable=True),
            ]

            # 타입 셀 색상
            color = _TYPE_COLORS.get(event.type, QColor(80, 80, 80))
            items[1].setBackground(QBrush(color))
            items[1].setForeground(QBrush(QColor(255, 255, 255)))

            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, item)

        total = len(events)
        raw_total = len(self._macro.raw_events)
        edited_tag = " [편집됨]" if self._macro.is_edited else ""
        mouse_moves = sum(1 for e in events if e.type == "mouse_move")
        self._summary.setText(
            f"총 {total}개 이벤트 (raw: {raw_total})  |  "
            f"마우스 이동: {mouse_moves}개{edited_tag}"
        )

    # ── 컨텍스트 메뉴 / 더블클릭 ─────────────────────────────────────────────

    def _context_menu(self, pos: object) -> None:
        from PyQt6.QtCore import QPoint
        rows = self._selected_rows()
        if not rows or self._macro is None:
            return

        menu = QMenu(self)

        if len(rows) == 1:
            act_edit_delay = menu.addAction("딜레이 설정...")
            act_edit_delay.triggered.connect(lambda: self._edit_delay_row(rows[0]))

        act_delete = menu.addAction(f"이벤트 삭제 ({len(rows)}개)")
        act_delete.triggered.connect(lambda: self._delete_rows(rows))

        global_pos = self._table.viewport().mapToGlobal(
            pos if isinstance(pos, QPoint) else QPoint(0, 0)
        )
        menu.exec(global_pos)

    def _on_double_click(self, row: int, col: int) -> None:
        if col == 6:  # 딜레이 셀 더블클릭
            self._edit_delay_row(row)

    # ── 편집 동작 ─────────────────────────────────────────────────────────────

    def _selected_rows(self) -> list[int]:
        return sorted({idx.row() for idx in self._table.selectedIndexes()})

    def _edit_delay_row(self, row: int) -> None:
        if self._macro is None or row >= len(self._macro.events):
            return
        event = self._macro.events[row]
        current = event.delay_override_ms if event.delay_override_ms is not None else 0

        val, ok = QInputDialog.getInt(
            self, "딜레이 설정",
            f"이벤트 #{row + 1} ({event.type}) 딜레이 (ms):\n0 입력 시 원래 타이밍으로 복원",
            current, 0, 60000, 10,
        )
        if not ok:
            return

        from macroflow.macro_file import set_delay_single
        try:
            new_macro = set_delay_single(
                self._macro, event.id, val if val > 0 else None
            )
        except KeyError:
            QMessageBox.warning(self, "오류", "이벤트를 찾을 수 없습니다.")
            return

        self._macro = new_macro
        self._refresh_table()
        self.macro_changed.emit(self._macro)

    def _delete_rows(self, rows: list[int]) -> None:
        if self._macro is None:
            return
        events = list(self._macro.events)
        for row in sorted(rows, reverse=True):
            if 0 <= row < len(events):
                events.pop(row)
        from macroflow.types import MacroData
        self._macro = MacroData(
            meta=self._macro.meta,
            settings=self._macro.settings,
            raw_events=self._macro.raw_events,
            events=events,
            is_edited=True,
        )
        self._refresh_table()
        self.macro_changed.emit(self._macro)

    def _delete_mouse_moves(self) -> None:
        if self._macro is None:
            return
        self._macro = delete_mouse_moves(self._macro)
        self._refresh_table()
        self.macro_changed.emit(self._macro)
        logger.info("Mouse moves deleted")

    def _set_delay_all(self) -> None:
        if self._macro is None:
            return
        val, ok = QInputDialog.getInt(
            self, "딜레이 일괄 설정",
            "모든 이벤트에 적용할 딜레이 (ms):\n0 입력 시 원래 타이밍으로 복원",
            100, 0, 60000, 10,
        )
        if not ok:
            return
        self._macro = set_delay_all(self._macro, val)
        self._refresh_table()
        self.macro_changed.emit(self._macro)
        logger.info(f"All delays set to {val}ms")

    def _reset_to_raw(self) -> None:
        if self._macro is None:
            return
        reply = QMessageBox.question(
            self, "원본 복원",
            "편집 내용을 모두 취소하고 원본(raw)으로 복원할까요?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._macro = reset_to_raw(self._macro)
        self._refresh_table()
        self.macro_changed.emit(self._macro)
        logger.info("Macro reset to raw")
