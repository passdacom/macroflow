"""MacroFlow 이벤트 에디터 위젯.

그룹 표시: mouse_down+up → 클릭, key_down+up → 키 입력.
Undo/Redo, 마우스 이동 숨김 토글, 더블클릭 편집 지원.
"""

from __future__ import annotations

import dataclasses
import logging
import secrets
from collections import deque
from collections.abc import Callable
from typing import Literal

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from macroflow.macro_file import (
    delete_mouse_moves,
    edit_key_value,
    edit_position,
    edit_wheel_delta,
    reset_to_raw,
    set_color_check_on_mismatch,
    set_delay_all,
    set_delay_single,
    toggle_color_check,
)
from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    KeyEvent,
    MacroData,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    TextInputEvent,
)
from macroflow.ui import editor_table as _editor_table
from macroflow.ui.editor_history import copy_events, macro_with_events
from macroflow.ui.editor_keys import key_name_to_vk
from macroflow.ui.editor_rows import (
    COLOR_CHECK_CLICK_KINDS,
    KIND_CLICK,
    KIND_COLOR_CHECK_CLICK,
    KIND_COLOR_CHECK_CLICK_STOP,
    KIND_COLOR_CHECK_CLICK_WAIT,
    KIND_COLOR_CHECK_RIGHT_CLICK,
    KIND_COLOR_CHECK_RIGHT_CLICK_STOP,
    KIND_COLOR_CHECK_RIGHT_CLICK_WAIT,
    KIND_COLOR_TRIGGER,
    KIND_CONDITION,
    KIND_DRAG,
    KIND_KEY_PRESS,
    KIND_LOOP,
    KIND_MOUSE_MOVE,
    KIND_MOUSE_WHEEL,
    KIND_ORPHAN,
    KIND_RIGHT_CLICK,
    KIND_RIGHT_DRAG,
    KIND_TEXT_INPUT,
    KIND_WAIT,
    KIND_WINDOW_TRIGGER,
    POSITION_EDIT_KINDS,
    _build_rows,
    _DisplayRow,
)
from macroflow.ui.editor_table import (
    COL_CONTENT,
    COL_DELAY,
    COL_INDEX,
    COL_REMARK,
    COL_SOURCE,
    COL_TIME,
    COL_TYPE,
    COLUMNS,
    CONTENT_COLUMN_MIN_WIDTH,
    _color_detail_widget,
    _is_hex_color,
    _table_row_items,
)

logger = logging.getLogger(__name__)

_MAX_UNDO = 50

# ── 행 종류별 색상 ──────────────────────────────────────────────────────────────

_KIND_COLORS: dict[str, QColor] = {
    KIND_CLICK:                 QColor(60, 110, 200),
    KIND_RIGHT_CLICK:           QColor(80, 60, 180),
    KIND_DRAG:                  QColor(40, 80, 160),
    KIND_RIGHT_DRAG:            QColor(60, 40, 140),
    KIND_COLOR_CHECK_CLICK:           QColor(200, 100, 30),   # 주황 — 색 체크 스킵 모드
    KIND_COLOR_CHECK_RIGHT_CLICK:     QColor(180, 70,  20),   # 진한 주황 — 우클릭 스킵 모드
    KIND_COLOR_CHECK_CLICK_STOP:      QColor(210,  45,  45),   # 빨강 — 색 체크 중지 모드
    KIND_COLOR_CHECK_RIGHT_CLICK_STOP: QColor(180, 30,  30),  # 진한 빨강 — 우클릭 중지 모드
    # wait 색상 (파란 계열)
    KIND_COLOR_CHECK_CLICK_WAIT:       QColor(40,  120, 210),  # 파랑 — 색 체크 대기 모드
    KIND_COLOR_CHECK_RIGHT_CLICK_WAIT: QColor(30,   90, 180),  # 진한 파랑
    # 텍스트 입력
    KIND_TEXT_INPUT:                   QColor(0,   170, 130),  # 녹청(teal)
    KIND_KEY_PRESS:             QColor(60, 145, 85),
    KIND_MOUSE_MOVE:            QColor(90, 90, 90),
    KIND_MOUSE_WHEEL:           QColor(20, 150, 155),   # 청록색 — 휠 스크롤
    KIND_WAIT:                  QColor(190, 120, 50),
    KIND_COLOR_TRIGGER:         QColor(140, 80, 170),
    KIND_WINDOW_TRIGGER:        QColor(140, 80, 170),
    KIND_CONDITION:             QColor(170, 140, 40),
    KIND_LOOP:                  QColor(170, 140, 40),
    KIND_ORPHAN:                QColor(160, 60, 60),
}

_COLUMNS = COLUMNS
CONTENT_COLUMN_REFERENCE_TEXT = _editor_table.CONTENT_COLUMN_REFERENCE_TEXT


class EventEditorWidget(QWidget):
    """이벤트 목록을 그룹 표시·편집하는 위젯.

    그룹 표시 규칙:
      - mouse_down + (moves) + mouse_up → 클릭/드래그 한 행
      - key_down + key_up (같은 vk_code) → 키 입력 한 행
      - mouse_move는 기본 숨김 (토글 버튼으로 표시 가능)

    편집 기능:
      - 더블클릭: 키 값·위치·딜레이 변경
      - 컨텍스트 메뉴: 딜레이·키·위치·삭제
      - Undo/Redo (Ctrl+Z / Ctrl+Y)
      - Delete 키: 선택 행 삭제
    """

    macro_changed = pyqtSignal(object)      # MacroData
    f6_capture_started = pyqtSignal()      # F6 캡처 대기 시작 (힌트 오버레이용)
    f6_capture_ended = pyqtSignal()        # F6 캡처 완료 또는 취소
    play_event_range = pyqtSignal(int, int)  # (start_idx, end_exclusive) 단일 이벤트 실행 요청

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._macro: MacroData | None = None
        self._rows: list[_DisplayRow] = []
        self._show_moves: bool = False
        self._undo_stack: deque[list[AnyEvent]] = deque(maxlen=_MAX_UNDO)
        self._redo_stack: list[list[AnyEvent]] = []
        # F6 캡처 콜백: (x_ratio, y_ratio, color_hex) 형태.
        # 위치 편집은 color 무시, 색 트리거 삽입은 모두 활용.
        self._f6_capture_cb: Callable[[float, float, str], None] | None = None
        # 재생 하이라이트: 마지막으로 하이라이트된 행 인덱스 (-1 = 없음).
        self._last_highlight_row: int = -1
        self._relative_time: bool = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 편집 도구바
        toolbar = QToolBar("편집 도구", self)
        toolbar.setMovable(False)

        self._act_toggle_moves = QAction("이동 표시", self)
        self._act_toggle_moves.setToolTip("마우스 이동 이벤트 표시/숨김 (비파괴)")
        self._act_toggle_moves.setCheckable(True)
        self._act_toggle_moves.setChecked(False)
        self._act_toggle_moves.triggered.connect(self._toggle_moves)
        self._act_toggle_moves.setEnabled(False)
        toolbar.addAction(self._act_toggle_moves)

        self._act_del_moves = QAction("이동 삭제", self)
        self._act_del_moves.setToolTip("mouse_move 이벤트를 events에서 영구 삭제합니다")
        self._act_del_moves.triggered.connect(self._delete_mouse_moves)
        self._act_del_moves.setEnabled(False)
        toolbar.addAction(self._act_del_moves)

        toolbar.addSeparator()

        self._act_set_delay = QAction("딜레이 일괄", self)
        self._act_set_delay.setToolTip("모든 이벤트의 딜레이를 동일한 값으로 설정합니다")
        self._act_set_delay.triggered.connect(self._set_delay_all)
        self._act_set_delay.setEnabled(False)
        toolbar.addAction(self._act_set_delay)

        toolbar.addSeparator()

        self._act_undo = QAction("↩ 취소", self)
        self._act_undo.setToolTip("실행 취소 (Ctrl+Z)")
        self._act_undo.triggered.connect(self._undo)
        self._act_undo.setEnabled(False)
        toolbar.addAction(self._act_undo)

        self._act_redo = QAction("↪ 재실행", self)
        self._act_redo.setToolTip("다시 실행 (Ctrl+Y)")
        self._act_redo.triggered.connect(self._redo)
        self._act_redo.setEnabled(False)
        toolbar.addAction(self._act_redo)

        toolbar.addSeparator()

        self._act_insert_color = QAction("🎨 색 체크 삽입", self)
        self._act_insert_color.setToolTip(
            "선택 행 다음에 ColorTriggerEvent를 삽입합니다\n"
            "클릭 후 원하는 위치로 마우스를 이동하고 F6을 누르세요"
        )
        self._act_insert_color.triggered.connect(self._start_color_trigger_insert)
        self._act_insert_color.setEnabled(False)
        toolbar.addAction(self._act_insert_color)

        toolbar.addSeparator()

        self._act_reset = QAction("원본 복원", self)
        self._act_reset.setToolTip("raw_events 기준으로 events를 초기화합니다")
        self._act_reset.triggered.connect(self._reset_to_raw)
        self._act_reset.setEnabled(False)
        toolbar.addAction(self._act_reset)

        toolbar.addSeparator()

        self._chk_relative_time = QCheckBox("⏱ 상대 시간")
        self._chk_relative_time.setToolTip(
            "체크: 시간(ms) 열을 이전 이벤트 대비 delta로 표시\n"
            "해제: 녹화 시작 기준 절대 시간 표시"
        )
        self._chk_relative_time.setChecked(False)
        self._chk_relative_time.toggled.connect(self._on_relative_time_toggled)
        toolbar.addWidget(self._chk_relative_time)

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
        hdr.setSectionResizeMode(COL_INDEX, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(COL_TYPE, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(COL_CONTENT, QHeaderView.ResizeMode.Interactive)
        hdr.setSectionResizeMode(COL_REMARK, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(COL_TIME, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(COL_DELAY, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(COL_SOURCE, QHeaderView.ResizeMode.ResizeToContents)

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

        # 단축키
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self._undo)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self._redo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self).activated.connect(self._redo)
        QShortcut(QKeySequence("Delete"), self).activated.connect(self._delete_selected)

    # ── 공개 인터페이스 ───────────────────────────────────────────────────────

    def load_macro(self, macro: MacroData) -> None:
        """MacroData를 테이블에 로드한다."""
        self._macro = macro
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._last_highlight_row = -1
        self._refresh()
        self._act_toggle_moves.setEnabled(True)
        self._act_del_moves.setEnabled(True)
        self._act_set_delay.setEnabled(True)
        self._act_insert_color.setEnabled(True)
        self._act_reset.setEnabled(True)
        self._act_undo.setEnabled(False)
        self._act_redo.setEnabled(False)

    def current_macro(self) -> MacroData | None:
        """현재 로드된 MacroData를 반환한다."""
        return self._macro

    def highlight_event(self, event_idx: int) -> None:
        """재생 중 해당 이벤트 인덱스에 대응하는 행을 하이라이트한다.

        - 같은 행이면 재갱신하지 않아 불필요한 깜빡임을 방지한다.
        - 해당 이벤트가 숨겨진 행(mouse_move 숨김 등)이면 이전 하이라이트를 유지한다.
        - 배경색 기반으로 표시하므로 테이블 포커스 해제 후에도 위치가 보인다.
        """
        for row_idx, row in enumerate(self._rows):
            if event_idx in row.event_indices:
                if row_idx != self._last_highlight_row:
                    if 0 <= self._last_highlight_row < self._table.rowCount():
                        self._repaint_row_default(self._last_highlight_row)
                    self._last_highlight_row = row_idx
                    self._repaint_row_highlight(row_idx)
                    self._table.scrollTo(
                        self._table.model().index(row_idx, 0),
                        QAbstractItemView.ScrollHint.PositionAtCenter,
                    )
                return
        # 이벤트에 대응하는 표시 행 없음(숨긴 mouse_move 등) → 이전 하이라이트 유지

    # ── 재생 하이라이트 헬퍼 ─────────────────────────────────────────────────

    _HIGHLIGHT_COLOR = QColor(255, 200, 0, 200)  # 황금색 — 포커스 해제에도 잘 보임

    def _repaint_row_highlight(self, row_idx: int) -> None:
        """지정 행 전체를 재생 하이라이트 색으로 덮어쓴다."""
        for col in range(self._table.columnCount()):
            item = self._table.item(row_idx, col)
            if item is not None:
                item.setBackground(QBrush(self._HIGHLIGHT_COLOR))

    def _repaint_row_default(self, row_idx: int) -> None:
        """지정 행을 원래 kind 색으로 복원한다."""
        if row_idx >= len(self._rows):
            return
        row = self._rows[row_idx]
        kind_color = _KIND_COLORS.get(row.kind, QColor(80, 80, 80))
        for col in range(self._table.columnCount()):
            item = self._table.item(row_idx, col)
            if item is None:
                continue
            if col == COL_TYPE:  # 타입 열은 kind 색 유지
                item.setBackground(QBrush(kind_color))
            else:
                item.setData(Qt.ItemDataRole.BackgroundRole, None)  # 기본(교대색) 복원

    # ── F6 캡처 인터페이스 (main_window에서 호출) ─────────────────────────────

    def is_f6_capture_active(self) -> bool:
        """F6 캡처 대기 중이면 True를 반환한다."""
        return self._f6_capture_cb is not None

    def consume_f6_capture(self, x_ratio: float, y_ratio: float, color_hex: str) -> bool:
        """F6이 눌렸을 때 캡처 콜백을 실행한다.

        캡처 대기 중이 아니면 False를 반환한다. 콜백 실행 후 대기 상태를 해제한다.
        """
        if self._f6_capture_cb is None:
            return False
        cb = self._f6_capture_cb
        self._f6_capture_cb = None
        cb(x_ratio, y_ratio, color_hex)
        self.f6_capture_ended.emit()
        return True

    def cancel_f6_capture(self) -> None:
        """F6 캡처 대기 상태를 취소한다."""
        if self._f6_capture_cb is not None:
            self._f6_capture_cb = None
            self.f6_capture_ended.emit()

    def _on_relative_time_toggled(self, checked: bool) -> None:
        """상대 시간 체크박스 토글 — 테이블을 다시 렌더링한다."""
        self._relative_time = checked
        self._refresh()

    def get_event_range_for_rows(
        self, start_row: int, end_row: int,
    ) -> tuple[int, int] | None:
        """표시 행 범위를 원본 events 인덱스 범위(start, end exclusive)로 변환한다.

        Args:
            start_row: 시작 표시 행 번호 (1-based, 사용자 기준).
            end_row: 끝 표시 행 번호 (1-based, inclusive).

        Returns:
            (start_event_idx, end_event_idx_exclusive) 또는 범위가 유효하지 않으면 None.
        """
        if not self._rows:
            return None
        # 1-based → 0-based
        s = max(0, start_row - 1)
        e = min(len(self._rows), end_row)
        if s >= e:
            return None
        selected_rows = self._rows[s:e]
        all_indices: list[int] = []
        for row in selected_rows:
            all_indices.extend(row.event_indices)
        if not all_indices:
            return None
        return (min(all_indices), max(all_indices) + 1)

    def row_count(self) -> int:
        """현재 표시 행 수를 반환한다."""
        return len(self._rows)

    # ── 테이블 갱신 ───────────────────────────────────────────────────────────

    def _refresh(self) -> None:
        if self._macro is None:
            self._table.setRowCount(0)
            self._rows = []
            self._summary.setText("이벤트 없음")
            return

        events = self._macro.events
        for row_idx in range(self._table.rowCount()):
            self._table.removeCellWidget(row_idx, COL_CONTENT)
        self._rows = _build_rows(events, self._show_moves)
        # 출처 열: primary 이벤트의 source_file을 각 행에 반영
        for row in self._rows:
            row.source_file = events[row.primary_idx].source_file
        self._last_highlight_row = -1  # 갱신 시 하이라이트 초기화
        self._table.setRowCount(len(self._rows))

        for row_idx, row in enumerate(self._rows):
            color = _KIND_COLORS.get(row.kind, QColor(80, 80, 80))
            items = _table_row_items(
                row,
                row_number=row_idx + 1,
                relative_time=self._relative_time,
                kind_color=color,
            )

            for col, item in enumerate(items):
                self._table.setItem(row_idx, col, item)

            if _is_hex_color(row.color_hex):
                self._table.setCellWidget(row_idx, COL_CONTENT, _color_detail_widget(row.detail, row.color_hex))

        self._fit_content_column()

        total = len(events)
        raw_total = len(self._macro.raw_events)
        move_count = sum(1 for e in events if e.type == "mouse_move")
        display_count = len(self._rows)
        edited_tag = " [편집됨]" if self._macro.is_edited else ""
        self._summary.setText(
            f"표시: {display_count}개  (원본: {total}개, raw: {raw_total}개)"
            f"  |  이동: {move_count}개{edited_tag}"
        )

    def _fit_content_column(self) -> None:
        """내용 열을 대표 색상 행 정도로 줄이되, 더 긴 내용은 자동으로 맞춘다."""
        self._table.resizeColumnToContents(COL_CONTENT)
        if self._table.columnWidth(COL_CONTENT) < CONTENT_COLUMN_MIN_WIDTH:
            self._table.setColumnWidth(COL_CONTENT, CONTENT_COLUMN_MIN_WIDTH)

    # ── Undo / Redo ───────────────────────────────────────────────────────────

    def _push_undo(self) -> None:
        if self._macro is None:
            return
        self._undo_stack.append(copy_events(self._macro.events))
        self._redo_stack.clear()
        self._act_undo.setEnabled(True)
        self._act_redo.setEnabled(False)

    def _apply_events(self, events: list[AnyEvent]) -> None:
        assert self._macro is not None
        self._macro = macro_with_events(self._macro, events)
        self._refresh()
        self.macro_changed.emit(self._macro)

    def _undo(self) -> None:
        if not self._undo_stack or self._macro is None:
            return
        self._redo_stack.append(copy_events(self._macro.events))
        events = self._undo_stack.pop()
        self._act_undo.setEnabled(bool(self._undo_stack))
        self._act_redo.setEnabled(True)
        self._apply_events(events)

    def _redo(self) -> None:
        if not self._redo_stack or self._macro is None:
            return
        self._undo_stack.append(copy_events(self._macro.events))
        events = self._redo_stack.pop()
        self._act_undo.setEnabled(True)
        self._act_redo.setEnabled(bool(self._redo_stack))
        self._apply_events(events)

    # ── 컨텍스트 메뉴 / 더블클릭 ─────────────────────────────────────────────

    def _context_menu(self, pos: object) -> None:
        rows = self._selected_row_indices()
        if not rows or self._macro is None:
            return

        menu = QMenu(self)

        if len(rows) == 1:
            row = self._rows[rows[0]]
            primary = self._macro.events[row.primary_idx]

            # ▶ 이 이벤트만 실행
            act_play_single = menu.addAction("▶ 이 이벤트만 실행")
            act_play_single.triggered.connect(lambda: self._play_single_event(rows[0]))
            menu.addSeparator()

            act_edit_delay = menu.addAction("딜레이 설정(&D)...")
            act_edit_delay.triggered.connect(lambda: self._edit_delay(rows[0]))

            if row.kind == KIND_KEY_PRESS and isinstance(primary, KeyEvent):
                act_edit_key = menu.addAction("키 값 변경(&K)...")
                assert act_edit_key is not None
                act_edit_key.triggered.connect(lambda: self._edit_key(rows[0]))

            if row.kind in POSITION_EDIT_KINDS:
                act_edit_pos = menu.addAction("위치 변경(&P)...")
                assert act_edit_pos is not None
                act_edit_pos.triggered.connect(lambda: self._edit_position(rows[0]))

            # 색 체크 토글 — recorded_color가 있는 클릭/드래그에서만 표시
            if row.kind in COLOR_CHECK_CLICK_KINDS and isinstance(primary, MouseButtonEvent) and primary.recorded_color is not None:
                is_checked = primary.color_check_enabled
                check_text = "🎨 색 체크 끄기(&C)" if is_checked else "🎨 색 체크 켜기(&C)"
                act_color = menu.addAction(check_text)
                assert act_color is not None
                act_color.triggered.connect(lambda: self._toggle_color_check(rows[0]))

                # 불일치 동작 선택 (색 체크 활성화된 경우만) — 원하는 모드를 한 번에 선택
                if is_checked:
                    mode_menu = menu.addMenu("불일치 시 동작(&M)")
                    assert mode_menu is not None
                    current_mode = primary.color_check_on_mismatch
                    mode_labels: tuple[tuple[Literal["skip", "stop", "wait"], str], ...] = (
                        ("skip", "▶ 스킵(&S)"),
                        ("stop", "⏹ 중지(&T)"),
                        ("wait", "⏳ 대기(&W)"),
                    )
                    for mode, label in mode_labels:
                        act_mode = mode_menu.addAction(label)
                        assert act_mode is not None
                        act_mode.setCheckable(True)
                        act_mode.setChecked(mode == current_mode)
                        act_mode.triggered.connect(
                            lambda _checked=False, mode=mode: self._set_color_check_mode(rows[0], mode)
                        )

            if row.kind == KIND_MOUSE_WHEEL:
                act_edit_wheel = menu.addAction("스크롤 편집(&W)...")
                assert act_edit_wheel is not None
                act_edit_wheel.triggered.connect(lambda: self._edit_wheel(rows[0]))

            if row.kind == KIND_TEXT_INPUT and isinstance(primary, TextInputEvent):
                act_edit_text = menu.addAction("💬 텍스트 편집(&E)...")
                assert act_edit_text is not None
                act_edit_text.triggered.connect(lambda: self._edit_text_input(rows[0]))

            act_text_insert = menu.addAction("💬 텍스트 입력 추가(&T)...")
            assert act_text_insert is not None
            act_text_insert.triggered.connect(lambda: self._insert_text_input(rows[0]))

            act_click_insert = menu.addAction("🖱 클릭 추가(&L)...")
            assert act_click_insert is not None
            act_click_insert.triggered.connect(lambda: self._insert_click(rows[0]))

            act_remark = menu.addAction("📝 비고 편집(&N)...")
            assert act_remark is not None
            act_remark.triggered.connect(lambda: self._edit_remark(rows[0]))

            menu.addSeparator()

        act_delete = menu.addAction(f"행 삭제(&X) ({len(rows)}개)")
        act_delete.triggered.connect(lambda: self._delete_rows(rows))

        if isinstance(pos, QPoint):
            global_pos = self._table.viewport().mapToGlobal(pos)
        else:
            global_pos = self._table.viewport().mapToGlobal(QPoint(0, 0))
        menu.exec(global_pos)

    def _on_double_click(self, row: int, col: int) -> None:
        if row >= len(self._rows) or self._macro is None:
            return
        display_row = self._rows[row]
        if col == COL_DELAY:  # 딜레이 셀
            self._edit_delay(row)
        elif col in (COL_TYPE, COL_REMARK):  # 타입/비고 셀 → 비고 편집
            self._edit_remark(row)
        elif col == COL_CONTENT:  # 내용 셀
            primary = self._macro.events[display_row.primary_idx]
            if display_row.kind == KIND_KEY_PRESS and isinstance(primary, KeyEvent):
                self._edit_key(row)
            elif display_row.kind in POSITION_EDIT_KINDS:
                self._edit_position(row)
            elif display_row.kind == KIND_MOUSE_WHEEL:
                self._edit_wheel(row)
            elif display_row.kind == KIND_TEXT_INPUT:
                self._edit_text_input(row)
            else:
                self._edit_remark(row)  # 나머지 타입(wait, color_trigger 등)

    # ── 편집 동작 ─────────────────────────────────────────────────────────────

    def _selected_row_indices(self) -> list[int]:
        return sorted({idx.row() for idx in self._table.selectedIndexes()})

    def _edit_delay(self, row: int) -> None:
        if self._macro is None or row >= len(self._rows):
            return
        display_row = self._rows[row]
        primary = self._macro.events[display_row.primary_idx]
        current = primary.delay_override_ms if primary.delay_override_ms is not None else 0

        val, ok = QInputDialog.getInt(
            self, "딜레이 설정",
            f"행 #{row + 1} 딜레이 (ms):\n"
            "0 입력 시 원래 타이밍으로 복원.\n"
            "음수(-) 입력 시 직전 이벤트보다 빨리 실행 (즉시 실행 방향).",
            current, -60000, 60000, 10,
        )
        if not ok:
            return
        self._push_undo()
        try:
            new_macro = set_delay_single(self._macro, primary.id, val if val != 0 else None)
        except KeyError:
            self._undo_stack.pop()
            QMessageBox.warning(self, "오류", "이벤트를 찾을 수 없습니다.")
            return
        self._macro = new_macro
        self._refresh()
        self.macro_changed.emit(self._macro)

    def _edit_key(self, row: int) -> None:
        """키 입력 행의 키 값을 변경한다."""
        if self._macro is None or row >= len(self._rows):
            return
        display_row = self._rows[row]
        primary = self._macro.events[display_row.primary_idx]
        if not isinstance(primary, KeyEvent):
            return

        new_key, ok = QInputDialog.getText(
            self, "키 값 변경",
            f"현재 키: {primary.key}\n"
            "새 키 이름을 입력하세요 (예: a, 1, enter, space, ctrl, f1):",
            text=primary.key,
        )
        if not ok or not new_key.strip():
            return

        new_key = new_key.strip().lower()
        new_vk = key_name_to_vk(new_key, primary.vk_code)

        self._push_undo()
        try:
            new_macro = edit_key_value(self._macro, primary.id, new_key, new_vk)
        except (KeyError, TypeError):
            self._undo_stack.pop()
            QMessageBox.warning(self, "오류", "키 값 변경에 실패했습니다.")
            return
        self._macro = new_macro
        self._refresh()
        self.macro_changed.emit(self._macro)

        # key_up 이벤트도 동일하게 업데이트
        if len(display_row.event_indices) == 2:
            up_event = self._macro.events[display_row.event_indices[1]]
            if isinstance(up_event, KeyEvent):
                try:
                    updated = edit_key_value(self._macro, up_event.id, new_key, new_vk)
                    self._macro = updated
                    self._refresh()
                    self.macro_changed.emit(self._macro)
                except (KeyError, TypeError):
                    pass

    def _edit_position(self, row: int) -> None:
        """마우스 이벤트의 위치를 변경한다.

        SpinBox 직접 입력 또는 'F6으로 직접 지정' (F6 캡처 모드) 중 선택.
        클릭/드래그 행은 mouse_down과 mouse_up 좌표를 동시에 업데이트한다.
        """
        if self._macro is None or row >= len(self._rows):
            return
        display_row = self._rows[row]
        primary = self._macro.events[display_row.primary_idx]
        if not isinstance(primary, (MouseButtonEvent, MouseMoveEvent)):
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("위치 변경")
        dialog.setFixedWidth(320)

        form = QFormLayout()
        x_spin = QDoubleSpinBox()
        x_spin.setRange(-500.0, 500.0)
        x_spin.setDecimals(2)
        x_spin.setSuffix(" %")
        x_spin.setToolTip("기본 모니터 너비 기준 비율. 보조 모니터는 100% 초과 가능.")
        x_spin.setValue(primary.x_ratio * 100)
        form.addRow("X 위치:", x_spin)

        y_spin = QDoubleSpinBox()
        y_spin.setRange(-500.0, 500.0)
        y_spin.setDecimals(2)
        y_spin.setSuffix(" %")
        y_spin.setToolTip("기본 모니터 높이 기준 비율. 보조 모니터는 100% 초과 가능.")
        y_spin.setValue(primary.y_ratio * 100)
        form.addRow("Y 위치:", y_spin)

        capture_label = QLabel("")
        capture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        capture_label.setStyleSheet("color: #c07000; font-weight: bold;")

        btn_capture = QPushButton("📍 화면에서 직접 지정 (F6으로 지정)")
        btn_capture.setToolTip(
            "버튼 클릭 후 원하는 위치로 마우스를 이동하고 F6을 누르세요."
        )

        captured_color: list[str] = []

        def _on_f6_captured(x_r: float, y_r: float, color: str) -> None:
            """F6 캡처 콜백 — 다이얼로그 복원 및 SpinBox 갱신."""
            captured_color.clear()
            captured_color.append(color)
            x_spin.setValue(x_r * 100)
            y_spin.setValue(y_r * 100)
            capture_label.setText(f"✅ 캡처됨: ({x_r * 100:.1f}%, {y_r * 100:.1f}%)")
            dialog.showNormal()
            dialog.raise_()
            btn_capture.setEnabled(True)

        def _start_capture() -> None:
            btn_capture.setEnabled(False)
            capture_label.setText("⏳ F6을 눌러 위치를 지정하세요...")
            self._f6_capture_cb = _on_f6_captured
            self.f6_capture_started.emit()  # → main_window에서 힌트 오버레이 표시
            dialog.showMinimized()

        def _on_dialog_finished(_result: int) -> None:
            # 다이얼로그가 닫힐 때 캡처 대기 상태 해제
            self.cancel_f6_capture()

        btn_capture.clicked.connect(_start_capture)
        dialog.finished.connect(_on_dialog_finished)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        v = QVBoxLayout(dialog)
        v.addLayout(form)
        v.addWidget(btn_capture)
        v.addWidget(capture_label)
        v.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_x = x_spin.value() / 100.0
        new_y = y_spin.value() / 100.0

        self._push_undo()
        try:
            new_macro = edit_position(self._macro, primary.id, new_x, new_y)
        except (KeyError, TypeError):
            self._undo_stack.pop()
            QMessageBox.warning(self, "오류", "위치 변경에 실패했습니다.")
            return

        # 그룹 내 나머지 마우스 이벤트(move + up)도 모두 같은 위치로 업데이트.
        # 이를 누락하면 재생 시 중간 move 이벤트가 old 위치로 마우스를 이동시킨다.
        for idx in display_row.event_indices:
            if idx == display_row.primary_idx:
                continue  # primary는 이미 위에서 업데이트
            ev = new_macro.events[idx]
            if isinstance(ev, (MouseButtonEvent, MouseMoveEvent)):
                try:
                    new_macro = edit_position(new_macro, ev.id, new_x, new_y)
                except (KeyError, TypeError):
                    pass

        # F6 캡처로 위치를 지정한 경우 primary 이벤트의 recorded_color도 업데이트.
        if captured_color and isinstance(primary, MouseButtonEvent):
            new_events = list(new_macro.events)
            for i, ev in enumerate(new_events):
                if ev.id == primary.id and isinstance(ev, MouseButtonEvent):
                    new_events[i] = dataclasses.replace(ev, recorded_color=captured_color[0])
                    break
            new_macro = dataclasses.replace(new_macro, events=new_events, is_edited=True)

        self._macro = new_macro
        self._refresh()
        self.macro_changed.emit(self._macro)

    def _edit_wheel(self, row: int) -> None:
        """휠 이벤트(그룹)의 스크롤 양과 방향을 변경한다.

        그룹 전체를 단일 이벤트로 병합 후 delta를 적용한다.
        이렇게 하면 노치 수를 자유롭게 조정할 수 있다.
        """
        if self._macro is None or row >= len(self._rows):
            return
        display_row = self._rows[row]
        primary = self._macro.events[display_row.primary_idx]
        if not isinstance(primary, MouseWheelEvent):
            return

        # 그룹의 현재 총 delta 계산
        total_delta = sum(
            self._macro.events[idx].delta  # type: ignore[union-attr]
            for idx in display_row.event_indices
            if isinstance(self._macro.events[idx], MouseWheelEvent)
        )
        current_notches = max(1, abs(total_delta) // 120)
        is_positive = total_delta >= 0

        dialog = QDialog(self)
        is_vertical = (primary.axis == "vertical")
        dialog.setWindowTitle(
            f"{'↕ 수직' if is_vertical else '↔ 수평'} 휠 스크롤 편집"
        )
        dialog.setFixedWidth(300)

        layout = QVBoxLayout(dialog)

        # ── 방향 선택 ────────────────────────────────────────────────────────
        dir_group = QGroupBox("방향")
        dir_layout = QHBoxLayout(dir_group)
        if is_vertical:
            btn_pos = QRadioButton("↑ 위 (앞으로)")
            btn_neg = QRadioButton("↓ 아래 (뒤로)")
        else:
            btn_pos = QRadioButton("→ 우 (앞으로)")
            btn_neg = QRadioButton("← 좌 (뒤로)")
        btn_pos.setChecked(is_positive)
        btn_neg.setChecked(not is_positive)
        dir_layout.addWidget(btn_pos)
        dir_layout.addWidget(btn_neg)
        layout.addWidget(dir_group)

        # ── 노치 수 ──────────────────────────────────────────────────────────
        form = QFormLayout()
        notch_spin = QSpinBox()
        notch_spin.setMinimum(1)
        notch_spin.setMaximum(999)
        notch_spin.setValue(current_notches)
        notch_spin.setSuffix("  노치  (1노치 = 120)")
        notch_spin.setFixedWidth(180)
        form.addRow("스크롤 양:", notch_spin)
        layout.addLayout(form)

        # 실시간 delta 미리보기
        preview = QLabel()
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setStyleSheet("color: #888; font-size: 11px;")

        def _update_preview() -> None:
            sign = 1 if btn_pos.isChecked() else -1
            delta_val = sign * notch_spin.value() * 120
            preview.setText(f"Δ = {delta_val:+d}")

        notch_spin.valueChanged.connect(lambda _: _update_preview())
        btn_pos.toggled.connect(lambda _: _update_preview())
        _update_preview()
        layout.addWidget(preview)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        sign = 1 if btn_pos.isChecked() else -1
        new_delta = sign * notch_spin.value() * 120

        self._push_undo()

        # 그룹의 첫 이벤트(primary)를 new_delta로 업데이트
        try:
            new_macro = edit_wheel_delta(self._macro, primary.id, new_delta)
        except (KeyError, TypeError):
            self._undo_stack.pop()
            QMessageBox.warning(self, "오류", "스크롤 편집에 실패했습니다.")
            return

        # 그룹 내 나머지 이벤트(primary 제외)를 삭제 — 단일 이벤트로 병합
        rest_indices = set(display_row.event_indices[1:])
        if rest_indices:
            merged_events = [
                e for idx, e in enumerate(new_macro.events)
                if idx not in rest_indices
            ]
            self._macro = MacroData(
                meta=new_macro.meta,
                settings=new_macro.settings,
                raw_events=new_macro.raw_events,
                events=merged_events,
                is_edited=True,
            )
        else:
            self._macro = new_macro

        self._refresh()
        self.macro_changed.emit(self._macro)

    def _start_color_trigger_insert(self) -> None:
        """선택 행 다음에 ColorTriggerEvent를 F6 캡처로 삽입한다.

        F6을 누르는 순간의 마우스 위치와 픽셀 색을 ColorTriggerEvent로 삽입.
        """
        if self._macro is None:
            return

        rows = self._selected_row_indices()
        # 삽입 기준: 선택 행의 마지막 이벤트 인덱스 다음 위치
        if rows:
            last_row = self._rows[rows[-1]]
            insert_after_event_idx = max(last_row.event_indices)
        else:
            # 선택 없으면 맨 끝에 추가
            insert_after_event_idx = len(self._macro.events) - 1

        # 색 트리거에 부여할 시간 예산 (1초)
        # 직전 이벤트 타임스탬프 + 1초를 색 트리거 타임스탬프로 사용한다.
        # 이후 이벤트들은 동일하게 1초 시프트하여 상대적 타이밍을 보존한다.
        _TRIGGER_BUDGET_NS = 1_000_000_000  # 1초

        def _on_color_captured(x_r: float, y_r: float, color_hex: str) -> None:
            """F6 콜백 — ColorTriggerEvent 삽입.

            타임스탬프: 직전 이벤트 ts + 1초 (perf_counter_ns 절대값 사용 금지).
            이후 이벤트: 모두 1초 시프트하여 상대 타이밍 보존.
            """
            if self._macro is None:
                return

            # 직전 이벤트의 타임스탬프 기준으로 +1초
            evs = self._macro.events
            if 0 <= insert_after_event_idx < len(evs):
                prev_ts_ns = evs[insert_after_event_idx].timestamp_ns
            elif evs:
                prev_ts_ns = evs[-1].timestamp_ns
            else:
                prev_ts_ns = 0

            color_ts_ns = prev_ts_ns + _TRIGGER_BUDGET_NS

            new_event = ColorTriggerEvent(
                id=secrets.token_hex(4),
                type="color_trigger",
                timestamp_ns=color_ts_ns,
                delay_override_ms=None,
                x_ratio=x_r,
                y_ratio=y_r,
                target_color=color_hex,
                tolerance=10,
                timeout_ms=0,
            )
            self._push_undo()
            events = list(self._macro.events)
            events.insert(insert_after_event_idx + 1, new_event)

            # 삽입 지점 이후의 이벤트들을 1초 시프트 → 상대적 타이밍 보존
            # (시프트 없으면 이후 이벤트의 ts < 색 트리거 ts → 삽입 후 즉시 재생)
            for i in range(insert_after_event_idx + 2, len(events)):
                ev = events[i]
                events[i] = dataclasses.replace(ev, timestamp_ns=ev.timestamp_ns + _TRIGGER_BUDGET_NS)

            self._apply_events(events)

        self._f6_capture_cb = _on_color_captured
        self.f6_capture_started.emit()  # → main_window에서 힌트 오버레이 표시

    def _delete_selected(self) -> None:
        rows = self._selected_row_indices()
        if rows:
            self._delete_rows(rows)

    def _delete_rows(self, rows: list[int]) -> None:
        if self._macro is None:
            return
        indices_to_remove: set[int] = set()
        for r in rows:
            if r < len(self._rows):
                indices_to_remove.update(self._rows[r].event_indices)
        self._push_undo()
        events = [e for i, e in enumerate(self._macro.events) if i not in indices_to_remove]
        self._apply_events(events)

    def _toggle_moves(self) -> None:
        self._show_moves = self._act_toggle_moves.isChecked()
        self._refresh()

    def _delete_mouse_moves(self) -> None:
        if self._macro is None:
            return
        self._push_undo()
        self._macro = delete_mouse_moves(self._macro)
        self._refresh()
        self.macro_changed.emit(self._macro)

    def _set_delay_all(self) -> None:
        if self._macro is None:
            return
        val, ok = QInputDialog.getInt(
            self, "딜레이 일괄 설정",
            "모든 이벤트에 적용할 딜레이 (ms):\n"
            "0 입력 시 원래 타이밍으로 복원.\n"
            "음수(-) 입력 시 직전 이벤트보다 빨리 실행.",
            100, -60000, 60000, 10,
        )
        if not ok:
            return
        self._push_undo()
        self._macro = set_delay_all(self._macro, val)
        self._refresh()
        self.macro_changed.emit(self._macro)

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
        self._push_undo()
        self._macro = reset_to_raw(self._macro)
        self._refresh()
        self.macro_changed.emit(self._macro)

    # ── 색 체크 토글 ─────────────────────────────────────────────────────────

    def _toggle_color_check(self, row_idx: int) -> None:
        """지정 행 클릭 이벤트의 색 체크(color_check_enabled)를 토글한다.

        recorded_color가 없는 이벤트에서는 아무 동작도 하지 않는다.
        """
        if self._macro is None or row_idx >= len(self._rows):
            return
        row = self._rows[row_idx]
        primary = self._macro.events[row.primary_idx]
        if not isinstance(primary, MouseButtonEvent) or primary.recorded_color is None:
            return
        self._push_undo()
        try:
            new_macro = toggle_color_check(self._macro, primary.id)
        except (KeyError, TypeError):
            self._undo_stack.pop()
            return
        self._macro = new_macro
        self._refresh()
        self.macro_changed.emit(self._macro)

    def _set_color_check_mode(
        self,
        row_idx: int,
        mode: Literal["skip", "stop", "wait"],
    ) -> None:
        """지정 행 클릭 이벤트의 color_check_on_mismatch를 선택한 모드로 즉시 설정한다."""
        if self._macro is None or row_idx >= len(self._rows):
            return
        row = self._rows[row_idx]
        primary = self._macro.events[row.primary_idx]
        if not isinstance(primary, MouseButtonEvent) or not primary.color_check_enabled:
            return
        self._push_undo()
        try:
            new_macro = set_color_check_on_mismatch(self._macro, primary.id, mode)
        except (KeyError, TypeError):
            self._undo_stack.pop()
            return
        self._macro = new_macro
        self._refresh()
        self.macro_changed.emit(self._macro)

    def _insert_text_input(self, row_idx: int) -> None:
        """선택 행 다음에 TextInputEvent를 삽입한다.

        커스텀 QDialog로 텍스트와 딜레이(ms)를 받아 이벤트 목록에 삽입.
        타임스탬프는 직전 이벤트 + 딜레이. 이후 이벤트도 같은 값만큼 시프트.
        """
        if self._macro is None:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("텍스트 입력 추가")
        dialog.setFixedWidth(360)

        form = QFormLayout()

        text_edit = QLineEdit()
        text_edit.setPlaceholderText("한글·영문·숫자·특수문자·이모지 모두 지원")
        form.addRow("텍스트:", text_edit)

        delay_spin = QSpinBox()
        delay_spin.setRange(0, 30000)
        delay_spin.setValue(1000)
        delay_spin.setSuffix(" ms")
        form.addRow("딜레이:", delay_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)

        v = QVBoxLayout(dialog)
        v.addLayout(form)
        v.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        text = text_edit.text()
        if not text:
            return

        delay_ms = delay_spin.value()
        _BUDGET_NS = max(delay_ms * 1_000_000, 1_000_000)  # 최소 1ms
        delay_override_ms = delay_ms if delay_ms > 0 else None

        rows = self._selected_row_indices()
        if rows:
            last_row = self._rows[rows[-1]]
            insert_after_event_idx = max(last_row.event_indices)
        else:
            insert_after_event_idx = len(self._macro.events) - 1

        evs = self._macro.events
        if 0 <= insert_after_event_idx < len(evs):
            prev_ts_ns = evs[insert_after_event_idx].timestamp_ns
        elif evs:
            prev_ts_ns = evs[-1].timestamp_ns
        else:
            prev_ts_ns = 0

        new_event = TextInputEvent(
            id=secrets.token_hex(4),
            type="text_input",
            timestamp_ns=prev_ts_ns + _BUDGET_NS,
            delay_override_ms=delay_override_ms,
            text=text,
        )
        self._push_undo()
        events = list(self._macro.events)
        events.insert(insert_after_event_idx + 1, new_event)

        # 삽입 지점 이후 이벤트 딜레이만큼 시프트 → 타이밍 보존
        for i in range(insert_after_event_idx + 2, len(events)):
            ev = events[i]
            events[i] = dataclasses.replace(ev, timestamp_ns=ev.timestamp_ns + _BUDGET_NS)

        self._apply_events(events)

    def _insert_click(self, row_idx: int) -> None:
        """선택 행 다음에 MouseButtonEvent (클릭/더블클릭)를 삽입한다.

        다이얼로그: 위치(X/Y%), F6 직접 지정, 버튼 종류, 딜레이.
        좌/우클릭: mouse_down + mouse_up 2개 이벤트.
        더블클릭: down+up+down+up 4개 이벤트, 50ms 간격.
        첫 번째 mouse_down에만 delay_override_ms 적용.
        """
        if self._macro is None:
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("클릭 추가")
        dialog.setFixedWidth(360)

        layout_v = QVBoxLayout(dialog)

        # ── 위치 ────────────────────────────────────────────────────────────
        form = QFormLayout()
        x_spin = QDoubleSpinBox()
        x_spin.setRange(-500.0, 500.0)
        x_spin.setDecimals(2)
        x_spin.setSuffix(" %")
        x_spin.setValue(50.0)
        form.addRow("X 위치:", x_spin)

        y_spin = QDoubleSpinBox()
        y_spin.setRange(-500.0, 500.0)
        y_spin.setDecimals(2)
        y_spin.setSuffix(" %")
        y_spin.setValue(50.0)
        form.addRow("Y 위치:", y_spin)
        layout_v.addLayout(form)

        # ── F6 직접 지정 ────────────────────────────────────────────────────
        capture_label = QLabel("")
        capture_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        capture_label.setStyleSheet("color: #c07000; font-weight: bold;")

        btn_capture = QPushButton("📍 화면에서 직접 지정 (F6으로 지정)")
        btn_capture.setToolTip("버튼 클릭 후 원하는 위치로 마우스를 이동하고 F6을 누르세요.")

        captured_color: list[str] = []

        def _on_f6_captured(x_r: float, y_r: float, color: str) -> None:
            captured_color.clear()
            captured_color.append(color)
            x_spin.setValue(x_r * 100)
            y_spin.setValue(y_r * 100)
            capture_label.setText(f"✅ 캡처됨: ({x_r * 100:.1f}%, {y_r * 100:.1f}%)")
            dialog.showNormal()
            dialog.raise_()
            btn_capture.setEnabled(True)

        def _start_capture() -> None:
            btn_capture.setEnabled(False)
            capture_label.setText("⏳ F6을 눌러 위치를 지정하세요...")
            self._f6_capture_cb = _on_f6_captured
            self.f6_capture_started.emit()
            dialog.showMinimized()

        def _on_dialog_finished(_result: int) -> None:
            self.cancel_f6_capture()

        btn_capture.clicked.connect(_start_capture)
        dialog.finished.connect(_on_dialog_finished)
        layout_v.addWidget(btn_capture)
        layout_v.addWidget(capture_label)

        # ── 버튼 종류 ────────────────────────────────────────────────────────
        btn_group = QGroupBox("버튼 종류")
        btn_layout = QHBoxLayout(btn_group)
        radio_left = QRadioButton("좌클릭")
        radio_right = QRadioButton("우클릭")
        radio_double = QRadioButton("더블클릭")
        radio_left.setChecked(True)
        btn_layout.addWidget(radio_left)
        btn_layout.addWidget(radio_right)
        btn_layout.addWidget(radio_double)
        layout_v.addWidget(btn_group)

        # ── 딜레이 ──────────────────────────────────────────────────────────
        delay_form = QFormLayout()
        delay_spin = QSpinBox()
        delay_spin.setRange(0, 30000)
        delay_spin.setValue(1000)
        delay_spin.setSuffix(" ms")
        delay_form.addRow("딜레이:", delay_spin)
        layout_v.addLayout(delay_form)

        # ── 버튼 ────────────────────────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout_v.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        x_ratio = x_spin.value() / 100.0
        y_ratio = y_spin.value() / 100.0
        delay_ms = delay_spin.value()
        rec_color = captured_color[0] if captured_color else None

        if radio_right.isChecked():
            button_str = "right"
        else:
            button_str = "left"

        is_double = radio_double.isChecked()
        budget_ns = max(delay_ms * 1_000_000, 1_000_000)

        rows = self._selected_row_indices()
        if rows:
            last_row = self._rows[rows[-1]]
            insert_after_event_idx = max(last_row.event_indices)
        else:
            insert_after_event_idx = len(self._macro.events) - 1

        evs = self._macro.events
        if 0 <= insert_after_event_idx < len(evs):
            base_ts = evs[insert_after_event_idx].timestamp_ns
        elif evs:
            base_ts = evs[-1].timestamp_ns
        else:
            base_ts = 0

        _50ms = 50_000_000
        _100ms = 100_000_000

        def _make_down(ts: int, dly: int | None) -> MouseButtonEvent:
            return MouseButtonEvent(
                id=secrets.token_hex(4), type="mouse_down", timestamp_ns=ts,
                x_ratio=x_ratio, y_ratio=y_ratio, button=button_str,
                delay_override_ms=dly,
                recorded_color=rec_color,
            )

        def _make_up(ts: int) -> MouseButtonEvent:
            return MouseButtonEvent(
                id=secrets.token_hex(4), type="mouse_up", timestamp_ns=ts,
                x_ratio=x_ratio, y_ratio=y_ratio, button=button_str,
            )

        if is_double:
            new_events: list[AnyEvent] = [
                _make_down(base_ts + budget_ns, delay_ms if delay_ms > 0 else None),
                _make_up(base_ts + budget_ns + _50ms),
                _make_down(base_ts + budget_ns + _100ms, None),
                _make_up(base_ts + budget_ns + _100ms + _50ms),
            ]
            total_budget = budget_ns + _100ms + _50ms
        else:
            new_events = [
                _make_down(base_ts + budget_ns, delay_ms if delay_ms > 0 else None),
                _make_up(base_ts + budget_ns + _100ms),
            ]
            total_budget = budget_ns + _100ms

        self._push_undo()
        events = list(self._macro.events)
        for offset, ne in enumerate(new_events):
            events.insert(insert_after_event_idx + 1 + offset, ne)

        for i in range(insert_after_event_idx + 1 + len(new_events), len(events)):
            ev = events[i]
            events[i] = dataclasses.replace(ev, timestamp_ns=ev.timestamp_ns + total_budget)

        self._apply_events(events)

    def _edit_text_input(self, row_idx: int) -> None:
        """TextInputEvent의 텍스트를 수정한다."""
        if self._macro is None or row_idx >= len(self._rows):
            return
        row = self._rows[row_idx]
        primary = self._macro.events[row.primary_idx]
        if not isinstance(primary, TextInputEvent):
            return

        text, ok = QInputDialog.getText(
            self, "텍스트 편집",
            "입력할 텍스트를 수정하세요:",
            text=primary.text,
        )
        if not ok:
            return

        self._push_undo()
        updated = copy_events(self._macro.events)
        for i, ev in enumerate(updated):
            if ev.id == primary.id and isinstance(ev, TextInputEvent):
                updated[i] = dataclasses.replace(ev, text=text)
                break
        self._apply_events(updated)

    # ── 비고(Remark) 편집 ────────────────────────────────────────────────────

    def _edit_remark(self, row: int) -> None:
        """지정 행의 primary 이벤트에 비고를 설정한다.

        비고는 내용 열을 대체하지 않고 별도 비고 열에 표시되며, MacroEvent.remark로 저장된다.
        비워두면 비고가 삭제되어 빈 비고 열로 복원된다.
        """
        if self._macro is None or row >= len(self._rows):
            return
        display_row = self._rows[row]
        primary = self._macro.events[display_row.primary_idx]
        current = primary.remark

        text, ok = QInputDialog.getText(
            self, "비고 편집",
            f"행 #{row + 1}  비고 (비워두면 비고 삭제):",
            text=current,
        )
        if not ok:
            return

        stripped = text.strip()
        if stripped == current:
            return

        self._push_undo()
        updated = copy_events(self._macro.events)
        for i, ev in enumerate(updated):
            if ev.id == primary.id:
                updated[i] = dataclasses.replace(ev, remark=stripped)
                break
        else:
            self._undo_stack.pop()
            QMessageBox.warning(self, "오류", "이벤트를 찾을 수 없습니다.")
            return

        self._apply_events(updated)

    # ── 단일 이벤트 실행 ──────────────────────────────────────────────────────

    def _play_single_event(self, row: int) -> None:
        """지정 행의 이벤트만 실행하도록 신호를 방출한다."""
        if self._macro is None or row >= len(self._rows):
            return
        display_row = self._rows[row]
        indices = display_row.event_indices
        if not indices:
            return
        start_idx = min(indices)
        end_idx = max(indices) + 1
        self.play_event_range.emit(start_idx, end_idx)

