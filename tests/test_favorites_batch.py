"""Favorites batch action helper tests.

These tests intentionally avoid importing PyQt. GitHub's Ubuntu runner does not
provide all Qt shared libraries (for example libEGL), so deterministic batch
index mutations live in a pure helper module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

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
