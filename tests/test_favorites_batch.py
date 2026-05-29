"""Favorites batch action helper tests.

These tests intentionally avoid importing PyQt. GitHub's Ubuntu runner does not
provide all Qt shared libraries (for example libEGL), so deterministic batch
index mutations live in a pure helper module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from macroflow.ui.favorites_batch import (
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


def test_remove_filenames_from_groups_removes_batch_from_every_group() -> None:
    index = _index()

    remove_filenames_from_groups(index, {"a.macroflow", "c.macroflow"})

    assert index["groups"][0]["items"] == ["b.macroflow"]
    assert index["groups"][1]["items"] == []
