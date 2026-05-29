"""Pure helpers for Favorites batch actions.

The Favorites UI itself is PyQt-based, but the index mutations should remain
small, deterministic, and testable on Linux CI without loading Qt libraries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def unique_filenames(paths: list[Path]) -> list[str]:
    """Return path names in first-seen order, dropping duplicates and blanks."""
    filenames: list[str] = []
    seen: set[str] = set()
    for path in paths:
        if path.name and path.name not in seen:
            filenames.append(path.name)
            seen.add(path.name)
    return filenames


def move_filenames_to_group(
    index: dict[str, Any],
    filenames: list[str],
    target_gid: str,
) -> None:
    """Move filenames to a target group in-place without duplicating items."""
    filename_set = set(filenames)
    if not filename_set:
        return

    target: dict[str, Any] | None = None
    for group in index.get("groups", []):
        items: list[str] = group.get("items", [])
        if group.get("id") == target_gid:
            target = group
            continue
        group["items"] = [filename for filename in items if filename not in filename_set]

    if target is None:
        return

    existing: list[str] = target.get("items", [])
    target["items"] = existing + [
        filename for filename in filenames if filename not in existing
    ]


def remove_filenames_from_groups(index: dict[str, Any], filenames: set[str]) -> None:
    """Remove filenames from every group in-place."""
    if not filenames:
        return
    for group in index.get("groups", []):
        items: list[str] = group.get("items", [])
        group["items"] = [filename for filename in items if filename not in filenames]
