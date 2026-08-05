"""Favorites batch action helper tests.

These tests intentionally avoid importing PyQt. GitHub's Ubuntu runner does not
provide all Qt shared libraries (for example libEGL), so deterministic batch
index mutations live in a pure helper module.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from PyQt6.QtWidgets import QMessageBox

from macroflow.ui.favorites import FavoritesWidget
from macroflow.ui.favorites_batch import (
    delete_favorite_paths,
    move_filenames_to_group,
    remove_filenames_from_groups,
    unique_filenames,
)


def _index() -> dict[str, Any]:
    return {
        "groups": [
            {"id": "default", "name": "기본", "items": ["a.macroflow", "b.macroflow"]},
            {"id": "target", "name": "Target", "items": ["c.macroflow"]},
        ]
    }


def test_unique_filenames_preserves_selection_order_and_drops_duplicates() -> None:
    assert unique_filenames(
        [
            Path("/tmp/a.macroflow"),
            Path("/other/b.macroflow"),
            Path("/duplicate/a.macroflow"),
        ]
    ) == ["a.macroflow", "b.macroflow"]


def test_move_filenames_to_group_removes_from_sources_and_appends_to_target() -> None:
    index = _index()

    move_filenames_to_group(index, ["a.macroflow", "b.macroflow"], "target")

    assert index["groups"][0]["items"] == []
    assert index["groups"][1]["items"] == [
        "c.macroflow",
        "a.macroflow",
        "b.macroflow",
    ]


def test_move_filenames_to_group_does_not_duplicate_existing_target_items() -> None:
    index = _index()

    move_filenames_to_group(index, ["b.macroflow", "c.macroflow"], "target")

    assert index["groups"][0]["items"] == ["a.macroflow"]
    assert index["groups"][1]["items"] == ["c.macroflow", "b.macroflow"]


def test_move_to_missing_group_is_a_noop() -> None:
    index = _index()
    before = json.loads(json.dumps(index))

    move_filenames_to_group(index, ["a.macroflow"], "deleted-group")

    assert index == before


def test_remove_filenames_from_groups_removes_batch_from_every_group() -> None:
    index = _index()

    remove_filenames_from_groups(index, {"a.macroflow", "c.macroflow"})

    assert index["groups"][0]["items"] == ["b.macroflow"]
    assert index["groups"][1]["items"] == []


def test_atomic_index_save_failure_preserves_previous_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from macroflow import favorites_index

    target = tmp_path / "_index.json"
    previous = b'{"version": 1, "groups": [{"id": "keep"}]}\n'
    target.write_bytes(previous)

    def fail_after_partial_write(data: object, stream: object, **kwargs: object) -> None:
        del data, kwargs
        stream.write("{")  # type: ignore[attr-defined]
        stream.flush()  # type: ignore[attr-defined]
        raise OSError("injected write failure")

    monkeypatch.setattr(json, "dump", fail_after_partial_write)

    with pytest.raises(OSError, match="injected write failure"):
        favorites_index.save_index({"version": 1, "groups": []}, target)

    assert target.read_bytes() == previous
    assert list(tmp_path.glob("._index.json.*.tmp")) == []


def test_partial_batch_delete_reports_only_successful_deletions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    first.write_text("a", encoding="utf-8")
    second.write_text("b", encoding="utf-8")
    original_unlink = Path.unlink

    def selective_unlink(path: Path, missing_ok: bool = False) -> None:
        if path == second:
            raise OSError("injected delete failure")
        original_unlink(path, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", selective_unlink)

    deleted, failures = delete_favorite_paths([first, second])

    assert deleted == {"a.json"}
    assert [path for path, _error in failures] == [second]
    assert not first.exists()
    assert second.exists()


def _configured_widget(tmp_path: Path, qtbot) -> FavoritesWidget:
    widget = FavoritesWidget()
    qtbot.addWidget(widget)
    widget.set_favorites_dir(tmp_path)
    (tmp_path / "a.json").write_text("{}", encoding="utf-8")
    widget._index = {
        "version": 1,
        "groups": [
            {"id": "default", "name": "기본", "expanded": True, "items": ["a.json"]},
            {"id": "target", "name": "대상", "expanded": True, "items": []},
        ],
    }
    widget._refresh_tree()
    return widget


def test_move_save_failure_restores_durable_index_and_ui(
    tmp_path: Path, qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    widget = _configured_widget(tmp_path, qtbot)
    original = copy.deepcopy(widget._index)
    warnings: list[tuple[object, ...]] = []
    monkeypatch.setattr(
        "macroflow.ui.favorites.save_index",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    monkeypatch.setattr(
        "macroflow.ui.favorites.QMessageBox.warning",
        lambda *args: warnings.append(args),
    )

    widget._move_item_to_group("a.json", "target")

    assert widget._index == original
    assert widget._summary.text() == "즐겨찾기 1개"
    assert warnings


def test_rename_save_failure_rolls_back_file_index_and_ui(
    tmp_path: Path, qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    widget = _configured_widget(tmp_path, qtbot)
    original = copy.deepcopy(widget._index)
    item = widget._tree.topLevelItem(0).child(0)
    monkeypatch.setattr(
        "macroflow.ui.favorites.QInputDialog.getText",
        lambda *_args, **_kwargs: ("renamed", True),
    )
    monkeypatch.setattr(
        "macroflow.ui.favorites.save_index",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    monkeypatch.setattr("macroflow.ui.favorites.QMessageBox.warning", lambda *_args: None)

    widget._rename_item(item)

    assert (tmp_path / "a.json").exists()
    assert not (tmp_path / "renamed.json").exists()
    assert widget._index == original
    assert widget._summary.text() == "즐겨찾기 1개"


def test_delete_save_failure_restores_files_index_and_ui(
    tmp_path: Path, qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    widget = _configured_widget(tmp_path, qtbot)
    original = copy.deepcopy(widget._index)
    monkeypatch.setattr(
        "macroflow.ui.favorites.QMessageBox.question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "macroflow.ui.favorites.save_index",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    monkeypatch.setattr("macroflow.ui.favorites.QMessageBox.warning", lambda *_args: None)

    widget._remove_paths([tmp_path / "a.json"])

    assert (tmp_path / "a.json").exists()
    assert widget._index == original
    assert widget._summary.text() == "즐겨찾기 1개"


def test_group_rename_and_delete_save_failures_restore_index_and_ui(
    tmp_path: Path, qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    widget = _configured_widget(tmp_path, qtbot)
    original = copy.deepcopy(widget._index)
    monkeypatch.setattr(
        "macroflow.ui.favorites.save_index",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    monkeypatch.setattr("macroflow.ui.favorites.QMessageBox.warning", lambda *_args: None)
    monkeypatch.setattr(
        "macroflow.ui.favorites.QInputDialog.getText",
        lambda *_args, **_kwargs: ("새 이름", True),
    )

    widget._rename_group("target")
    assert widget._index == original
    assert widget._tree.topLevelItem(1).text(0).startswith("📁  대상")

    monkeypatch.setattr(
        "macroflow.ui.favorites.QMessageBox.question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    widget._delete_group("target")
    assert widget._index == original
    assert widget._tree.topLevelItemCount() == 2


def test_drag_save_failure_restores_index_tree_and_does_not_retry_during_refresh(
    tmp_path: Path, qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    widget = _configured_widget(tmp_path, qtbot)
    original = copy.deepcopy(widget._index)
    save_attempts = 0

    def fail_save(*_args, **_kwargs) -> None:
        nonlocal save_attempts
        save_attempts += 1
        raise OSError("disk full")

    monkeypatch.setattr("macroflow.ui.favorites.save_index", fail_save)
    monkeypatch.setattr("macroflow.ui.favorites.QMessageBox.warning", lambda *_args: None)
    default_item = widget._tree.topLevelItem(0)
    target_item = widget._tree.topLevelItem(1)
    moved = default_item.takeChild(0)
    target_item.addChild(moved)

    widget._on_item_moved()

    assert widget._index == original
    assert widget._tree.topLevelItem(0).childCount() == 1
    assert widget._tree.topLevelItem(1).childCount() == 0
    assert save_attempts == 1


def test_rename_rollback_failure_reports_degraded_state_truthfully(
    tmp_path: Path, qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    widget = _configured_widget(tmp_path, qtbot)
    item = widget._tree.topLevelItem(0).child(0)
    critical_messages: list[str] = []
    monkeypatch.setattr(
        "macroflow.ui.favorites.QInputDialog.getText",
        lambda *_args, **_kwargs: ("renamed", True),
    )
    monkeypatch.setattr(
        "macroflow.ui.favorites.save_index",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    original_replace = Path.replace

    def fail_rollback(path: Path, target: Path) -> Path:
        if path.name == "renamed.json":
            raise OSError("rollback denied")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_rollback)
    monkeypatch.setattr("macroflow.ui.favorites.QMessageBox.warning", lambda *_args: None)
    monkeypatch.setattr(
        "macroflow.ui.favorites.QMessageBox.critical",
        lambda _parent, _title, message: critical_messages.append(message),
    )

    widget._rename_item(item)

    assert not (tmp_path / "a.json").exists()
    assert (tmp_path / "renamed.json").exists()
    assert critical_messages
    assert "완전히 복원하지 못했습니다" in critical_messages[0]
    assert "복원했습니다" not in critical_messages[0]


def test_delete_rollback_failure_preserves_staging_and_reports_degraded_state(
    tmp_path: Path, qtbot, monkeypatch: pytest.MonkeyPatch
) -> None:
    widget = _configured_widget(tmp_path, qtbot)
    critical_messages: list[str] = []
    monkeypatch.setattr(
        "macroflow.ui.favorites.QMessageBox.question",
        lambda *_args, **_kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "macroflow.ui.favorites.save_index",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )
    original_replace = Path.replace

    def fail_staging_rollback(path: Path, target: Path) -> Path:
        if path.name.startswith(".a.json.delete-"):
            raise OSError("rollback denied")
        return original_replace(path, target)

    monkeypatch.setattr(Path, "replace", fail_staging_rollback)
    monkeypatch.setattr("macroflow.ui.favorites.QMessageBox.warning", lambda *_args: None)
    monkeypatch.setattr(
        "macroflow.ui.favorites.QMessageBox.critical",
        lambda _parent, _title, message: critical_messages.append(message),
    )

    widget._remove_paths([tmp_path / "a.json"])

    assert not (tmp_path / "a.json").exists()
    assert len(list(tmp_path.glob(".a.json.delete-*.tmp"))) == 1
    assert critical_messages
    assert "완전히 복원하지 못했습니다" in critical_messages[0]
    assert ".delete-*.tmp" in critical_messages[0]
    assert "복원했습니다" not in critical_messages[0]
