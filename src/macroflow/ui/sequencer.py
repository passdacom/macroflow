"""MacroFlow 플로우차트 시퀀서 위젯.

두 가지 모드를 제공한다:
1. 단순 모드 — 매크로 JSON 파일을 순서대로 드래그앤드롭, 순차 실행
2. 플로우 모드 — .macroflow 파일 로드/저장 및 실행

단순 모드에서 만든 시퀀스는 내부적으로 success 연결만 있는
선형 .macroflow 플로우로 변환되어 FlowEngine이 실행한다.

drag-drop-sequencer.md 스펙 기반.
"""

from __future__ import annotations

import copy
import dataclasses
import logging
import secrets
import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QDragEnterEvent, QDropEvent, QKeySequence
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSpinBox,
    QSplitter,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from macroflow.event_insertions import (
    _insert_click_events,
    _insert_color_trigger_event,
    _insert_text_input_event,
)
from macroflow.macro_file import inline_event_block_valid, settings_types_valid
from macroflow.script_engine import (
    EndNode,
    FlowEngine,
    MacroFlow,
    MacroNode,
    WaitFixedNode,
    load_flow,
    save_flow,
)
from macroflow.sequence_limits import MAX_SEQUENCE_WAIT_MS
from macroflow.sequence_merge import merge_sequence_items
from macroflow.sequence_model import (
    InlineActionItem,
    MacroFileItem,
    SequenceItem,
    WaitItem,
    build_sequence_flow,
    project_sequence_flow,
)
from macroflow.types import (
    ColorTriggerEvent,
    MacroSettings,
    MouseButtonEvent,
    TextInputEvent,
)

from .spinbox_sizing import fit_compact_spinbox

logger = logging.getLogger(__name__)

_MAX_GAP_MS = MAX_SEQUENCE_WAIT_MS

# ── 상태 색상 ─────────────────────────────────────────────────────────────────
_STATUS_COLORS: dict[str, QColor] = {
    "pending":   QColor(80,  80,  80),
    "running":   QColor(200, 130, 30),
    "done":      QColor(50,  150, 60),
    "error":     QColor(190, 50,  50),
}

_STATUS_ICONS: dict[str, str] = {
    "pending": "○",
    "running": "⚡",
    "done":    "✅",
    "error":   "❌",
}


def _linear_gap_ms(flow: MacroFlow) -> int | None:
    """단순 선형 플로우의 균일한 매크로 사이 대기값을 반환한다.

    대기가 없으면 0, 분기/지원하지 않는 노드/서로 다른 대기값이면 None이다.
    """
    node_id: str | None = flow.start_node_id
    visited: set[str] = set()
    durations: list[int] = []

    while node_id and node_id not in visited:
        visited.add(node_id)
        node = flow.nodes.get(node_id)
        if isinstance(node, MacroNode):
            node_id = node.next_on_success
        elif isinstance(node, WaitFixedNode):
            durations.append(max(0, int(node.duration_ms)))
            node_id = node.next
        elif isinstance(node, EndNode):
            break
        else:
            return None

    if not durations:
        return 0
    first = durations[0]
    return first if all(value == first for value in durations) else None


def _project_linear_flow(
    flow: MacroFlow,
    flow_path: str | Path,
) -> tuple[list[Path], int]:
    """플로우를 단순 시퀀서로 손실 없이 투영한다.

    성공 경로는 ``Macro (Wait Macro)* [End]`` 형태여야 하며, 모든 대기값은
    동일해야 한다. 매크로 실패 경로는 error EndNode로 끝나는 경우만 허용한다.
    그 밖의 분기·지원하지 않는 노드·미사용 노드는 저장 시 유실되므로 거부한다.
    """
    if flow.start_node_id not in flow.nodes:
        raise ValueError("시작 노드를 찾을 수 없습니다.")

    base = Path(flow_path).parent
    current_id: str | None = flow.start_node_id
    visited: set[str] = set()
    error_end_ids: set[str] = set()
    paths: list[Path] = []
    durations: list[int] = []

    while current_id is not None:
        if current_id in visited:
            raise ValueError("순환 플로우는 단순 시퀀서로 열 수 없습니다.")
        node = flow.nodes.get(current_id)
        if node is None:
            raise ValueError(f"노드 ID를 찾을 수 없습니다: {current_id!r}")
        visited.add(current_id)

        if isinstance(node, MacroNode):
            raw_path = Path(node.macro_path)
            macro_path = (
                raw_path.resolve(strict=False)
                if raw_path.is_absolute()
                else (base / raw_path).resolve(strict=False)
            )
            paths.append(macro_path)

            if node.next_on_failure is not None:
                failure_node = flow.nodes.get(node.next_on_failure)
                if not isinstance(failure_node, EndNode) or failure_node.status != "error":
                    raise ValueError(
                        "분기 실패 경로가 있는 플로우는 단순 시퀀서로 열 수 없습니다."
                    )
                error_end_ids.add(node.next_on_failure)
            current_id = node.next_on_success
            continue

        if isinstance(node, WaitFixedNode):
            next_node = flow.nodes.get(node.next) if node.next is not None else None
            if not paths or not isinstance(next_node, MacroNode):
                raise ValueError(
                    "매크로 사이가 아닌 대기 노드는 단순 시퀀서로 열 수 없습니다."
                )
            duration_ms = int(node.duration_ms)
            if not 0 <= duration_ms <= _MAX_GAP_MS:
                raise ValueError(
                    f"시퀀서 간격은 0~{_MAX_GAP_MS}ms 범위여야 합니다."
                )
            durations.append(duration_ms)
            current_id = node.next
            continue

        if isinstance(node, EndNode):
            if node.status != "success":
                raise ValueError("성공 경로가 오류 종료 노드로 연결되어 있습니다.")
            current_id = None
            continue

        raise ValueError(
            "분기 또는 지원하지 않는 노드가 있어 단순 시퀀서로 열 수 없습니다."
        )

    if not paths:
        raise ValueError("매크로 노드가 없는 플로우는 단순 시퀀서로 열 수 없습니다.")
    if durations and len(durations) != len(paths) - 1:
        raise ValueError("일부 구간에만 대기가 있어 단일 간격으로 표현할 수 없습니다.")
    if durations and any(value != durations[0] for value in durations[1:]):
        raise ValueError("서로 다른 대기값은 단일 시퀀서 간격으로 표현할 수 없습니다.")

    represented_ids = visited | error_end_ids
    if represented_ids != set(flow.nodes):
        raise ValueError("시퀀서에 표시되지 않는 노드가 있어 로드를 거부했습니다.")

    gap_ms = durations[0] if durations else 0
    expected = _build_canonical_flow(
        paths,
        gap_ms,
        Path(flow_path),
        created_at=flow.created_at,
    )
    if flow != expected:
        raise ValueError(
            "정규 시퀀서 문서가 아닌 선형 플로우는 원본 정보를 보존할 수 없어 "
            "열 수 없습니다."
        )

    return paths, gap_ms


def _build_canonical_flow(
    macro_paths: list[Path],
    gap_ms: int,
    save_path: Path,
    *,
    created_at: str,
) -> MacroFlow:
    """시퀀서가 무손실로 다시 저장할 수 있는 정규 플로우를 생성한다."""
    base = save_path.parent
    nodes: dict[str, Any] = {}
    count = len(macro_paths)
    effective_gap_ms = gap_ms if count > 1 else 0

    for index, path in enumerate(macro_paths):
        node_id = f"macro_{index:03d}"
        if effective_gap_ms > 0 and index < count - 1:
            next_node_id = f"wait_{index:03d}"
        else:
            next_node_id = (
                f"macro_{index + 1:03d}" if index < count - 1 else "end_success"
            )

        try:
            macro_path = str(path.relative_to(base)).replace("\\", "/")
        except ValueError:
            macro_path = str(path).replace("\\", "/")

        nodes[node_id] = MacroNode(
            id=node_id,
            label=path.name,
            macro_path=macro_path,
            next_on_success=next_node_id,
            next_on_failure="end_error",
            position={
                "x": 100,
                "y": 100 + index * (200 if effective_gap_ms > 0 else 150),
            },
        )
        if effective_gap_ms > 0 and index < count - 1:
            wait_node_id = f"wait_{index:03d}"
            nodes[wait_node_id] = WaitFixedNode(
                id=wait_node_id,
                label=f"{effective_gap_ms}ms 대기",
                duration_ms=effective_gap_ms,
                next=f"macro_{index + 1:03d}",
                position={"x": 100, "y": 100 + index * 200 + 100},
            )

    row_count = count * (2 if effective_gap_ms > 0 else 1)
    nodes["end_success"] = EndNode(
        id="end_success",
        label="완료",
        status="success",
        position={"x": 100, "y": 100 + row_count * 100},
    )
    nodes["end_error"] = EndNode(
        id="end_error",
        label="오류 종료",
        status="error",
        position={"x": 350, "y": 250},
    )
    return MacroFlow(
        version="1.0",
        name="sequence",
        created_at=created_at,
        start_node_id="macro_000" if macro_paths else "end_success",
        nodes=nodes,
    )


class _MacroItem(MacroFileItem):
    """Backward-compatible macro row with stable sequence identity."""

    def __init__(self, path: Path, *, step_id: str | None = None) -> None:
        super().__init__(
            step_id=step_id or f"macro-{secrets.token_hex(8)}",
            path=path,
        )

    @property
    def display_text(self) -> str:
        return _item_display_text(self)


def _item_display_text(item: SequenceItem) -> str:
    icon = _STATUS_ICONS.get(item.status, "○")
    message = f"  — {item.message}" if item.message else ""
    if isinstance(item, MacroFileItem):
        detail = f"📄  {item.path.name}"
    elif isinstance(item, WaitItem):
        detail = f"⏱  {item.duration_ms}ms 대기"
    else:
        display_label = item.label.replace("\r", "").replace("\n", "\\n")
        if len(display_label) > 120:
            display_label = f"{display_label[:117]}..."
        detail = f"⚙  {display_label}"
    return f"{icon}  {detail}{message}"


def _node_local_events(events: list[Any]) -> list[Any]:
    if not events:
        return []
    first_timestamp = min(event.timestamp_ns for event in events)
    return [
        dataclasses.replace(event, timestamp_ns=event.timestamp_ns - first_timestamp)
        for event in events
    ]


class MacroSequencerWidget(QWidget):
    """매크로 시퀀서 위젯.

    QListWidget 기반 드래그앤드롭 정렬 + 실행 상태 표시.
    매크로 JSON 파일을 목록에 추가하여 순서대로 실행한다.
    """

    # 워커 → 메인 스레드 신호
    sequence_complete = pyqtSignal(str)   # status
    sequence_error = pyqtSignal(str)      # message
    sequence_progress = pyqtSignal(int, int)  # current, total macro step
    open_in_editor = pyqtSignal(str)      # 더블클릭 시 파일 경로 전달
    merge_to_editor = pyqtSignal(object)  # 병합 결과 MacroData → 에디터로 전달
    dirty_changed = pyqtSignal(bool)      # 미저장 변경 상태
    f6_capture_started = pyqtSignal()
    f6_capture_ended = pyqtSignal()
    _node_started = pyqtSignal(int, str, str)
    _node_finished = pyqtSignal(int, str, bool, str)
    _sequence_finished = pyqtSignal(int, str)
    _sequence_failed = pyqtSignal(int, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: list[SequenceItem] = []
        self._engine: FlowEngine | None = None
        self._run_generation = 0
        self._active_generation: int | None = None
        self._current_flow_path: Path | None = None
        self._document_created_at: str | None = None
        self._is_dirty = False
        self._suppress_dirty = False
        self._capture_hotkey_label = "F6"
        self._f6_capture_cb: Callable[[float, float, str], None] | None = None
        self._setup_ui()
        self._node_started.connect(self._apply_node_start)
        self._node_finished.connect(self._apply_node_done)
        self._sequence_finished.connect(self._apply_sequence_complete)
        self._sequence_failed.connect(self._apply_sequence_error)
        self._stop_watch_timer = QTimer(self)
        self._stop_watch_timer.setInterval(100)
        self._stop_watch_timer.timeout.connect(self._poll_stopping_engine)

    # ── UI 구성 ───────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 1행: 시퀀스 단계 추가
        add_toolbar = QToolBar("단계 추가", self)
        add_toolbar.setObjectName("sequencer-add-toolbar")
        add_toolbar.setMovable(False)

        self._act_add = QAction("➕ 매크로 추가", self)
        self._act_add.setToolTip("매크로 JSON 파일을 선택 행 다음에 추가합니다")
        self._act_add.triggered.connect(self._add_files)
        add_toolbar.addAction(self._act_add)

        self._act_add_text = QAction("📝 문구 추가", self)
        self._act_add_text.triggered.connect(self._prompt_text_action)
        add_toolbar.addAction(self._act_add_text)

        self._act_add_click = QAction("🖱 클릭 추가", self)
        self._act_add_click.setToolTip("클릭 종류를 선택한 뒤 F6으로 좌표를 지정합니다")
        self._act_add_click.triggered.connect(self._prompt_click_capture)
        add_toolbar.addAction(self._act_add_click)

        self._act_add_color = QAction("🎨 색상 대기 추가", self)
        self._act_add_color.setToolTip("F6으로 좌표와 목표 색상을 지정합니다")
        self._act_add_color.triggered.connect(self._prompt_color_capture)
        add_toolbar.addAction(self._act_add_color)

        self._act_add_wait = QAction("⏱ 대기 추가", self)
        self._act_add_wait.triggered.connect(self._prompt_wait_action)
        add_toolbar.addAction(self._act_add_wait)

        # 2행: 플로우 문서와 선택 단계 편집
        manage_toolbar = QToolBar("플로우/편집", self)
        manage_toolbar.setObjectName("sequencer-manage-toolbar")
        manage_toolbar.setMovable(False)

        self._act_duplicate = QAction("⧉ 복제", self)
        self._act_duplicate.setShortcut(QKeySequence("Ctrl+D"))
        self._act_duplicate.triggered.connect(self._duplicate_selected)
        self._act_duplicate.setEnabled(False)
        manage_toolbar.addAction(self._act_duplicate)

        self._act_remove = QAction("— 제거", self)
        self._act_remove.setToolTip("선택한 항목을 목록에서 제거합니다")
        self._act_remove.triggered.connect(self._remove_selected)
        self._act_remove.setEnabled(False)
        manage_toolbar.addAction(self._act_remove)

        flow_toolbar = QToolBar("플로우 파일", self)
        flow_toolbar.setObjectName("sequencer-flow-toolbar")
        flow_toolbar.setMovable(False)

        self._act_open_flow = QAction("📂 플로우 열기", self)
        self._act_open_flow.setToolTip(".macroflow 파일을 불러옵니다")
        self._act_open_flow.triggered.connect(self._open_flow)
        flow_toolbar.addAction(self._act_open_flow)

        self._act_save_flow = QAction("💾 플로우 저장", self)
        self._act_save_flow.setToolTip(
            "현재 .macroflow 파일에 덮어쓰기 저장합니다 (파일이 없으면 다른 이름으로 저장)"
        )
        self._act_save_flow.triggered.connect(self._save_flow)
        self._act_save_flow.setEnabled(False)
        flow_toolbar.addAction(self._act_save_flow)

        self._act_save_flow_as = QAction("💾 플로우 다른 이름으로 저장", self)
        self._act_save_flow_as.setToolTip("새 경로를 지정하여 .macroflow 파일로 저장합니다")
        self._act_save_flow_as.triggered.connect(self._save_flow_as)
        self._act_save_flow_as.setEnabled(False)
        flow_toolbar.addAction(self._act_save_flow_as)

        manage_toolbar.addSeparator()

        self._act_merge = QAction("🔗 매크로로 병합", self)
        self._act_merge.setToolTip(
            "목록의 모든 매크로를 순서대로 이어 붙여 하나의 매크로로 만든 뒤\n"
            "매크로 에디터 탭으로 보냅니다 (저장 후 수정 가능)"
        )
        self._act_merge.triggered.connect(self._merge_to_editor)
        self._act_merge.setEnabled(False)
        manage_toolbar.addAction(self._act_merge)

        manage_toolbar.addSeparator()
        manage_toolbar.addWidget(QLabel(" 매크로 간격:"))
        self._gap_spin = QSpinBox()
        self._gap_spin.setMinimum(0)
        self._gap_spin.setMaximum(_MAX_GAP_MS)
        self._gap_spin.setValue(500)
        self._gap_spin.setSuffix("ms")
        self._gap_spin.setToolTip(
            "시퀀스 실행: 한 매크로가 완전히 끝난 뒤 실제 시간으로 대기하며 "
            "재생 속도는 적용되지 않습니다.\n"
            "에디터 병합: 같은 숫자를 기록 타임라인 간격으로 삽입하므로 "
            "병합 후 재생 속도가 적용됩니다."
        )
        fit_compact_spinbox(
            self._gap_spin,
            ("0ms", f"{_MAX_GAP_MS}ms"),
            minimum_width=95,
        )
        self._gap_spin.valueChanged.connect(self._on_gap_changed)
        manage_toolbar.addWidget(self._gap_spin)

        layout.addWidget(flow_toolbar)
        layout.addWidget(add_toolbar)
        layout.addWidget(manage_toolbar)

        # 본문: 목록 + 실행 버튼 + 로그
        splitter = QSplitter(Qt.Orientation.Vertical, self)

        # 위쪽: 매크로 목록
        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(4, 4, 4, 4)

        self._list = QListWidget()
        self._list.setAcceptDrops(True)
        self._list.setDragEnabled(True)
        self._list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self._list.itemSelectionChanged.connect(self._on_selection_changed)
        self._list.itemDoubleClicked.connect(self._on_item_double_clicked)

        # 파일 드래그앤드롭 지원
        self._list.setAcceptDrops(True)
        self._list.viewport().setAcceptDrops(True)
        self._list.dragEnterEvent = self._drag_enter  # type: ignore[method-assign]
        self._list.dropEvent = self._drop_event       # type: ignore[method-assign]

        list_layout.addWidget(QLabel("매크로 목록 (드래그로 순서 변경, 파일을 여기로 끌어오기)"))
        list_layout.addWidget(self._list)

        splitter.addWidget(list_container)

        # 아래쪽: 실행 로그
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(4, 4, 4, 4)
        log_layout.addWidget(QLabel("실행 로그"))
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(160)
        log_layout.addWidget(self._log)
        splitter.addWidget(log_container)

        splitter.setSizes([400, 160])
        layout.addWidget(splitter)

    # ── 드래그앤드롭 (파일 시스템에서) ──────────────────────────────────────

    def _drag_enter(self, event: QDragEnterEvent) -> None:
        if self._engine is not None:
            event.ignore()
            return
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            # 내부 재정렬은 기본 처리
            QListWidget.dragEnterEvent(self._list, event)

    def _drop_event(self, event: QDropEvent) -> None:
        if self._engine is not None:
            event.ignore()
            return
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            for url in event.mimeData().urls():
                p = Path(url.toLocalFile())
                if p.suffix.lower() == ".json":
                    self._add_item(p)
                elif p.suffix.lower() == ".macroflow":
                    self._load_flow_from_path(p)
        else:
            QListWidget.dropEvent(self._list, event)
            self._sync_items_from_list()

    # ── 항목 관리 ─────────────────────────────────────────────────────────────

    def _add_item(self, path: Path) -> None:
        if self._engine is not None:
            self._log_message("실행 중에는 매크로 목록을 변경할 수 없습니다")
            return
        normalized_path = path.resolve(strict=False)
        if not normalized_path.exists():
            self._log_message(f"파일을 찾을 수 없습니다: {path}")
            return
        item = _MacroItem(normalized_path)
        self._insert_sequence_item(item)

    def _insert_sequence_item(self, item: SequenceItem) -> None:
        """Insert after the selected row, or append when there is no selection."""
        if self._engine is not None:
            self._log_message("실행 중에는 시퀀스 단계를 변경할 수 없습니다")
            return
        row = self._list.currentRow()
        index = row + 1 if 0 <= row < len(self._items) else len(self._items)
        self._items.insert(index, item)
        self._refresh_all()
        self._list.setCurrentRow(index)
        self._update_buttons()
        self._set_dirty(True)

    def add_text_action(self, text: str) -> None:
        """Add a literal text-input action after the current row."""
        if not text:
            return
        events = _node_local_events(_insert_text_input_event([], -1, text, 0))
        self._insert_sequence_item(
            InlineActionItem(
                step_id=f"inline-{secrets.token_hex(8)}",
                label=f"문구 입력: {text}",
                events=events,
                playback_settings=MacroSettings(),
            )
        )

    def add_click_action(
        self,
        x_ratio: float,
        y_ratio: float,
        *,
        button: Literal["left", "right", "middle"] = "left",
        is_double: bool = False,
        recorded_color: str | None = None,
        _replace_row: int | None = None,
    ) -> None:
        """Add or replace a click action using ratio coordinates."""
        events = _node_local_events(
            _insert_click_events(
                [],
                -1,
                x_ratio,
                y_ratio,
                button,
                is_double,
                0,
                recorded_color,
            )
        )
        click_name = f"{button} {'더블' if is_double else ''}클릭".replace("  ", " ")
        self._put_inline_action(
            InlineActionItem(
                step_id=f"inline-{secrets.token_hex(8)}",
                label=f"{click_name}: X {x_ratio:.2%}, Y {y_ratio:.2%}",
                events=events,
                playback_settings=MacroSettings(),
            ),
            _replace_row,
        )

    def add_color_wait_action(
        self,
        x_ratio: float,
        y_ratio: float,
        target_color: str,
        *,
        timeout_ms: int,
        _replace_row: int | None = None,
    ) -> None:
        """Add or replace a color trigger whose timeout is a sequence failure."""
        settings = MacroSettings()
        events = _node_local_events(
            _insert_color_trigger_event(
                [],
                -1,
                x_ratio,
                y_ratio,
                target_color,
                timeout_ms=timeout_ms,
                check_interval_ms=settings.color_trigger_check_interval_ms,
            )
        )
        self._put_inline_action(
            InlineActionItem(
                step_id=f"inline-{secrets.token_hex(8)}",
                label=(
                    f"색상 대기: {target_color.upper()} · X {x_ratio:.2%}, "
                    f"Y {y_ratio:.2%} · {timeout_ms}ms"
                ),
                events=events,
                playback_settings=settings,
            ),
            _replace_row,
        )

    def _put_inline_action(
        self,
        action: InlineActionItem,
        replace_row: int | None,
    ) -> None:
        if self._engine is not None:
            self._log_message("실행 중에는 시퀀스 단계를 변경할 수 없습니다")
            return
        if replace_row is None:
            self._insert_sequence_item(action)
            return
        if not 0 <= replace_row < len(self._items):
            return
        existing = self._items[replace_row]
        action.step_id = existing.step_id
        if isinstance(existing, InlineActionItem):
            action.playback_settings = copy.deepcopy(existing.playback_settings)
        self._items[replace_row] = action
        self._refresh_list_item(replace_row)
        self._list.setCurrentRow(replace_row)
        self._update_buttons()
        self._set_dirty(True)

    def add_wait_action(self, duration_ms: int) -> None:
        """Add an explicit real-time wait step."""
        if not 0 <= duration_ms <= _MAX_GAP_MS:
            raise ValueError(f"대기 시간은 0~{_MAX_GAP_MS}ms 범위여야 합니다.")
        self._insert_sequence_item(
            WaitItem(
                step_id=f"wait-{secrets.token_hex(8)}",
                duration_ms=duration_ms,
            )
        )

    def preflight_errors(self) -> list[str]:
        """Validate every step before any player or input side effect starts."""
        from macroflow.macro_file import load as load_macro

        errors: list[str] = []
        for index, item in enumerate(self._items, start=1):
            if isinstance(item, MacroFileItem):
                if not item.path.exists():
                    errors.append(f"{index}번 단계 파일 없음: {item.path}")
                    continue
                try:
                    load_macro(str(item.path))
                except Exception as exc:
                    errors.append(f"{index}번 단계 파일 오류: {item.path.name} ({exc})")
            elif isinstance(item, InlineActionItem):
                if (
                    not item.events
                    or not inline_event_block_valid(item.events)
                    or not settings_types_valid(item.playback_settings)
                ):
                    errors.append(f"{index}번 inline 단계 형식 오류: {item.label}")
            elif not 0 <= item.duration_ms <= _MAX_GAP_MS:
                errors.append(f"{index}번 대기 단계 범위 오류: {item.duration_ms}ms")
        return errors

    def _edit_inline_item(self, row: int) -> None:
        if self._engine is not None:
            self._log_message("실행 중에는 시퀀스 단계를 편집할 수 없습니다")
            return
        item = self._items[row]
        if isinstance(item, WaitItem):
            value, ok = QInputDialog.getInt(
                self,
                "대기 단계 편집",
                "대기 시간 (ms):",
                item.duration_ms,
                0,
                _MAX_GAP_MS,
            )
            if self._engine is not None:
                self._log_message("실행 중에는 시퀀스 단계를 편집할 수 없습니다")
                return
            if ok and value != item.duration_ms:
                item.duration_ms = value
                self._refresh_list_item(row)
                self._set_dirty(True)
            return
        if isinstance(item, InlineActionItem) and len(item.events) == 1:
            event = item.events[0]
            if isinstance(event, TextInputEvent):
                text, ok = QInputDialog.getMultiLineText(
                    self,
                    "문구 입력 편집",
                    "입력할 문구:",
                    event.text,
                )
                if self._engine is not None:
                    self._log_message("실행 중에는 시퀀스 단계를 편집할 수 없습니다")
                    return
                if ok and text and text != event.text:
                    item.events = _node_local_events(
                        _insert_text_input_event([], -1, text, 0)
                    )
                    item.label = f"문구 입력: {text}"
                    self._refresh_list_item(row)
                    self._set_dirty(True)
                    return
            if isinstance(event, ColorTriggerEvent):
                self.start_color_wait_capture(
                    timeout_ms=event.timeout_ms,
                    replace_row=row,
                )
                self._log_message(
                    f"{self._capture_hotkey_label}을 눌러 새 색상 확인 위치를 지정하세요"
                )
                return
        if isinstance(item, InlineActionItem) and item.events and all(
            isinstance(event, MouseButtonEvent) for event in item.events
        ):
            first_click = item.events[0]
            assert isinstance(first_click, MouseButtonEvent)
            self.start_click_capture(
                button=first_click.button,
                is_double=len(item.events) == 4,
                replace_row=row,
            )
            self._log_message(
                f"{self._capture_hotkey_label}을 눌러 새 클릭 위치를 지정하세요"
            )
            return
        QMessageBox.information(
            self,
            "단계 편집",
            "이 단계는 현재 시퀀서에서 직접 편집할 수 없습니다.",
        )

    def _refresh_list_item(self, idx: int) -> None:
        """단일 목록 행을 갱신한다."""
        item_data = self._items[idx]
        if idx < self._list.count():
            list_item = self._list.item(idx)
        else:
            list_item = QListWidgetItem()
            self._list.addItem(list_item)

        if list_item is None:
            return
        list_item.setText(_item_display_text(item_data))
        list_item.setData(Qt.ItemDataRole.UserRole, item_data.step_id)
        color = _STATUS_COLORS.get(item_data.status, QColor(80, 80, 80))
        list_item.setForeground(QBrush(color))

    def _refresh_all(self) -> None:
        """전체 목록을 다시 그린다."""
        self._list.clear()
        for i in range(len(self._items)):
            self._refresh_list_item(i)

    def _sync_items_from_list(self) -> None:
        """내부 드래그앤드롭 재정렬 후 _items 순서를 동기화한다."""
        if self._engine is not None:
            self._refresh_all()
            return
        previous_ids = [item.step_id for item in self._items]
        items_by_id = {item.step_id: item for item in self._items}
        new_items: list[SequenceItem] = []
        for i in range(self._list.count()):
            list_item = self._list.item(i)
            if list_item is None:
                continue
            step_id = list_item.data(Qt.ItemDataRole.UserRole)
            if isinstance(step_id, str) and step_id in items_by_id:
                new_items.append(items_by_id[step_id])
        self._items = new_items
        if [item.step_id for item in new_items] != previous_ids:
            self._set_dirty(True)

    def add_macro_file(self, path: Path) -> None:
        """외부에서 매크로 파일을 시퀀서에 추가한다."""
        self._add_item(path)

    def has_items(self) -> bool:
        """목록에 항목이 있는지 반환한다."""
        return bool(self._items)

    def item_count(self) -> int:
        """현재 시퀀스의 매크로 단계 수를 반환한다."""
        return len(self._items)

    def is_dirty(self) -> bool:
        """저장되지 않은 시퀀서 변경이 있는지 반환한다."""
        return self._is_dirty

    def _set_dirty(self, dirty: bool) -> None:
        """미저장 상태를 변경하고 실제 전이만 알린다."""
        if self._is_dirty == dirty:
            return
        self._is_dirty = dirty
        self.dirty_changed.emit(dirty)

    def _on_gap_changed(self, _value: int) -> None:
        """목록이 있는 시퀀스의 대기값 변경을 미저장 변경으로 기록한다."""
        if self._items and not self._suppress_dirty:
            self._set_dirty(True)

    def is_running(self) -> bool:
        """worker가 종료 확인되기 전까지 active run으로 간주한다."""
        return self._engine is not None

    def run_sequence(self, speed: float = 1.0) -> bool:
        """외부(main_window)에서 시퀀스를 시작한다."""
        if self._items and self._engine is None:
            return self._run_sequence(speed=speed)
        return False

    def stop_sequence(self) -> bool:
        """중지를 요청하고 worker 종료가 확인됐는지 반환한다."""
        return self._stop_sequence()

    def open_flow(self) -> None:
        """외부(main_window)에서 플로우 열기 다이얼로그를 연다."""
        self._open_flow()

    def set_capture_hotkey_label(self, label: str) -> None:
        self._capture_hotkey_label = label
        self._act_add_click.setToolTip(f"클릭 종류를 선택한 뒤 {label}으로 좌표를 지정합니다")
        self._act_add_color.setToolTip(f"{label}으로 좌표와 목표 색상을 지정합니다")

    def save_flow(self) -> bool:
        """외부(main_window)에서 현재 플로우를 저장한다."""
        return self._save_flow()

    def save_flow_as(self) -> bool:
        """외부(main_window)에서 현재 플로우를 다른 이름으로 저장한다."""
        return self._save_flow_as()

    def confirm_discard_changes(self) -> bool:
        """미저장 변경의 저장·폐기·취소를 확인한다.

        Returns:
            열기 또는 종료를 계속해도 되면 True. 저장 취소·실패 또는
            명시적 취소이면 False.
        """
        if not self._is_dirty:
            return True

        answer = QMessageBox.question(
            self,
            "시퀀서 변경 내용 저장",
            "저장하지 않은 시퀀서 변경 내용이 있습니다. 저장할까요?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if answer == QMessageBox.StandardButton.Discard:
            return True
        if answer == QMessageBox.StandardButton.Save:
            if self._current_flow_path is not None:
                return self._do_save_flow(self._current_flow_path)
            return self._save_flow_as()
        return False

    def _get_default_dir(self) -> str:
        """파일 다이얼로그 초기 폴더를 반환한다."""
        if getattr(sys, "frozen", False):
            return str(Path(sys.executable).parent)
        return str(Path.cwd())

    def _prompt_text_action(self) -> None:
        text, ok = QInputDialog.getMultiLineText(
            self,
            "문구 입력 단계",
            "입력할 문구:",
        )
        if ok and text:
            self.add_text_action(text)

    def _prompt_click_capture(self) -> None:
        choice, ok = QInputDialog.getItem(
            self,
            "클릭 단계",
            "클릭 종류:",
            ["좌클릭", "더블클릭", "우클릭"],
            0,
            False,
        )
        if not ok:
            return
        button: Literal["left", "right", "middle"] = (
            "right" if choice == "우클릭" else "left"
        )
        self.start_click_capture(button=button, is_double=choice == "더블클릭")
        self._log_message(
            f"{self._capture_hotkey_label}을 눌러 클릭 위치를 지정하세요"
        )

    def _prompt_color_capture(self) -> None:
        timeout_ms, ok = QInputDialog.getInt(
            self,
            "색상 대기 단계",
            "최대 대기 시간 (ms, 0=제한 없음):",
            10_000,
            0,
            600_000,
        )
        if ok:
            self.start_color_wait_capture(timeout_ms=timeout_ms)
            self._log_message(
                f"{self._capture_hotkey_label}을 눌러 색상 확인 위치를 지정하세요"
            )

    def _prompt_wait_action(self) -> None:
        duration_ms, ok = QInputDialog.getInt(
            self,
            "고정 대기 단계",
            "대기 시간 (ms):",
            500,
            0,
            _MAX_GAP_MS,
        )
        if ok:
            self.add_wait_action(duration_ms)

    def is_f6_capture_active(self) -> bool:
        return self._f6_capture_cb is not None

    def start_click_capture(
        self,
        *,
        button: Literal["left", "right", "middle"],
        is_double: bool,
        replace_row: int | None = None,
    ) -> None:
        self.cancel_f6_capture()
        self._f6_capture_cb = lambda x, y, color: self.add_click_action(
            x,
            y,
            button=button,
            is_double=is_double,
            recorded_color=color,
            _replace_row=replace_row,
        )
        self.f6_capture_started.emit()

    def start_color_wait_capture(
        self,
        *,
        timeout_ms: int,
        replace_row: int | None = None,
    ) -> None:
        self.cancel_f6_capture()
        self._f6_capture_cb = lambda x, y, color: self.add_color_wait_action(
            x,
            y,
            color,
            timeout_ms=timeout_ms,
            _replace_row=replace_row,
        )
        self.f6_capture_started.emit()

    def consume_f6_capture(self, x_ratio: float, y_ratio: float, color_hex: str) -> bool:
        callback = self._f6_capture_cb
        if callback is None:
            return False
        self._f6_capture_cb = None
        try:
            callback(x_ratio, y_ratio, color_hex)
        finally:
            self.f6_capture_ended.emit()
        return True

    def cancel_f6_capture(self) -> None:
        if self._f6_capture_cb is None:
            return
        self._f6_capture_cb = None
        self.f6_capture_ended.emit()

    def _duplicate_selected(self) -> None:
        if self._engine is not None:
            return
        row = self._list.currentRow()
        if not 0 <= row < len(self._items):
            return
        duplicate = copy.deepcopy(self._items[row])
        if isinstance(duplicate, MacroFileItem):
            duplicate.step_id = f"macro-{secrets.token_hex(8)}"
        elif isinstance(duplicate, WaitItem):
            duplicate.step_id = f"wait-{secrets.token_hex(8)}"
        else:
            duplicate.step_id = f"inline-{secrets.token_hex(8)}"
        duplicate.status = "pending"
        duplicate.message = ""
        self._insert_sequence_item(duplicate)

    def _add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "매크로 파일 추가",
            self._get_default_dir(),
            "Macro JSON (*.json);;모든 파일 (*)",
        )
        for path in paths:
            self._add_item(Path(path))

    def _remove_selected(self) -> None:
        if self._engine is not None:
            self._log_message("실행 중에는 매크로 목록을 변경할 수 없습니다")
            return
        rows = sorted(
            {idx.row() for idx in self._list.selectedIndexes()},
            reverse=True,
        )
        removed = False
        for row in rows:
            if 0 <= row < len(self._items):
                self._items.pop(row)
                removed = True
        self._refresh_all()
        self._update_buttons()
        if removed:
            self._set_dirty(True)

    def _on_selection_changed(self) -> None:
        has_sel = bool(self._list.selectedItems())
        self._act_remove.setEnabled(has_sel and self._engine is None)
        self._act_duplicate.setEnabled(has_sel and self._engine is None)

    def _on_item_double_clicked(self, item: object) -> None:
        """Open macro rows in the editor; edit inline rows in place."""
        del item
        if self._engine is not None:
            self._log_message("실행 중에는 시퀀스 단계를 열거나 편집할 수 없습니다")
            return
        row = self._list.currentRow()
        if 0 <= row < len(self._items):
            sequence_item = self._items[row]
            if not isinstance(sequence_item, MacroFileItem):
                self._edit_inline_item(row)
                return
            path = sequence_item.path
            if path.exists():
                self.open_in_editor.emit(str(path))
            else:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self, "파일 없음",
                    f"파일을 찾을 수 없습니다:\n{path}",
                )

    # ── 플로우 파일 I/O ───────────────────────────────────────────────────────

    def _open_flow(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "플로우 파일 열기",
            self._get_default_dir(),
            "MacroFlow (*.macroflow);;모든 파일 (*)",
        )
        if path:
            self._load_flow_from_path(Path(path))

    def _load_flow_from_path(self, path: Path) -> bool:
        if self._engine is not None:
            self._log_message("실행 중에는 플로우를 교체할 수 없습니다")
            return False
        if not self.confirm_discard_changes():
            return False
        if self._engine is not None:
            self._log_message("실행 중에는 플로우를 교체할 수 없습니다")
            return False
        try:
            flow = load_flow(str(path), strict=True)
            if flow.version == "1.0":
                macro_paths, gap_ms = _project_linear_flow(flow, path)
                if not self._gap_spin.minimum() <= gap_ms <= self._gap_spin.maximum():
                    raise ValueError("현재 시퀀서 UI에서 표현할 수 없는 간격입니다.")
                loaded_items: list[SequenceItem] = [
                    _MacroItem(macro_path, step_id=f"macro_{index:03d}")
                    for index, macro_path in enumerate(macro_paths)
                ]
            else:
                loaded_items = project_sequence_flow(flow, path)
                gap_ms = 0
        except Exception as exc:
            QMessageBox.critical(self, "플로우 열기 오류", str(exc))
            return False

        if self._engine is not None:
            self._log_message("실행 중에는 플로우를 교체할 수 없습니다")
            return False

        self._suppress_dirty = True
        try:
            self._items = loaded_items
            self._gap_spin.setValue(gap_ms)
        finally:
            self._suppress_dirty = False

        self._current_flow_path = path
        self._document_created_at = flow.created_at
        self._refresh_all()
        self._update_buttons()
        self._set_dirty(False)
        self._log_message(f"플로우 로드: {path.name}")
        return True

    def _save_flow(self) -> bool:
        if self._engine is not None or not self._items:
            return False
        if self._current_flow_path is None:
            return self._save_flow_as()

        answer = QMessageBox.question(
            self,
            "플로우 덮어쓰기",
            f"현재 파일을 덮어쓸까요?\n{self._current_flow_path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False
        if self._engine is not None:
            return False

        return self._do_save_flow(self._current_flow_path)

    def _save_flow_as(self) -> bool:
        if self._engine is not None or not self._items:
            return False
        path, _ = QFileDialog.getSaveFileName(
            self, "다른 이름으로 플로우 저장",
            self._get_default_dir(),
            "MacroFlow (*.macroflow)",
        )
        if not path:
            return False
        if self._engine is not None:
            return False
        if not path.endswith(".macroflow"):
            path += ".macroflow"
        return self._do_save_flow(Path(path))

    def _do_save_flow(self, path: Path) -> bool:
        if self._engine is not None:
            return False
        try:
            flow = self._build_flow(path)
            if self._engine is not None:
                return False
            save_flow(flow, str(path))
        except Exception as exc:
            QMessageBox.critical(self, "플로우 저장 오류", str(exc))
            return False
        self._current_flow_path = path
        self._document_created_at = flow.created_at
        self._set_dirty(False)
        self._log_message(f"플로우 저장: {path.name}")
        return True

    def _build_flow(self, save_path: Path) -> MacroFlow:
        """현재 목록에서 정규 선형 MacroFlow를 생성한다."""
        created_at = self._document_created_at or datetime.now().isoformat(
            timespec="seconds"
        )
        if all(isinstance(item, MacroFileItem) for item in self._items):
            return _build_canonical_flow(
                [item.path for item in self._items if isinstance(item, MacroFileItem)],
                self._gap_spin.value(),
                save_path,
                created_at=created_at,
            )
        return build_sequence_flow(self._items, save_path, created_at=created_at)

    # ── 시퀀스 실행 ───────────────────────────────────────────────────────────

    def _run_sequence(self, speed: float = 1.0) -> bool:
        self.cancel_f6_capture()
        if not self._items or self._engine is not None:
            return False

        errors = self.preflight_errors()
        if errors:
            message = "\n".join(errors)
            self._log_message(f"실행 전 검증 실패: {message}")
            QMessageBox.warning(self, "시퀀스 실행 전 검증 실패", message)
            self.sequence_error.emit(message)
            return False

        # 상태 초기화
        for item in self._items:
            item.status = "pending"
            item.message = ""
        self._refresh_all()
        self._log.clear()

        # 임시 플로우 경로 (저장된 파일 없으면 홈 디렉토리 기준)
        first_macro = next(
            (item for item in self._items if isinstance(item, MacroFileItem)),
            None,
        )
        flow_base = (
            self._current_flow_path.parent
            if self._current_flow_path
            else first_macro.path.parent
            if first_macro is not None
            else Path.cwd()
        )
        temp_flow_path = flow_base / "__temp_sequence__.macroflow"
        flow = self._build_flow(temp_flow_path)

        self._run_generation += 1
        generation = self._run_generation
        self._active_generation = generation
        engine = FlowEngine(
            str(temp_flow_path),
            on_node_start=lambda node_id, label, gen=generation: self._node_started.emit(
                gen, node_id, label
            ),
            on_node_done=lambda node_id, success, message, gen=generation: (
                self._node_finished.emit(gen, node_id, success, message)
            ),
            on_complete=lambda status, gen=generation: self._sequence_finished.emit(
                gen, status
            ),
            on_error=lambda message, gen=generation: self._sequence_failed.emit(
                gen, message
            ),
            speed=speed,
        )
        self._engine = engine
        self._update_buttons()
        try:
            engine.start(flow)
        except Exception:
            if self._engine is engine and self._active_generation == generation:
                self._engine = None
                self._active_generation = None
                self._update_buttons()
            raise
        self._log_message(f"시퀀스 실행 시작 (속도 {speed:.1f}x)")
        return True

    def _stop_sequence(self) -> bool:
        engine = self._engine
        generation = self._active_generation
        if engine is None:
            return True

        engine.stop()
        if self._engine is not engine:
            return True
        if engine.is_running():
            self._log_message("시퀀스 중지 요청됨 — worker 종료 대기 중")
            self._stop_watch_timer.start()
            self._update_buttons()
            return False

        if generation is not None:
            self._finish_stopped_generation(generation)
        else:
            self._engine = None
            self._update_buttons()
        self._log_message("시퀀스 중지됨")
        return True

    def _poll_stopping_engine(self) -> None:
        engine = self._engine
        generation = self._active_generation
        if engine is None:
            self._stop_watch_timer.stop()
            return
        if engine.is_running():
            return
        if generation is not None:
            self._finish_stopped_generation(generation)
        else:
            self._engine = None
            self._stop_watch_timer.stop()
            self._update_buttons()
        self._log_message("시퀀스 worker 종료 확인")

    def _finish_stopped_generation(self, generation: int) -> bool:
        if generation != self._active_generation:
            return False
        self._stop_watch_timer.stop()
        self._engine = None
        self._active_generation = None
        self._update_buttons()
        return True

    def _on_node_start(self, node_id: str, label: str) -> None:
        """호환용 callback: 현재 generation을 포함해 GUI thread로 전달한다."""
        generation = self._active_generation
        if generation is not None:
            self._node_started.emit(generation, node_id, label)

    def _apply_node_start(self, generation: int, node_id: str, label: str) -> None:
        if generation != self._active_generation:
            return
        idx = self._node_id_to_idx(node_id)
        if 0 <= idx < len(self._items):
            self._items[idx].status = "running"
            self._items[idx].message = ""
            self._refresh_list_item(idx)
            self.sequence_progress.emit(idx + 1, len(self._items))
        self._log_message(f"실행: {label}")

    def _on_node_done(self, node_id: str, success: bool, message: str) -> None:
        generation = self._active_generation
        if generation is not None:
            self._node_finished.emit(generation, node_id, success, message)

    def _apply_node_done(
        self,
        generation: int,
        node_id: str,
        success: bool,
        message: str,
    ) -> None:
        if generation != self._active_generation:
            return
        idx = self._node_id_to_idx(node_id)
        if 0 <= idx < len(self._items):
            self._items[idx].status = "done" if success else "error"
            self._items[idx].message = message
            self._refresh_list_item(idx)
        status_str = "완료" if success else "오류"
        self._log_message(f"{status_str}: {message}")

    def _apply_sequence_complete(self, generation: int, status: str) -> None:
        if not self._finish_stopped_generation(generation):
            return
        self._log_message(f"시퀀스 {status}")
        self.sequence_complete.emit(status)

    def _apply_sequence_error(self, generation: int, message: str) -> None:
        if not self._finish_stopped_generation(generation):
            return
        self._log_message(f"오류: {message}")
        QMessageBox.warning(self, "시퀀스 오류", message)
        self.sequence_error.emit(message)

    def _node_id_to_idx(self, node_id: str) -> int:
        """Map stable v1.1 IDs or legacy macro_NNN IDs to visible rows."""
        for index, item in enumerate(self._items):
            if item.step_id == node_id:
                return index
        if not node_id.startswith("macro_"):
            return -1
        try:
            return int(node_id.split("_")[-1])
        except (ValueError, IndexError):
            return -1

    # ── 병합 ──────────────────────────────────────────────────────────────────

    def _merge_to_editor(self) -> None:
        """시퀀서의 파일·인라인·대기 단계를 하나의 편집 매크로로 변환한다."""
        if self._engine is not None or len(self._items) < 2:
            return

        from macroflow.macro_file import load

        try:
            merged = merge_sequence_items(
                self._items,
                load_macro=lambda path: load(str(path)),
                macro_gap_ms=self._gap_spin.value(),
            )
        except Exception as exc:
            QMessageBox.critical(self, "병합 오류", str(exc))
            return

        self.merge_to_editor.emit(merged)
        self._log_message(
            f"에디터로 병합 완료: {len(self._items)}개 단계 → {len(merged.events)}개 이벤트"
        )

    # ── 버튼 활성화 관리 ──────────────────────────────────────────────────────

    def _update_buttons(self) -> None:
        has_items = bool(self._items)
        editable = self._engine is None
        self._act_add.setEnabled(editable)
        self._act_add_text.setEnabled(editable)
        self._act_add_click.setEnabled(editable)
        self._act_add_color.setEnabled(editable)
        self._act_add_wait.setEnabled(editable)
        self._act_remove.setEnabled(editable and bool(self._list.selectedItems()))
        self._act_duplicate.setEnabled(editable and bool(self._list.selectedItems()))
        self._act_open_flow.setEnabled(editable)
        self._act_save_flow.setEnabled(editable and has_items)
        self._act_save_flow_as.setEnabled(editable and has_items)
        macro_only = all(isinstance(item, MacroFileItem) for item in self._items)
        has_macro = any(isinstance(item, MacroFileItem) for item in self._items)
        self._act_merge.setEnabled(editable and has_macro and len(self._items) >= 2)
        self._act_merge.setToolTip(
            "목록의 매크로·문구·클릭·색상 대기·대기를 순서대로 에디터로 병합합니다.\n"
            "혼합 병합의 대기 단계는 매크로 대기로 변환되어 재생 속도의 영향을 받습니다."
            if has_macro
            else "에디터 병합에는 매크로 파일이 하나 이상 필요합니다."
        )
        self._gap_spin.setEnabled(editable and macro_only)
        self._list.setDragEnabled(editable)
        self._list.setAcceptDrops(editable)
        viewport = self._list.viewport()
        if viewport is not None:
            viewport.setAcceptDrops(editable)

    # ── 로그 ──────────────────────────────────────────────────────────────────

    def _log_message(self, msg: str) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self._log.append(f"{now}  {msg}")
