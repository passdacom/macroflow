"""FavoritesWidget multi-selection batch action tests."""

# ruff: noqa: E402,I001

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from typing import Any

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QMessageBox, QTreeWidgetItem  # noqa: E402

from macroflow.ui.favorites import FavoritesWidget  # noqa: E402


_APP: QApplication | None = None


def _ensure_real_qt() -> None:
    """Recover real PyQt modules if earlier source-level tests left fakes in sys.modules."""
    global QApplication, QMessageBox, QTreeWidgetItem, FavoritesWidget
    if isinstance(QApplication, type):
        return
    for module_name in (
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "macroflow.ui.favorites",
    ):
        sys.modules.pop(module_name, None)
    qtwidgets = importlib.import_module("PyQt6.QtWidgets")
    QApplication = qtwidgets.QApplication
    QMessageBox = qtwidgets.QMessageBox
    QTreeWidgetItem = qtwidgets.QTreeWidgetItem
    FavoritesWidget = importlib.import_module("macroflow.ui.favorites").FavoritesWidget


def _app() -> QApplication:
    global _APP
    _ensure_real_qt()
    app = QApplication.instance()
    if app is not None:
        _APP = app
    elif _APP is None:
        _APP = QApplication([])
    return _APP


def _write_favorites(directory: Path, filenames: list[str]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for filename in filenames:
        (directory / filename).write_text("{}", encoding="utf-8")


def _default_group(widget: FavoritesWidget) -> QTreeWidgetItem:
    root = widget._tree.invisibleRootItem()
    assert root is not None
    group = root.child(0)
    assert group is not None
    return group


def _child_by_filename(group: QTreeWidgetItem, filename: str) -> QTreeWidgetItem:
    for idx in range(group.childCount()):
        child = group.child(idx)
        assert child is not None
        if Path(str(child.data(0, widget_role_path_key()))).name == filename:
            return child
    raise AssertionError(f"missing child {filename}")


def widget_role_path_key() -> Any:
    from macroflow.ui.favorites import _ROLE

    return _ROLE


def _select_children(group: QTreeWidgetItem, filenames: set[str]) -> None:
    for idx in range(group.childCount()):
        child = group.child(idx)
        assert child is not None
        data = child.data(0, widget_role_path_key()) or {}
        child.setSelected(Path(str(data.get("path", ""))).name in filenames)


def test_selected_favorites_are_emitted_to_sequencer(tmp_path: Path) -> None:
    _app()
    _write_favorites(tmp_path, ["a.json", "b.json", "c.json"])
    widget = FavoritesWidget()
    widget.set_favorites_dir(tmp_path)
    emitted: list[str] = []
    widget.add_to_sequencer.connect(emitted.append)

    _select_children(_default_group(widget), {"a.json", "c.json"})
    widget._add_selected_to_sequencer()

    assert {Path(path).name for path in emitted} == {"a.json", "c.json"}


def test_selected_favorites_move_to_target_group(tmp_path: Path) -> None:
    _app()
    _write_favorites(tmp_path, ["a.json", "b.json", "c.json"])
    widget = FavoritesWidget()
    widget.set_favorites_dir(tmp_path)
    widget._index["groups"].append({
        "id": "target",
        "name": "Target",
        "expanded": True,
        "items": [],
    })
    widget._save_index()
    widget._refresh_tree()

    _select_children(_default_group(widget), {"a.json", "b.json"})
    widget._move_selected_to_group("target")

    target = widget._find_group("target")
    assert target is not None
    assert target["items"] == ["a.json", "b.json"]
    default = widget._find_group("default")
    assert default is not None
    assert "a.json" not in default["items"]
    assert "b.json" not in default["items"]
    assert "c.json" in default["items"]


def test_selected_favorites_remove_with_single_confirmation(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _app()
    _write_favorites(tmp_path, ["a.json", "b.json", "c.json"])
    widget = FavoritesWidget()
    widget.set_favorites_dir(tmp_path)
    confirmations: list[str] = []

    def _yes(*args: object) -> QMessageBox.StandardButton:
        confirmations.append("yes")
        return QMessageBox.StandardButton.Yes

    monkeypatch.setattr(QMessageBox, "question", _yes)

    _select_children(_default_group(widget), {"a.json", "b.json"})
    widget._remove_selected()

    assert confirmations == ["yes"]
    assert not (tmp_path / "a.json").exists()
    assert not (tmp_path / "b.json").exists()
    assert (tmp_path / "c.json").exists()
    default = widget._find_group("default")
    assert default is not None
    assert default["items"] == ["c.json"]
