"""MacroFlow 이벤트 에디터 위젯.

그룹 표시: mouse_down+up → 클릭, key_down+up → 키 입력.
Undo/Redo, 마우스 이동 숨김 토글, 더블클릭 편집 지원.
"""

from __future__ import annotations

import copy
import dataclasses
import logging
import secrets
import sys
from collections import deque
from collections.abc import Callable
from typing import Literal

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
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
    ConditionEvent,
    KeyEvent,
    LoopEvent,
    MacroData,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    WaitEvent,
    WindowTriggerEvent,
)

logger = logging.getLogger(__name__)

_MAX_UNDO = 50

# ── 행 종류별 색상 ──────────────────────────────────────────────────────────────

_KIND_COLORS: dict[str, QColor] = {
    "click":                 QColor(60, 110, 200),
    "right_click":           QColor(80, 60, 180),
    "drag":                  QColor(40, 80, 160),
    "right_drag":            QColor(60, 40, 140),
    "color_check_click":           QColor(200, 100, 30),   # 주황 — 색 체크 스킵 모드
    "color_check_right_click":     QColor(180, 70,  20),   # 진한 주황 — 우클릭 스킵 모드
    "color_check_click_stop":      QColor(210,  45,  45),   # 빨강 — 색 체크 중지 모드
    "color_check_right_click_stop": QColor(180, 30,  30),  # 진한 빨강 — 우클릭 중지 모드
    "key_press":             QColor(60, 145, 85),
    "mouse_move":            QColor(90, 90, 90),
    "mouse_wheel":           QColor(20, 150, 155),   # 청록색 — 휠 스크롤
    "wait":                  QColor(190, 120, 50),
    "color_trigger":         QColor(140, 80, 170),
    "window_trigger":        QColor(140, 80, 170),
    "condition":             QColor(170, 140, 40),
    "loop":                  QColor(170, 140, 40),
    "orphan":                QColor(160, 60, 60),
}

_COLUMNS = ["#", "타입", "내용", "시간(ms)", "딜레이(ms)", "출처"]


# ── 표시 행 데이터 ─────────────────────────────────────────────────────────────

@dataclasses.dataclass
class _DisplayRow:
    """에디터 테이블의 한 행을 나타낸다."""

    kind: str                 # 색상/편집 동작 결정
    label: str                # 타입 열 텍스트
    detail: str               # 내용 열 텍스트
    time_ms: float            # 시간(ms) 열 값
    delay_str: str            # 딜레이(ms) 열 텍스트
    event_indices: list[int]  # 이 행이 나타내는 이벤트 인덱스들
    primary_idx: int          # 딜레이/편집 기준 이벤트 인덱스
    source_file: str = ""     # 출처 파일명 (병합 매크로에서 설정)
    color_check_enabled: bool = False         # 색 체크 활성 여부
    color_check_on_mismatch: str = "skip"     # "skip" | "stop"


def _delay_str(event: AnyEvent) -> str:
    return str(event.delay_override_ms) if event.delay_override_ms is not None else ""


def _build_rows(events: list[AnyEvent], show_moves: bool) -> list[_DisplayRow]:
    """events 리스트를 표시용 _DisplayRow 리스트로 변환한다.

    연속된 mouse_down+up → 클릭/드래그 한 행으로 그룹화.
    연속된 key_down+up → 키 입력 한 행으로 그룹화.
    show_moves=False 이면 mouse_move는 행 목록에서 제외.
    """
    rows: list[_DisplayRow] = []
    consumed: set[int] = set()

    for i, event in enumerate(events):
        if i in consumed:
            continue

        # ── 마우스 버튼 down ──────────────────────────────────────────────────
        if isinstance(event, MouseButtonEvent) and event.type == "mouse_down":
            move_indices: list[int] = []
            up_idx: int | None = None

            for j in range(i + 1, len(events)):
                if j in consumed:
                    continue
                e2 = events[j]
                if isinstance(e2, MouseMoveEvent):
                    move_indices.append(j)
                elif (
                    isinstance(e2, MouseButtonEvent)
                    and e2.type == "mouse_up"
                    and e2.button == event.button
                ):
                    up_idx = j
                    break

            btn_ko = "왼쪽" if event.button == "left" else "오른쪽"
            x_s = f"{event.x_ratio * 100:.1f}%"
            y_s = f"{event.y_ratio * 100:.1f}%"
            is_color_check = event.color_check_enabled and event.recorded_color is not None

            if up_idx is not None:
                all_indices = [i] + move_indices + [up_idx]
                consumed.update(all_indices)
                if len(move_indices) > 3:
                    kind = "drag" if event.button == "left" else "right_drag"
                    label = f"드래그({btn_ko})"
                elif is_color_check:
                    is_stop = event.color_check_on_mismatch == "stop"
                    emoji = "🛑" if is_stop else "🎨"
                    if event.button == "left":
                        kind = "color_check_click_stop" if is_stop else "color_check_click"
                    else:
                        kind = ("color_check_right_click_stop" if is_stop
                                else "color_check_right_click")
                    label = f"클릭({btn_ko}) {emoji}"
                else:
                    is_stop = False
                    emoji = "🎨"
                    kind = "click" if event.button == "left" else "right_click"
                    label = f"클릭({btn_ko})"
                # 색 정보 표시: 체크 활성=색 강조, 비활성=회색 괄호
                if event.recorded_color:
                    if is_color_check:
                        color_tag = f" {emoji}{event.recorded_color}"
                    else:
                        color_tag = f" [{event.recorded_color}]"
                    detail = f"({x_s}, {y_s}){color_tag}"
                else:
                    detail = f"({x_s}, {y_s})"
                rows.append(_DisplayRow(
                    kind, label, detail,
                    event.timestamp_ns / 1_000_000,
                    _delay_str(event), all_indices, i,
                    color_check_enabled=is_color_check,
                    color_check_on_mismatch=event.color_check_on_mismatch,
                ))
            else:
                consumed.add(i)
                rows.append(_DisplayRow(
                    "orphan", f"눌림({btn_ko})", f"({x_s}, {y_s})",
                    event.timestamp_ns / 1_000_000,
                    _delay_str(event), [i], i,
                ))

        # ── 마우스 버튼 up (미소비) ───────────────────────────────────────────
        elif isinstance(event, MouseButtonEvent) and event.type == "mouse_up":
            consumed.add(i)
            btn_ko = "왼쪽" if event.button == "left" else "오른쪽"
            x_s = f"{event.x_ratio * 100:.1f}%"
            y_s = f"{event.y_ratio * 100:.1f}%"
            rows.append(_DisplayRow(
                "orphan", f"뗌({btn_ko})", f"({x_s}, {y_s})",
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 마우스 이동 ───────────────────────────────────────────────────────
        elif isinstance(event, MouseMoveEvent):
            consumed.add(i)
            if show_moves:
                x_s = f"{event.x_ratio * 100:.1f}%"
                y_s = f"{event.y_ratio * 100:.1f}%"
                rows.append(_DisplayRow(
                    "mouse_move", "마우스 이동", f"({x_s}, {y_s})",
                    event.timestamp_ns / 1_000_000,
                    _delay_str(event), [i], i,
                ))

        # ── 키 누름 ───────────────────────────────────────────────────────────
        elif isinstance(event, KeyEvent) and event.type == "key_down":
            up_idx = None
            for j in range(i + 1, len(events)):
                if j in consumed:
                    continue
                e2 = events[j]
                if (
                    isinstance(e2, KeyEvent)
                    and e2.type == "key_up"
                    and e2.vk_code == event.vk_code
                ):
                    up_idx = j
                    break

            if up_idx is not None:
                consumed.add(i)
                consumed.add(up_idx)
                rows.append(_DisplayRow(
                    "key_press", "키 입력", event.key,
                    event.timestamp_ns / 1_000_000,
                    _delay_str(event), [i, up_idx], i,
                ))
            else:
                consumed.add(i)
                rows.append(_DisplayRow(
                    "key_press", "키 누름", event.key,
                    event.timestamp_ns / 1_000_000,
                    _delay_str(event), [i], i,
                ))

        # ── 키 뗌 (미소비) ────────────────────────────────────────────────────
        elif isinstance(event, KeyEvent) and event.type == "key_up":
            consumed.add(i)
            rows.append(_DisplayRow(
                "key_press", "키 뗌", event.key,
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 대기 ─────────────────────────────────────────────────────────────
        elif isinstance(event, WaitEvent):
            consumed.add(i)
            rows.append(_DisplayRow(
                "wait", "대기", f"{event.duration_ms}ms",
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 마우스 휠 ────────────────────────────────────────────────────────
        elif isinstance(event, MouseWheelEvent):
            # 연속된 같은 축(axis) 휠 이벤트를 하나의 행으로 그룹핑한다.
            # 다른 이벤트 타입이 사이에 끼면 그룹을 끊는다.
            group_indices: list[int] = [i]
            total_delta: int = event.delta
            for j in range(i + 1, len(events)):
                if j in consumed:
                    break
                e2 = events[j]
                if isinstance(e2, MouseWheelEvent) and e2.axis == event.axis:
                    group_indices.append(j)
                    total_delta += e2.delta
                else:
                    break
            consumed.update(group_indices)

            # 방향 아이콘 결정
            if event.axis == "vertical":
                icon = "↑" if total_delta > 0 else "↓"
                label = f"↕ 휠 {'위' if total_delta > 0 else '아래'}"
            else:
                icon = "→" if total_delta > 0 else "←"
                label = f"↔ 휠 {'우' if total_delta > 0 else '좌'}"

            notches = abs(total_delta) // 120 or 1  # 0 방지
            count_str = f" ×{len(group_indices)}" if len(group_indices) > 1 else ""
            x_s = f"{event.x_ratio * 100:.1f}%"
            y_s = f"{event.y_ratio * 100:.1f}%"
            detail = (
                f"{icon} {notches}노치  Δ{total_delta:+d}{count_str}"
                f"  @ ({x_s}, {y_s})"
            )
            rows.append(_DisplayRow(
                "mouse_wheel", label, detail,
                event.timestamp_ns / 1_000_000,
                _delay_str(event), group_indices, i,
            ))

        # ── 색 트리거 ─────────────────────────────────────────────────────────
        elif isinstance(event, ColorTriggerEvent):
            consumed.add(i)
            x_s = f"{event.x_ratio * 100:.1f}%"
            y_s = f"{event.y_ratio * 100:.1f}%"
            rows.append(_DisplayRow(
                "color_trigger", "색 트리거",
                f"({x_s}, {y_s}) {event.target_color}",
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 창 트리거 ─────────────────────────────────────────────────────────
        elif isinstance(event, WindowTriggerEvent):
            consumed.add(i)
            rows.append(_DisplayRow(
                "window_trigger", "창 트리거",
                event.window_title_contains,
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 조건 분기 ─────────────────────────────────────────────────────────
        elif isinstance(event, ConditionEvent):
            consumed.add(i)
            rows.append(_DisplayRow(
                "condition", "조건 분기",
                event.expression[:30],
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 반복 ─────────────────────────────────────────────────────────────
        elif isinstance(event, LoopEvent):
            consumed.add(i)
            rows.append(_DisplayRow(
                "loop", "반복", f"×{event.count}",
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

    return rows


def _cell(text: str) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
    return item


# ── 키 이름 → VK 코드 매핑 ────────────────────────────────────────────────────

_NAME_TO_VK: dict[str, int] = {
    # 제어 키
    "backspace": 0x08, "tab": 0x09, "enter": 0x0D, "return": 0x0D,
    "shift": 0x10, "ctrl": 0x11, "control": 0x11, "alt": 0x12,
    "pause": 0x13, "capslock": 0x14,
    "escape": 0x1B, "esc": 0x1B, "space": 0x20,
    "pageup": 0x21, "pagedown": 0x22, "end": 0x23, "home": 0x24,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "insert": 0x2D, "delete": 0x2E, "del": 0x2E,
    # 숫자 (일반)
    **{str(d): 0x30 + d for d in range(10)},
    # 알파벳
    **{chr(ord("a") + k): 0x41 + k for k in range(26)},
    # 기능 키
    **{f"f{n}": 0x70 + n - 1 for n in range(1, 25)},
    # 숫자패드
    "num0": 0x60, "num1": 0x61, "num2": 0x62, "num3": 0x63,
    "num4": 0x64, "num5": 0x65, "num6": 0x66, "num7": 0x67,
    "num8": 0x68, "num9": 0x69,
    "num*": 0x6A, "num+": 0x6B, "num-": 0x6D, "num.": 0x6E, "num/": 0x6F,
    "numlock": 0x90, "scrolllock": 0x91,
    # OEM 특수문자 (US 표준 키보드 배열)
    ";": 0xBA,   # VK_OEM_1
    "=": 0xBB,   # VK_OEM_PLUS
    ",": 0xBC,   # VK_OEM_COMMA
    "-": 0xBD,   # VK_OEM_MINUS
    ".": 0xBE,   # VK_OEM_PERIOD
    "/": 0xBF,   # VK_OEM_2
    "`": 0xC0,   # VK_OEM_3
    "[": 0xDB,   # VK_OEM_4
    "\\": 0xDC,  # VK_OEM_5
    "]": 0xDD,   # VK_OEM_6
    "'": 0xDE,   # VK_OEM_7
    # 수식어 확장
    "lshift": 0xA0, "rshift": 0xA1,
    "lctrl": 0xA2, "rctrl": 0xA3,
    "lalt": 0xA4, "ralt": 0xA5,
    "lwin": 0x5B, "rwin": 0x5C,
    # 기타
    "printscreen": 0x2C, "prtsc": 0x2C,
    "apps": 0x5D,
    # 하위 호환 별칭 — recorder.py 구버전이 저장한 이름도 편집 가능하도록
    "period": 0xBE, "comma": 0xBC, "minus": 0xBD, "equal": 0xBB,
    "slash": 0xBF, "backtick": 0xC0,
    "bracket_left": 0xDB, "backslash": 0xDC,
    "bracket_right": 0xDD, "quote": 0xDE, "semicolon": 0xBA,
    "shift_left": 0xA0, "shift_right": 0xA1,
    "ctrl_left": 0xA2, "ctrl_right": 0xA3,
    "alt_left": 0xA4, "alt_right": 0xA5,
    "win_left": 0x5B, "win_right": 0x5C,
    "numpad0": 0x60, "numpad1": 0x61, "numpad2": 0x62, "numpad3": 0x63,
    "numpad4": 0x64, "numpad5": 0x65, "numpad6": 0x66, "numpad7": 0x67,
    "numpad8": 0x68, "numpad9": 0x69,
}


def _key_name_to_vk(key_name: str, fallback_vk: int) -> int:
    """키 이름 문자열을 VK 코드로 변환한다.

    1) _NAME_TO_VK 딕셔너리에서 찾는다.
    2) Windows 환경에서 단일 문자이면 VkKeyScanA API로 조회한다.
    3) 위 모두 실패하면 fallback_vk를 반환한다.
    """
    lower = key_name.lower()
    if lower in _NAME_TO_VK:
        return _NAME_TO_VK[lower]

    # Win32 VkKeyScanA: 단일 ASCII 문자 → VK 코드 변환 (US 레이아웃 기준)
    if sys.platform == "win32" and len(key_name) == 1:
        try:
            import ctypes
            result = ctypes.windll.user32.VkKeyScanA(ord(key_name[0]))
            vk = result & 0xFF
            # VkKeyScanA 실패 시 0xFF 반환
            if vk not in (0x00, 0xFF):
                return vk
        except Exception:
            pass

    return fallback_vk


# ── 위젯 ──────────────────────────────────────────────────────────────────────

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
        # 비고(remark): event_id → 비고 문자열. 내용 열 표시를 대체.
        self._remarks: dict[str, str] = {}
        # 재생 하이라이트: 마지막으로 하이라이트된 행 인덱스 (-1 = 없음).
        self._last_highlight_row: int = -1
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
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)

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
        self._remarks.clear()
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
            if col == 1:  # 타입 열은 kind 색 유지
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
        self._rows = _build_rows(events, self._show_moves)
        # 출처 열: primary 이벤트의 source_file을 각 행에 반영
        for row in self._rows:
            row.source_file = events[row.primary_idx].source_file
        # 비고: 있으면 내용 열을 대체
        for row in self._rows:
            eid = events[row.primary_idx].id
            if eid in self._remarks:
                row.detail = f"📝 {self._remarks[eid]}"
        self._last_highlight_row = -1  # 갱신 시 하이라이트 초기화
        self._table.setRowCount(len(self._rows))

        for row_idx, row in enumerate(self._rows):
            color = _KIND_COLORS.get(row.kind, QColor(80, 80, 80))

            source_item = _cell(row.source_file)
            source_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            items = [
                _cell(str(row_idx + 1)),
                _cell(row.label),
                _cell(row.detail),
                _cell(f"{row.time_ms:.0f}"),
                _cell(row.delay_str),
                source_item,
            ]

            items[1].setBackground(QBrush(color))
            items[1].setForeground(QBrush(QColor(255, 255, 255)))

            for col, item in enumerate(items):
                if col != 5:  # 출처 열은 이미 정렬 지정됨
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row_idx, col, item)

        total = len(events)
        raw_total = len(self._macro.raw_events)
        move_count = sum(1 for e in events if e.type == "mouse_move")
        display_count = len(self._rows)
        edited_tag = " [편집됨]" if self._macro.is_edited else ""
        self._summary.setText(
            f"표시: {display_count}개  (원본: {total}개, raw: {raw_total}개)"
            f"  |  이동: {move_count}개{edited_tag}"
        )

    # ── Undo / Redo ───────────────────────────────────────────────────────────

    def _push_undo(self) -> None:
        if self._macro is None:
            return
        self._undo_stack.append(copy.deepcopy(self._macro.events))
        self._redo_stack.clear()
        self._act_undo.setEnabled(True)
        self._act_redo.setEnabled(False)

    def _apply_events(self, events: list[AnyEvent]) -> None:
        assert self._macro is not None
        self._macro = MacroData(
            meta=self._macro.meta,
            settings=self._macro.settings,
            raw_events=self._macro.raw_events,
            events=events,
            is_edited=True,
        )
        self._refresh()
        self.macro_changed.emit(self._macro)

    def _undo(self) -> None:
        if not self._undo_stack or self._macro is None:
            return
        self._redo_stack.append(copy.deepcopy(self._macro.events))
        events = self._undo_stack.pop()
        self._act_undo.setEnabled(bool(self._undo_stack))
        self._act_redo.setEnabled(True)
        self._apply_events(events)

    def _redo(self) -> None:
        if not self._redo_stack or self._macro is None:
            return
        self._undo_stack.append(copy.deepcopy(self._macro.events))
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

            act_edit_delay = menu.addAction("딜레이 설정...")
            act_edit_delay.triggered.connect(lambda: self._edit_delay(rows[0]))

            if row.kind == "key_press" and isinstance(primary, KeyEvent):
                act_edit_key = menu.addAction("키 값 변경...")
                act_edit_key.triggered.connect(lambda: self._edit_key(rows[0]))

            _COLOR_CHECK_KINDS = (
                "click", "right_click", "drag", "right_drag",
                "color_check_click", "color_check_right_click",
                "color_check_click_stop", "color_check_right_click_stop",
            )

            if row.kind in _COLOR_CHECK_KINDS + ("orphan", "mouse_move"):
                act_edit_pos = menu.addAction("위치 변경...")
                assert act_edit_pos is not None
                act_edit_pos.triggered.connect(lambda: self._edit_position(rows[0]))

            # 색 체크 토글 — recorded_color가 있는 클릭/드래그에서만 표시
            if row.kind in _COLOR_CHECK_KINDS and isinstance(primary, MouseButtonEvent) and primary.recorded_color is not None:
                is_checked = primary.color_check_enabled
                check_text = "🎨 색 체크 끄기" if is_checked else "🎨 색 체크 켜기"
                act_color = menu.addAction(check_text)
                assert act_color is not None
                act_color.triggered.connect(lambda: self._toggle_color_check(rows[0]))

                # 불일치 동작 전환 (색 체크 활성화된 경우만)
                if is_checked:
                    if primary.color_check_on_mismatch == "skip":
                        act_mode = menu.addAction("⏹ 불일치 시: 중지로 변경")
                    else:
                        act_mode = menu.addAction("▶ 불일치 시: 스킵으로 변경")
                    assert act_mode is not None
                    act_mode.triggered.connect(
                        lambda: self._toggle_color_check_mode(rows[0])
                    )

            if row.kind == "mouse_wheel":
                act_edit_wheel = menu.addAction("스크롤 편집...")
                act_edit_wheel.triggered.connect(lambda: self._edit_wheel(rows[0]))

            act_remark = menu.addAction("📝 비고 편집...")
            act_remark.triggered.connect(lambda: self._edit_remark(rows[0]))

            menu.addSeparator()

        act_delete = menu.addAction(f"행 삭제 ({len(rows)}개)")
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
        if col == 4:  # 딜레이 셀
            self._edit_delay(row)
        elif col == 1:  # 타입 셀 → 비고 편집
            self._edit_remark(row)
        elif col == 2:  # 내용 셀
            primary = self._macro.events[display_row.primary_idx]
            if display_row.kind == "key_press" and isinstance(primary, KeyEvent):
                self._edit_key(row)
            elif display_row.kind in (
                "click", "right_click", "drag", "right_drag",
                "color_check_click", "color_check_right_click",
                "color_check_click_stop", "color_check_right_click_stop",
                "orphan", "mouse_move",
            ):
                self._edit_position(row)
            elif display_row.kind == "mouse_wheel":
                self._edit_wheel(row)
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
        new_vk = _key_name_to_vk(new_key, primary.vk_code)

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

        def _on_f6_captured(x_r: float, y_r: float, _color: str) -> None:
            """F6 캡처 콜백 — 다이얼로그 복원 및 SpinBox 갱신."""
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
                timeout_ms=10000,
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

    def _toggle_color_check_mode(self, row_idx: int) -> None:
        """지정 행 클릭 이벤트의 color_check_on_mismatch를 skip ↔ stop으로 전환한다."""
        if self._macro is None or row_idx >= len(self._rows):
            return
        row = self._rows[row_idx]
        primary = self._macro.events[row.primary_idx]
        if not isinstance(primary, MouseButtonEvent) or not primary.color_check_enabled:
            return
        new_mode: Literal["skip", "stop"] = (
            "stop" if primary.color_check_on_mismatch == "skip" else "skip"
        )
        self._push_undo()
        try:
            new_macro = set_color_check_on_mismatch(self._macro, primary.id, new_mode)
        except (KeyError, TypeError):
            self._undo_stack.pop()
            return
        self._macro = new_macro
        self._refresh()
        self.macro_changed.emit(self._macro)

    # ── 비고(Remark) 편집 ────────────────────────────────────────────────────

    def _edit_remark(self, row: int) -> None:
        """지정 행에 비고를 설정한다.

        비고가 있으면 내용 열에 📝 prefix와 함께 원래 내용 대신 표시된다.
        비워두면 비고가 삭제되어 원래 내용이 복원된다.
        """
        if self._macro is None or row >= len(self._rows):
            return
        display_row = self._rows[row]
        event_id = self._macro.events[display_row.primary_idx].id
        current = self._remarks.get(event_id, "")

        text, ok = QInputDialog.getText(
            self, "비고 편집",
            f"행 #{row + 1}  비고 (비워두면 기본 표시로 복원):",
            text=current,
        )
        if not ok:
            return

        stripped = text.strip()
        if stripped:
            self._remarks[event_id] = stripped
        else:
            self._remarks.pop(event_id, None)

        # 해당 셀만 갱신 — 전체 refresh 불필요
        detail_text = f"📝 {stripped}" if stripped else display_row.detail
        # _DisplayRow.detail 갱신 후 셀 텍스트 업데이트
        display_row.detail = detail_text
        item = self._table.item(row, 2)
        if item is not None:
            # detail이 원래 내용이면 remark 없음 → 직접 재계산
            if not stripped:
                # 원래 detail을 재계산하기 위해 해당 행만 다시 빌드
                events = self._macro.events
                rebuilt = _build_rows(events, self._show_moves)
                if row < len(rebuilt):
                    src_row = rebuilt[row]
                    src_row.source_file = events[src_row.primary_idx].source_file
                    display_row.detail = src_row.detail
            item.setText(display_row.detail)

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

