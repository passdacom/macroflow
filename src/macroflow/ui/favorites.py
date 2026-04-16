"""MacroFlow 즐겨찾기 위젯 (트리 구조).

즐겨찾기를 그룹별로 분류하고 아코디언 트리 뷰로 표시한다.
그룹과 항목 모두 드래그앤드롭으로 순서 변경·이동이 가능하다.

- 더블클릭(항목): 에디터로 로드
- 더블클릭(그룹): 접기/펼치기
- 우클릭(그룹): 이름 변경 / 그룹 삭제
- 우클릭(항목): 에디터 열기 / 시퀀서 추가 / 그룹 이동 / 제거
- 드래그앤드롭: 순서 변경 및 그룹 간 이동
"""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any, cast

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QDropEvent
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QInputDialog,
    QLabel,
    QMenu,
    QMessageBox,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

_INDEX_FILE = "_index.json"
_DEFAULT_GROUP_ID = "default"
_DEFAULT_GROUP_NAME = "기본"

_GROUP_FG = QColor(100, 160, 220)   # 파란 계열 — 그룹 헤더
_ITEM_FG = QColor(220, 200, 80)     # 노란 계열 — 매크로 항목

# setData/data 에 사용하는 역할 (UserRole = 256)
_ROLE = Qt.ItemDataRole.UserRole  # dict {"type": "group"|"item", "id"/"path": str}


# ── 커스텀 트리 위젯 ─────────────────────────────────────────────────────────

class FavoritesTreeWidget(QTreeWidget):
    """드래그앤드롭 유효성을 검사하는 즐겨찾기 트리 위젯.

    그룹 항목은 루트 레벨 재정렬만 허용하고,
    매크로 항목은 반드시 그룹 하위에만 드롭되도록 강제한다.
    """

    item_moved = pyqtSignal()  # 드래그앤드롭 완료 → 인덱스 저장 트리거

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

    def dropEvent(self, event: QDropEvent) -> None:  # type: ignore[override]
        """드롭 위치를 검사하여 유효하지 않은 이동을 차단한다."""
        dragged = self.currentItem()
        if dragged is None:
            event.ignore()
            return

        data: dict[str, Any] = dragged.data(0, _ROLE) or {}
        dragged_type: str = data.get("type", "")
        target_item = self.itemAt(event.position().toPoint())
        drop_pos = self.dropIndicatorPosition()
        DIP = QAbstractItemView.DropIndicatorPosition

        if dragged_type == "group":
            # 그룹은 루트 레벨에서만 순서 변경 가능
            if target_item is None:
                event.ignore()
                return
            tdata: dict[str, Any] = target_item.data(0, _ROLE) or {}
            if tdata.get("type") != "group":
                event.ignore()
                return
            if drop_pos == DIP.OnItem:
                # 그룹 위에 OnItem 으로 드롭하면 중첩이 되므로 차단
                event.ignore()
                return
        else:
            # 매크로 항목은 반드시 그룹 하위에 있어야 함
            if target_item is None:
                event.ignore()
                return
            tdata2: dict[str, Any] = target_item.data(0, _ROLE) or {}
            target_type: str = tdata2.get("type", "")
            if target_type == "group" and drop_pos != DIP.OnItem:
                # 그룹 헤더 위/아래에 드롭 → 루트 레벨이 됨 → 차단
                event.ignore()
                return

        super().dropEvent(event)
        self.item_moved.emit()


# ── 즐겨찾기 위젯 ────────────────────────────────────────────────────────────

class FavoritesWidget(QWidget):
    """즐겨찾기 트리 위젯.

    favorites/ 디렉토리와 _index.json 파일을 함께 관리한다.
    새로 추가된 항목은 기본 그룹('기본')에 들어가며,
    우클릭 메뉴나 드래그앤드롭으로 다른 그룹으로 이동할 수 있다.
    """

    open_in_editor = pyqtSignal(str)    # 파일 경로 → 에디터 탭 로드
    add_to_sequencer = pyqtSignal(str)  # 파일 경로 → 시퀀서 추가

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._favorites_dir: Path | None = None
        self._index: dict[str, Any] = {}
        self._setup_ui()

    # ── UI 구성 ──────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 도구바
        toolbar = QToolBar("즐겨찾기 도구", self)
        toolbar.setMovable(False)

        self._act_new_group = QAction("📁 새 그룹", self)
        self._act_new_group.setToolTip("새 그룹을 추가합니다")
        self._act_new_group.triggered.connect(self._add_group)
        toolbar.addAction(self._act_new_group)

        toolbar.addSeparator()

        self._act_refresh = QAction("🔄 새로고침", self)
        self._act_refresh.setToolTip("즐겨찾기 폴더를 다시 스캔합니다")
        self._act_refresh.triggered.connect(self._refresh_tree)
        toolbar.addAction(self._act_refresh)

        toolbar.addSeparator()

        self._act_remove = QAction("🗑 제거", self)
        self._act_remove.setToolTip("선택한 즐겨찾기를 제거합니다")
        self._act_remove.triggered.connect(self._remove_selected)
        self._act_remove.setEnabled(False)
        toolbar.addAction(self._act_remove)

        layout.addWidget(toolbar)

        # 안내 레이블
        self._hint = QLabel(
            "  '즐겨찾기에 추가' 버튼으로 현재 에디터의 매크로를 등록하세요.\n"
            "  더블클릭: 에디터로 로드  |  우클릭: 메뉴  |  드래그: 순서/그룹 변경"
        )
        self._hint.setContentsMargins(8, 6, 8, 6)
        self._hint.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self._hint)

        # 트리 위젯
        self._tree = FavoritesTreeWidget(self)
        self._tree.setHeaderHidden(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._context_menu)
        self._tree.itemDoubleClicked.connect(self._on_double_click)
        self._tree.currentItemChanged.connect(self._on_selection_changed)
        self._tree.itemExpanded.connect(self._on_expand_change)
        self._tree.itemCollapsed.connect(self._on_expand_change)
        self._tree.item_moved.connect(self._on_item_moved)
        layout.addWidget(self._tree)

        # 하단 요약
        self._summary = QLabel("즐겨찾기 없음")
        self._summary.setContentsMargins(8, 4, 8, 4)
        self._summary.setStyleSheet("font-size: 10px; color: #aaa;")
        layout.addWidget(self._summary)

    # ── 공개 인터페이스 ──────────────────────────────────────────────────────

    def set_favorites_dir(self, path: Path) -> None:
        """즐겨찾기 디렉토리를 설정하고 트리를 초기 로드한다."""
        self._favorites_dir = path
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"즐겨찾기 폴더 생성 실패: {e}")
        self._load_index()
        self._refresh_tree()

    def add_favorite(self, macro_data: object, name: str) -> bool:
        """MacroData를 즐겨찾기 폴더에 저장하고 기본 그룹에 추가한다.

        Args:
            macro_data: 저장할 MacroData.
            name: 사용자가 지정한 이름 (.json 자동 추가).

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

        # 기본 그룹 맨 앞에 추가
        self._ensure_default_group()
        default = self._find_group(_DEFAULT_GROUP_ID)
        if default is not None:
            default["items"].insert(0, save_path.name)
        self._save_index()
        self._refresh_tree()
        logger.info(f"즐겨찾기 추가: {save_path.name}")
        return True

    # ── 인덱스 파일 관리 ─────────────────────────────────────────────────────

    def _index_path(self) -> Path | None:
        if self._favorites_dir is None:
            return None
        return self._favorites_dir / _INDEX_FILE

    def _load_index(self) -> None:
        """_index.json 을 읽어 self._index 에 적재한다."""
        idx_path = self._index_path()
        if idx_path is None:
            return
        if not idx_path.exists():
            self._index = {"version": 1, "groups": []}
            self._ensure_default_group()
            self._save_index()
            return
        try:
            with open(idx_path, encoding="utf-8") as f:
                self._index = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"즐겨찾기 인덱스 로드 실패, 초기화: {e}")
            self._index = {"version": 1, "groups": []}
        self._ensure_default_group()

    def _save_index(self) -> None:
        """self._index 를 _index.json 에 저장한다."""
        idx_path = self._index_path()
        if idx_path is None:
            return
        try:
            with open(idx_path, "w", encoding="utf-8") as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except OSError as e:
            logger.error(f"즐겨찾기 인덱스 저장 오류: {e}")

    def _ensure_default_group(self) -> None:
        """기본 그룹이 없으면 인덱스 맨 앞에 생성한다."""
        groups: list[dict[str, Any]] = self._index.setdefault("groups", [])
        if not any(g.get("id") == _DEFAULT_GROUP_ID for g in groups):
            groups.insert(0, {
                "id": _DEFAULT_GROUP_ID,
                "name": _DEFAULT_GROUP_NAME,
                "expanded": True,
                "items": [],
            })

    def _find_group(self, gid: str) -> dict[str, Any] | None:
        for g in self._index.get("groups", []):
            if g.get("id") == gid:
                return cast(dict[str, Any], g)
        return None

    def _all_indexed_filenames(self) -> set[str]:
        """인덱스에 등록된 모든 파일명 집합을 반환한다."""
        result: set[str] = set()
        for g in self._index.get("groups", []):
            for fn in g.get("items", []):
                result.add(fn)
        return result

    def _find_item_group_id(self, filename: str) -> str | None:
        """파일명이 속한 그룹 ID를 반환한다."""
        for g in self._index.get("groups", []):
            if filename in g.get("items", []):
                raw_id = g.get("id")
                return str(raw_id) if raw_id is not None else None
        return None

    # ── 트리 갱신 ────────────────────────────────────────────────────────────

    def _refresh_tree(self) -> None:
        """인덱스를 기반으로 트리를 재구성한다."""
        self._tree.clear()
        if self._favorites_dir is None:
            self._summary.setText("즐겨찾기 없음")
            return

        # 실제 존재하는 파일 집합 (인덱스 파일 제외)
        existing: set[str] = {
            f.name for f in self._favorites_dir.glob("*.json")
            if f.name != _INDEX_FILE
        }

        # 인덱스에 없는 파일 → 기본 그룹에 추가 (고아 처리)
        indexed = self._all_indexed_filenames()
        orphans = existing - indexed
        if orphans:
            default = self._find_group(_DEFAULT_GROUP_ID)
            if default is not None:
                for fn in sorted(orphans):
                    default["items"].append(fn)

        total_items = 0
        for group in self._index.get("groups", []):
            gid: str = group.get("id", "")
            gname: str = group.get("name", "그룹")
            expanded: bool = group.get("expanded", True)
            items_in_group: list[str] = group.get("items", [])

            # 실제 존재하는 파일만 유지
            valid_items = [fn for fn in items_in_group if fn in existing]
            group["items"] = valid_items

            # 그룹 트리 항목
            group_tw = QTreeWidgetItem(self._tree)
            group_tw.setText(0, f"📁  {gname}  ({len(valid_items)})")
            group_tw.setData(0, _ROLE, {"type": "group", "id": gid})
            group_tw.setForeground(0, QBrush(_GROUP_FG))
            font = group_tw.font(0)
            font.setBold(True)
            group_tw.setFont(0, font)
            group_tw.setFlags(
                Qt.ItemFlag.ItemIsEnabled
                | Qt.ItemFlag.ItemIsSelectable
                | Qt.ItemFlag.ItemIsDragEnabled
                | Qt.ItemFlag.ItemIsDropEnabled
            )
            group_tw.setExpanded(expanded)

            for fn in valid_items:
                file_path = self._favorites_dir / fn
                child = QTreeWidgetItem(group_tw)
                stem = Path(fn).stem
                child.setText(0, f"⭐  {stem}")
                child.setData(0, _ROLE, {"type": "item", "path": str(file_path)})
                child.setForeground(0, QBrush(_ITEM_FG))
                child.setToolTip(0, str(file_path))
                child.setFlags(
                    Qt.ItemFlag.ItemIsEnabled
                    | Qt.ItemFlag.ItemIsSelectable
                    | Qt.ItemFlag.ItemIsDragEnabled
                )
                total_items += 1

        self._save_index()
        self._summary.setText(
            f"즐겨찾기 {total_items}개"
            if total_items > 0 else "즐겨찾기 없음"
        )
        self._act_remove.setEnabled(False)

    # ── 그룹 관리 ────────────────────────────────────────────────────────────

    def _add_group(self) -> None:
        """새 그룹을 대화상자로 추가한다."""
        name, ok = QInputDialog.getText(self, "새 그룹", "그룹 이름:")
        if not ok or not name.strip():
            return
        gid = f"group_{uuid.uuid4().hex[:8]}"
        self._index.setdefault("groups", []).append({
            "id": gid,
            "name": name.strip(),
            "expanded": True,
            "items": [],
        })
        self._save_index()
        self._refresh_tree()

    def _rename_group(self, gid: str) -> None:
        group = self._find_group(gid)
        if group is None:
            return
        old_name: str = group.get("name", "")
        new_name, ok = QInputDialog.getText(
            self, "그룹 이름 변경", "새 이름:", text=old_name
        )
        if not ok or not new_name.strip():
            return
        group["name"] = new_name.strip()
        self._save_index()
        self._refresh_tree()

    def _delete_group(self, gid: str) -> None:
        if gid == _DEFAULT_GROUP_ID:
            QMessageBox.information(self, "알림", "기본 그룹은 삭제할 수 없습니다.")
            return
        group = self._find_group(gid)
        if group is None:
            return

        items: list[str] = group.get("items", [])
        reply = QMessageBox.question(
            self,
            "그룹 삭제",
            f"'{group.get('name')}' 그룹을 삭제하시겠습니까?\n"
            f"그룹 내 {len(items)}개 항목은 기본 그룹으로 이동됩니다.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # 항목을 기본 그룹 앞으로 이동
        default = self._find_group(_DEFAULT_GROUP_ID)
        if default is not None and items:
            default["items"] = items + default["items"]

        self._index["groups"] = [
            g for g in self._index.get("groups", [])
            if g.get("id") != gid
        ]
        self._save_index()
        self._refresh_tree()

    def _move_item_to_group(self, filename: str, target_gid: str) -> None:
        """파일을 다른 그룹으로 이동한다."""
        for g in self._index.get("groups", []):
            items: list[str] = g.get("items", [])
            if filename in items:
                items.remove(filename)
                break
        target = self._find_group(target_gid)
        if target is not None:
            target["items"].append(filename)
        self._save_index()
        self._refresh_tree()

    # ── 이벤트 핸들러 ────────────────────────────────────────────────────────

    def _on_double_click(self, item: QTreeWidgetItem, _col: int) -> None:
        data: dict[str, Any] = item.data(0, _ROLE) or {}
        if data.get("type") == "item":
            path: str = data.get("path", "")
            if path and Path(path).exists():
                self.open_in_editor.emit(path)
            else:
                QMessageBox.warning(self, "파일 없음", f"파일을 찾을 수 없습니다:\n{path}")
                self._refresh_tree()
        elif data.get("type") == "group":
            item.setExpanded(not item.isExpanded())

    def _on_selection_changed(
        self,
        current: QTreeWidgetItem | None,
        _prev: QTreeWidgetItem | None,
    ) -> None:
        if current is None:
            self._act_remove.setEnabled(False)
            return
        data: dict[str, Any] = current.data(0, _ROLE) or {}
        self._act_remove.setEnabled(data.get("type") == "item")

    def _on_expand_change(self, item: QTreeWidgetItem) -> None:
        """그룹 펼침/접힘 상태를 인덱스에 즉시 반영한다."""
        data: dict[str, Any] = item.data(0, _ROLE) or {}
        if data.get("type") == "group":
            gid: str = data.get("id", "")
            group = self._find_group(gid)
            if group is not None:
                group["expanded"] = item.isExpanded()
                self._save_index()

    def _on_item_moved(self) -> None:
        """드래그앤드롭 완료 후 트리 순서를 인덱스에 반영한다."""
        root = self._tree.invisibleRootItem()
        if root is None:
            return

        new_groups: list[dict[str, Any]] = []
        for gi in range(root.childCount()):
            g_tw = root.child(gi)
            if g_tw is None:
                continue
            gdata: dict[str, Any] = g_tw.data(0, _ROLE) or {}
            gid = gdata.get("id", "")
            group = self._find_group(gid)
            if group is None:
                continue

            group["expanded"] = g_tw.isExpanded()

            # 자식 항목 순서 재구성
            new_items: list[str] = []
            for ii in range(g_tw.childCount()):
                child = g_tw.child(ii)
                if child is None:
                    continue
                cdata: dict[str, Any] = child.data(0, _ROLE) or {}
                path: str = cdata.get("path", "")
                if path:
                    new_items.append(Path(path).name)
            group["items"] = new_items
            new_groups.append(group)

        self._index["groups"] = new_groups
        self._save_index()

        # 그룹 텍스트(카운트) 업데이트 — 트리 재구성 없이 텍스트만 갱신
        for gi in range(root.childCount()):
            g_tw = root.child(gi)
            if g_tw is None:
                continue
            gdata2: dict[str, Any] = g_tw.data(0, _ROLE) or {}
            gid2 = gdata2.get("id", "")
            group2 = self._find_group(gid2)
            if group2:
                gname: str = group2.get("name", "그룹")
                g_tw.setText(0, f"📁  {gname}  ({g_tw.childCount()})")

    def _context_menu(self, pos: object) -> None:
        item = self._tree.currentItem()
        if item is None:
            return
        data: dict[str, Any] = item.data(0, _ROLE) or {}
        item_type: str = data.get("type", "")

        menu = QMenu(self)
        if item_type == "group":
            self._build_group_menu(menu, item)
        elif item_type == "item":
            self._build_item_menu(menu, item)
        else:
            return

        viewport = self._tree.viewport()
        assert viewport is not None
        if isinstance(pos, QPoint):
            global_pos = viewport.mapToGlobal(pos)
        else:
            global_pos = viewport.mapToGlobal(QPoint(0, 0))
        menu.exec(global_pos)

    def _build_group_menu(self, menu: QMenu, item: QTreeWidgetItem) -> None:
        data: dict[str, Any] = item.data(0, _ROLE) or {}
        gid: str = data.get("id", "")

        act_rename = menu.addAction("✏️ 이름 변경")
        assert act_rename is not None
        act_rename.triggered.connect(lambda: self._rename_group(gid))

        if gid != _DEFAULT_GROUP_ID:
            act_delete = menu.addAction("🗑 그룹 삭제")
            assert act_delete is not None
            act_delete.triggered.connect(lambda: self._delete_group(gid))

        menu.addSeparator()

        act_expand = menu.addAction("📂 모두 펼치기")
        assert act_expand is not None
        act_expand.triggered.connect(self._tree.expandAll)

        act_collapse = menu.addAction("📁 모두 접기")
        assert act_collapse is not None
        act_collapse.triggered.connect(self._tree.collapseAll)

    def _build_item_menu(self, menu: QMenu, item: QTreeWidgetItem) -> None:
        data: dict[str, Any] = item.data(0, _ROLE) or {}
        path: str = data.get("path", "")
        filename = Path(path).name if path else ""
        current_gid = self._find_item_group_id(filename)

        act_open = menu.addAction("📂 에디터로 열기")
        assert act_open is not None
        act_open.triggered.connect(lambda: self._open_item(item))

        act_seq = menu.addAction("📋 시퀀서에 추가")
        assert act_seq is not None
        act_seq.triggered.connect(lambda: self._add_item_to_sequencer(item))

        menu.addSeparator()

        # 그룹 이동 서브메뉴
        move_menu = menu.addMenu("📁 그룹으로 이동")
        assert move_menu is not None
        has_target = False
        for g in self._index.get("groups", []):
            gid: str = g.get("id", "")
            if gid == current_gid:
                continue
            gname: str = g.get("name", "그룹")
            act_move = move_menu.addAction(f"📁 {gname}")
            assert act_move is not None
            # 캡처 변수 바인딩 주의
            act_move.triggered.connect(
                lambda _checked=False, _fn=filename, _gid=gid:
                    self._move_item_to_group(_fn, _gid)
            )
            has_target = True
        if not has_target:
            no_target = move_menu.addAction("(이동 가능한 그룹 없음)")
            assert no_target is not None
            no_target.setEnabled(False)

        menu.addSeparator()

        act_remove = menu.addAction("🗑 즐겨찾기에서 제거")
        assert act_remove is not None
        act_remove.triggered.connect(lambda: self._remove_item(item))

    def _open_item(self, item: QTreeWidgetItem) -> None:
        data: dict[str, Any] = item.data(0, _ROLE) or {}
        path: str = data.get("path", "")
        if path and Path(path).exists():
            self.open_in_editor.emit(path)
        else:
            QMessageBox.warning(self, "파일 없음", f"파일을 찾을 수 없습니다:\n{path}")
            self._refresh_tree()

    def _add_item_to_sequencer(self, item: QTreeWidgetItem) -> None:
        data: dict[str, Any] = item.data(0, _ROLE) or {}
        path: str = data.get("path", "")
        if path and Path(path).exists():
            self.add_to_sequencer.emit(path)
        else:
            QMessageBox.warning(self, "파일 없음", f"파일을 찾을 수 없습니다:\n{path}")
            self._refresh_tree()

    def _remove_selected(self) -> None:
        item = self._tree.currentItem()
        if item:
            data: dict[str, Any] = item.data(0, _ROLE) or {}
            if data.get("type") == "item":
                self._remove_item(item)

    def _remove_item(self, item: QTreeWidgetItem) -> None:
        data: dict[str, Any] = item.data(0, _ROLE) or {}
        path: str = data.get("path", "")
        name: str = item.text(0)
        filename = Path(path).name if path else ""

        reply = QMessageBox.question(
            self,
            "즐겨찾기 제거",
            f"'{name}' 을(를) 즐겨찾기에서 제거하고 파일도 삭제하시겠습니까?\n\n"
            f"파일: {path}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # 인덱스에서 제거
        for g in self._index.get("groups", []):
            items: list[str] = g.get("items", [])
            if filename in items:
                items.remove(filename)
                break

        file_path = Path(path)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"즐겨찾기 파일 삭제: {file_path}")
            except OSError as e:
                QMessageBox.warning(self, "삭제 오류", str(e))
                return

        self._save_index()
        self._refresh_tree()


# ── 헬퍼 ─────────────────────────────────────────────────────────────────────

def _sanitize_filename(name: str) -> str:
    """파일명으로 사용할 수 없는 문자를 제거하고 안전한 이름을 반환한다."""
    for ch in r'\/:*?"<>|':
        name = name.replace(ch, "_")
    name = name.strip(". ")
    return name[:100]
