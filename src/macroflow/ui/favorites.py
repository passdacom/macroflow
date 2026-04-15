"""MacroFlow 즐겨찾기 위젯.

자주 사용하는 매크로를 이름과 함께 영구 보관한다.
즐겨찾기 폴더(favorites/)에 사용자가 지정한 이름으로 저장한다.

- 더블클릭: 매크로 에디터로 로드
- 우클릭: 시퀀서에 추가 / 즐겨찾기에서 제거
"""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

_ITEM_COLOR = QColor(60, 110, 60)


class FavoritesWidget(QWidget):
    """즐겨찾기 매크로 관리 위젯.

    favorites/ 디렉토리를 스캔하여 목록을 구성한다.
    항목별 더블클릭·우클릭 동작을 지원한다.
    """

    open_in_editor = pyqtSignal(str)      # 파일 경로 → 에디터 탭에서 로드
    add_to_sequencer = pyqtSignal(str)    # 파일 경로 → 시퀀서에 추가

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._favorites_dir: Path | None = None  # main_window가 세팅
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 도구바
        toolbar = QToolBar("즐겨찾기 도구", self)
        toolbar.setMovable(False)

        self._act_refresh = QAction("🔄 새로고침", self)
        self._act_refresh.setToolTip("즐겨찾기 폴더를 다시 스캔합니다")
        self._act_refresh.triggered.connect(self._refresh_list)
        toolbar.addAction(self._act_refresh)

        toolbar.addSeparator()

        self._act_remove = QAction("🗑 제거", self)
        self._act_remove.setToolTip("선택한 즐겨찾기를 목록 및 파일에서 삭제합니다")
        self._act_remove.triggered.connect(self._remove_selected)
        self._act_remove.setEnabled(False)
        toolbar.addAction(self._act_remove)

        layout.addWidget(toolbar)

        # 안내 레이블
        self._hint = QLabel(
            "  '즐겨찾기에 추가' 버튼으로 현재 에디터의 매크로를 등록하세요.\n"
            "  더블클릭: 에디터로 로드  |  우클릭: 시퀀서에 추가 / 제거"
        )
        self._hint.setContentsMargins(8, 6, 8, 6)
        self._hint.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._hint)

        # 목록
        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self._list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._list.customContextMenuRequested.connect(self._context_menu)
        self._list.itemDoubleClicked.connect(self._on_double_click)
        self._list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list)

        # 하단 요약
        self._summary = QLabel("즐겨찾기 없음")
        self._summary.setContentsMargins(8, 4, 8, 4)
        self._summary.setStyleSheet("font-size: 10px; color: #aaa;")
        layout.addWidget(self._summary)

    # ── 공개 인터페이스 ───────────────────────────────────────────────────────

    def set_favorites_dir(self, path: Path) -> None:
        """즐겨찾기 디렉토리를 설정하고 목록을 초기 로드한다."""
        self._favorites_dir = path
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"즐겨찾기 폴더 생성 실패: {e}")
        self._refresh_list()

    def add_favorite(self, macro_data: object, name: str) -> bool:
        """MacroData를 즐겨찾기 폴더에 name.json 으로 저장하고 목록에 추가한다.

        Args:
            macro_data: 저장할 MacroData.
            name: 사용자가 지정한 이름 (파일명으로 사용, .json 자동 추가).

        Returns:
            저장 성공 여부.
        """
        if self._favorites_dir is None:
            logger.warning("즐겨찾기 디렉토리가 설정되지 않았습니다")
            return False

        safe_name = _sanitize_filename(name)
        if not safe_name:
            return False

        save_path = self._favorites_dir / f"{safe_name}.json"

        # 중복 이름 처리: 이미 있으면 _2, _3 ... 붙이기
        counter = 2
        while save_path.exists():
            save_path = self._favorites_dir / f"{safe_name}_{counter}.json"
            counter += 1

        try:
            from macroflow import macro_file
            macro_file.save(macro_data, str(save_path))  # type: ignore[arg-type]
        except OSError as e:
            logger.error(f"즐겨찾기 저장 오류: {e}")
            return False

        self._refresh_list()
        # 방금 추가한 항목 선택
        self._select_by_path(save_path)
        logger.info(f"즐겨찾기 추가: {save_path.name}")
        return True

    # ── 목록 갱신 ────────────────────────────────────────────────────────────

    def _refresh_list(self) -> None:
        """즐겨찾기 폴더를 스캔하여 목록을 갱신한다."""
        self._list.clear()
        if self._favorites_dir is None or not self._favorites_dir.exists():
            self._summary.setText("즐겨찾기 없음")
            self._act_remove.setEnabled(False)
            return

        files = sorted(
            self._favorites_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
        )

        for f in files:
            item = QListWidgetItem(f"⭐  {f.stem}")
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            item.setForeground(QBrush(QColor(220, 200, 80)))
            item.setToolTip(str(f))
            self._list.addItem(item)

        count = self._list.count()
        self._summary.setText(
            f"즐겨찾기 {count}개"
            if count > 0 else "즐겨찾기 없음"
        )

    def _select_by_path(self, path: Path) -> None:
        """특정 파일 경로를 가진 항목을 선택 상태로 만든다."""
        target = str(path)
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == target:
                self._list.setCurrentItem(item)
                return

    # ── 이벤트 핸들러 ────────────────────────────────────────────────────────

    def _on_double_click(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and Path(path).exists():
            self.open_in_editor.emit(path)
        else:
            QMessageBox.warning(self, "파일 없음", f"파일을 찾을 수 없습니다:\n{path}")
            self._refresh_list()

    def _on_selection_changed(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        self._act_remove.setEnabled(current is not None)

    def _context_menu(self, pos: object) -> None:
        from PyQt6.QtCore import QPoint
        item = self._list.currentItem()
        if item is None:
            return

        menu = QMenu(self)

        act_open = menu.addAction("📂 에디터로 열기")
        assert act_open is not None
        act_open.triggered.connect(lambda: self._open_item(item))

        act_seq = menu.addAction("📋 시퀀서에 추가")
        assert act_seq is not None
        act_seq.triggered.connect(lambda: self._add_item_to_sequencer(item))

        menu.addSeparator()

        act_remove = menu.addAction("🗑 즐겨찾기에서 제거")
        assert act_remove is not None
        act_remove.triggered.connect(lambda: self._remove_item(item))

        viewport = self._list.viewport()
        assert viewport is not None
        global_pos = viewport.mapToGlobal(pos if isinstance(pos, QPoint) else QPoint(0, 0))
        menu.exec(global_pos)

    def _open_item(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and Path(path).exists():
            self.open_in_editor.emit(path)
        else:
            QMessageBox.warning(self, "파일 없음", f"파일을 찾을 수 없습니다:\n{path}")
            self._refresh_list()

    def _add_item_to_sequencer(self, item: QListWidgetItem) -> None:
        path = item.data(Qt.ItemDataRole.UserRole)
        if path and Path(path).exists():
            self.add_to_sequencer.emit(path)
        else:
            QMessageBox.warning(self, "파일 없음", f"파일을 찾을 수 없습니다:\n{path}")
            self._refresh_list()

    def _remove_selected(self) -> None:
        item = self._list.currentItem()
        if item:
            self._remove_item(item)

    def _remove_item(self, item: QListWidgetItem) -> None:
        path_str = item.data(Qt.ItemDataRole.UserRole)
        name = item.text()

        reply = QMessageBox.question(
            self,
            "즐겨찾기 제거",
            f"'{name}' 을(를) 즐겨찾기에서 제거하고 파일도 삭제하시겠습니까?\n\n"
            f"파일: {path_str}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        path = Path(path_str)
        if path.exists():
            try:
                path.unlink()
                logger.info(f"즐겨찾기 파일 삭제: {path}")
            except OSError as e:
                QMessageBox.warning(self, "삭제 오류", str(e))
                return

        self._refresh_list()


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _sanitize_filename(name: str) -> str:
    """파일명으로 사용할 수 없는 문자를 제거하고 안전한 이름을 반환한다."""
    # Windows 금지 문자 제거
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "_")
    name = name.strip(". ")  # 앞뒤 점·공백 제거
    return name[:100]  # 최대 100자
