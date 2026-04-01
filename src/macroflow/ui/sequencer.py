"""MacroFlow 플로우차트 시퀀서 위젯.

두 가지 모드를 제공한다:
1. 단순 모드 — 매크로 JSON 파일을 순서대로 드래그앤드롭, 순차 실행
2. 플로우 모드 — .macroflow 파일 로드/저장 및 실행

단순 모드에서 만든 시퀀스는 내부적으로 success 연결만 있는
선형 .macroflow 플로우로 변환되어 FlowEngine이 실행한다.

drag-drop-sequencer.md 스펙 기반.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from macroflow.script_engine import (
    EndNode,
    FlowEngine,
    MacroFlow,
    MacroNode,
    load_flow,
    save_flow,
)

logger = logging.getLogger(__name__)

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


class _MacroItem:
    """시퀀서 목록의 단일 항목."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.status: str = "pending"   # pending | running | done | error
        self.message: str = ""

    @property
    def display_text(self) -> str:
        icon = _STATUS_ICONS.get(self.status, "○")
        msg = f"  — {self.message}" if self.message else ""
        return f"{icon}  {self.path.name}{msg}"


class MacroSequencerWidget(QWidget):
    """매크로 시퀀서 위젯.

    QListWidget 기반 드래그앤드롭 정렬 + 실행 상태 표시.
    매크로 JSON 파일을 목록에 추가하여 순서대로 실행한다.
    """

    # 워커 → 메인 스레드 신호
    sequence_complete = pyqtSignal(str)   # status
    sequence_error = pyqtSignal(str)      # message
    open_in_editor = pyqtSignal(str)      # 더블클릭 시 파일 경로 전달
    merge_to_editor = pyqtSignal(object)  # 병합 결과 MacroData → 에디터로 전달

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: list[_MacroItem] = []
        self._engine: FlowEngine | None = None
        self._current_flow_path: Path | None = None
        self._setup_ui()
        self.sequence_complete.connect(self._on_complete)
        self.sequence_error.connect(self._on_error)

    # ── UI 구성 ───────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 도구바
        toolbar = QToolBar("시퀀서 도구", self)
        toolbar.setMovable(False)

        self._act_add = QAction("+ 매크로 추가", self)
        self._act_add.setToolTip("매크로 JSON 파일을 목록에 추가합니다")
        self._act_add.triggered.connect(self._add_files)
        toolbar.addAction(self._act_add)

        self._act_remove = QAction("— 제거", self)
        self._act_remove.setToolTip("선택한 항목을 목록에서 제거합니다")
        self._act_remove.triggered.connect(self._remove_selected)
        self._act_remove.setEnabled(False)
        toolbar.addAction(self._act_remove)

        toolbar.addSeparator()

        self._act_open_flow = QAction("📂 플로우 열기", self)
        self._act_open_flow.setToolTip(".macroflow 파일을 불러옵니다")
        self._act_open_flow.triggered.connect(self._open_flow)
        toolbar.addAction(self._act_open_flow)

        self._act_save_flow = QAction("💾 플로우 저장", self)
        self._act_save_flow.setToolTip("현재 시퀀스를 .macroflow 파일로 저장합니다")
        self._act_save_flow.triggered.connect(self._save_flow)
        self._act_save_flow.setEnabled(False)
        toolbar.addAction(self._act_save_flow)

        toolbar.addSeparator()

        self._act_merge = QAction("🔗 에디터로 병합", self)
        self._act_merge.setToolTip(
            "목록의 모든 매크로를 순서대로 이어 붙여 하나의 매크로로 만든 뒤\n"
            "매크로 에디터 탭으로 보냅니다 (저장 후 수정 가능)"
        )
        self._act_merge.triggered.connect(self._merge_to_editor)
        self._act_merge.setEnabled(False)
        toolbar.addAction(self._act_merge)

        layout.addWidget(toolbar)

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

        # 실행 버튼
        btn_row = QHBoxLayout()
        self._btn_run = QPushButton("▶ 시퀀스 실행")
        self._btn_run.setEnabled(False)
        self._btn_run.clicked.connect(self._run_sequence)
        self._btn_stop = QPushButton("⏹ 중지")
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self._stop_sequence)
        btn_row.addWidget(self._btn_run)
        btn_row.addWidget(self._btn_stop)
        list_layout.addLayout(btn_row)

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
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            # 내부 재정렬은 기본 처리
            QListWidget.dragEnterEvent(self._list, event)

    def _drop_event(self, event: QDropEvent) -> None:
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
        item = _MacroItem(path)
        self._items.append(item)
        self._refresh_list_item(len(self._items) - 1)
        self._update_buttons()

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
        list_item.setText(item_data.display_text)
        color = _STATUS_COLORS.get(item_data.status, QColor(80, 80, 80))
        list_item.setForeground(QBrush(color))

    def _refresh_all(self) -> None:
        """전체 목록을 다시 그린다."""
        self._list.clear()
        for i in range(len(self._items)):
            self._refresh_list_item(i)

    def _sync_items_from_list(self) -> None:
        """내부 드래그앤드롭 재정렬 후 _items 순서를 동기화한다."""
        new_items: list[_MacroItem] = []
        for i in range(self._list.count()):
            li = self._list.item(i)
            if li is None:
                continue
            text = li.text()
            for item in self._items:
                if item.path.name in text:
                    new_items.append(item)
                    break
        self._items = new_items

    def add_macro_file(self, path: Path) -> None:
        """외부에서 매크로 파일을 시퀀서에 추가한다."""
        self._add_item(path)

    def has_items(self) -> bool:
        """목록에 항목이 있는지 반환한다."""
        return bool(self._items)

    def is_running(self) -> bool:
        """시퀀스가 실행 중인지 반환한다."""
        return self._engine is not None and self._engine.is_running()

    def run_sequence(self) -> None:
        """외부(main_window)에서 시퀀스를 시작한다."""
        if self._items and not self.is_running():
            self._run_sequence()

    def stop_sequence(self) -> None:
        """외부(main_window)에서 시퀀스를 중지한다."""
        self._stop_sequence()

    def _get_default_dir(self) -> str:
        """파일 다이얼로그 초기 폴더를 반환한다."""
        if getattr(sys, "frozen", False):
            return str(Path(sys.executable).parent)
        return str(Path.cwd())

    def _add_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "매크로 파일 추가",
            self._get_default_dir(),
            "Macro JSON (*.json);;모든 파일 (*)",
        )
        for path in paths:
            self._add_item(Path(path))

    def _remove_selected(self) -> None:
        rows = sorted(
            {idx.row() for idx in self._list.selectedIndexes()},
            reverse=True,
        )
        for row in rows:
            if 0 <= row < len(self._items):
                self._items.pop(row)
        self._refresh_all()
        self._update_buttons()

    def _on_selection_changed(self) -> None:
        has_sel = bool(self._list.selectedItems())
        self._act_remove.setEnabled(has_sel)

    def _on_item_double_clicked(self, item: object) -> None:
        """목록 항목 더블클릭 시 해당 매크로를 에디터로 불러온다."""
        row = self._list.currentRow()
        if 0 <= row < len(self._items):
            path = self._items[row].path
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

    def _load_flow_from_path(self, path: Path) -> None:
        try:
            flow = load_flow(str(path))
        except Exception as exc:
            QMessageBox.critical(self, "플로우 열기 오류", str(exc))
            return

        self._items.clear()
        base = path.parent

        # 선형 플로우에서 매크로 노드만 순서대로 추출
        current_id: str | None = flow.start_node_id
        visited: set[str] = set()
        while current_id and current_id in flow.nodes and current_id not in visited:
            visited.add(current_id)
            node = flow.nodes[current_id]
            if isinstance(node, MacroNode):
                macro_path = base / node.macro_path
                self._items.append(_MacroItem(macro_path))
                current_id = node.next_on_success
            else:
                break

        self._current_flow_path = path
        self._refresh_all()
        self._update_buttons()
        self._log_message(f"플로우 로드: {path.name}")

    def _save_flow(self) -> None:
        if not self._items:
            return
        if self._current_flow_path:
            self._do_save_flow(self._current_flow_path)
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "플로우 저장",
                self._get_default_dir(),
                "MacroFlow (*.macroflow)",
            )
            if not path:
                return
            if not path.endswith(".macroflow"):
                path += ".macroflow"
            self._current_flow_path = Path(path)
            self._do_save_flow(self._current_flow_path)

    def _do_save_flow(self, path: Path) -> None:
        flow = self._build_flow(path)
        try:
            save_flow(flow, str(path))
            self._log_message(f"플로우 저장: {path.name}")
        except Exception as exc:
            QMessageBox.critical(self, "플로우 저장 오류", str(exc))

    def _build_flow(self, save_path: Path) -> MacroFlow:
        """현재 목록에서 선형 MacroFlow를 생성한다."""
        base = save_path.parent
        nodes: dict[str, Any] = {}

        for i, item in enumerate(self._items):
            nid = f"macro_{i:03d}"
            next_nid = f"macro_{i + 1:03d}" if i < len(self._items) - 1 else "end_success"
            try:
                rel = item.path.relative_to(base)
            except ValueError:
                rel = item.path   # 같은 드라이브가 아닌 경우 절대경로 폴백

            nodes[nid] = MacroNode(
                id=nid,
                label=item.path.name,
                macro_path=str(rel).replace("\\", "/"),
                next_on_success=next_nid,
                next_on_failure="end_error",
                position={"x": 100, "y": 100 + i * 150},
            )

        nodes["end_success"] = EndNode(
            id="end_success", label="완료", status="success",
            position={"x": 100, "y": 100 + len(self._items) * 150},
        )
        nodes["end_error"] = EndNode(
            id="end_error", label="오류 종료", status="error",
            position={"x": 350, "y": 250},
        )

        return MacroFlow(
            version="1.0",
            name="sequence",
            created_at=datetime.now().isoformat(timespec="seconds"),
            start_node_id="macro_000" if self._items else "end_success",
            nodes=nodes,
        )

    # ── 시퀀스 실행 ───────────────────────────────────────────────────────────

    def _run_sequence(self) -> None:
        if not self._items:
            return

        # 상태 초기화
        for item in self._items:
            item.status = "pending"
            item.message = ""
        self._refresh_all()
        self._log.clear()

        # 임시 플로우 경로 (저장된 파일 없으면 홈 디렉토리 기준)
        flow_base = (
            self._current_flow_path.parent
            if self._current_flow_path
            else self._items[0].path.parent
        )
        temp_flow_path = flow_base / "__temp_sequence__.macroflow"
        flow = self._build_flow(temp_flow_path)

        self._engine = FlowEngine(
            str(temp_flow_path),
            on_node_start=self._on_node_start,
            on_node_done=self._on_node_done,
            on_complete=lambda s: self.sequence_complete.emit(s),
            on_error=lambda m: self.sequence_error.emit(m),
        )
        self._engine.start(flow)

        self._btn_run.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._log_message("시퀀스 실행 시작")

    def _stop_sequence(self) -> None:
        if self._engine:
            self._engine.stop()
            self._engine = None
        self._btn_run.setEnabled(bool(self._items))
        self._btn_stop.setEnabled(False)
        self._log_message("시퀀스 중지됨")

    def _on_node_start(self, node_id: str, label: str) -> None:
        """FlowEngine 스레드에서 호출 — 목록 업데이트는 메인 스레드에서."""
        idx = self._node_id_to_idx(node_id)
        if idx >= 0:
            self._items[idx].status = "running"
            self._items[idx].message = ""
            QTimer.singleShot(0, lambda: self._refresh_list_item(idx))
        QTimer.singleShot(0, lambda: self._log_message(f"실행: {label}"))

    def _on_node_done(self, node_id: str, success: bool, message: str) -> None:
        idx = self._node_id_to_idx(node_id)
        if idx >= 0:
            self._items[idx].status = "done" if success else "error"
            self._items[idx].message = message
            QTimer.singleShot(0, lambda: self._refresh_list_item(idx))
        status_str = "완료" if success else "오류"
        QTimer.singleShot(0, lambda: self._log_message(f"{status_str}: {message}"))

    def _on_complete(self, status: str) -> None:
        self._btn_run.setEnabled(bool(self._items))
        self._btn_stop.setEnabled(False)
        self._log_message(f"시퀀스 {status}")
        self._engine = None

    def _on_error(self, message: str) -> None:
        self._btn_run.setEnabled(bool(self._items))
        self._btn_stop.setEnabled(False)
        self._log_message(f"오류: {message}")
        QMessageBox.warning(self, "시퀀스 오류", message)
        self._engine = None

    def _node_id_to_idx(self, node_id: str) -> int:
        """macro_000 형식 node_id를 _items 인덱스로 변환한다."""
        try:
            return int(node_id.split("_")[-1])
        except (ValueError, IndexError):
            return -1

    # ── 병합 ──────────────────────────────────────────────────────────────────

    def _merge_to_editor(self) -> None:
        """시퀀서의 모든 매크로를 하나로 병합하여 에디터에 전달한다.

        각 매크로 파일을 순서대로 로드하고, macro_file.merge_macros()를 사용하여
        하나의 MacroData로 병합한 뒤 merge_to_editor 신호를 방출한다.
        이벤트의 source_file 필드에 원본 파일명이 기록되어 에디터 '출처' 열에 표시된다.
        """
        if len(self._items) < 2:
            return

        from macroflow.macro_file import load, merge_macros
        from macroflow.types import MacroData

        macro_tuples: list[tuple[MacroData, str]] = []
        for item in self._items:
            try:
                macro = load(str(item.path))
            except Exception as exc:
                QMessageBox.critical(
                    self, "로드 오류",
                    f"파일을 읽을 수 없습니다:\n{item.path.name}\n\n{exc}",
                )
                return
            macro_tuples.append((macro, item.path.name))

        try:
            merged = merge_macros(macro_tuples)
        except Exception as exc:
            QMessageBox.critical(self, "병합 오류", str(exc))
            return

        self.merge_to_editor.emit(merged)
        self._log_message(
            f"에디터로 병합 완료: {len(self._items)}개 파일 → {len(merged.events)}개 이벤트"
        )

    # ── 버튼 활성화 관리 ──────────────────────────────────────────────────────

    def _update_buttons(self) -> None:
        has_items = bool(self._items)
        self._btn_run.setEnabled(has_items)
        self._act_save_flow.setEnabled(has_items)
        self._act_merge.setEnabled(len(self._items) >= 2)

    # ── 로그 ──────────────────────────────────────────────────────────────────

    def _log_message(self, msg: str) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self._log.append(f"{now}  {msg}")
