"""Validation, damaged-index preservation, and atomic favorites persistence.

The UI owns index mutation and recovery presentation. Backups retain exact
invalid bytes before recovery can replace the index.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def validate_index(data: object) -> dict[str, Any]:
    """Reject malformed metadata before the UI can consume or rewrite it."""
    if not isinstance(data, dict) or not isinstance(data.get("groups"), list):
        raise ValueError("favorites index must contain a groups list")
    if type(data.get("version", 1)) is not int or data.get("version", 1) != 1:
        raise ValueError("unsupported favorites index version")
    ids: set[str] = set()
    for group in data["groups"]:
        if (
            not isinstance(group, dict)
            or not isinstance(group.get("id"), str)
            or not group["id"]
            or group["id"] in ids
            or not isinstance(group.get("name"), str)
            or not isinstance(group.get("expanded", True), bool)
            or not isinstance(group.get("items"), list)
        ):
            raise ValueError("invalid or duplicate favorites group")
        ids.add(group["id"])
        for item in group["items"]:
            if (
                not isinstance(item, str) or not item
                or "\\" in item or ":" in item
                or item.startswith("/")
                or any(part in ("", ".", "..") for part in item.split("/"))
                or item == "_index.json"
            ):
                raise ValueError("invalid favorites item path")
    return data


def backup_invalid_index(path: Path, payload: bytes) -> Path:
    """Durably preserve exact damaged bytes under a non-macro backup name."""
    with tempfile.NamedTemporaryFile(
        mode="wb", prefix=f"{path.name}.corrupt-", suffix=".bak",
        dir=path.parent, delete=False,
    ) as stream:
        backup = Path(stream.name)
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    if backup.read_bytes() != payload:
        raise OSError("favorites index backup readback failed")
    return backup


def save_index(index: Mapping[str, Any], path: Path) -> None:
    """Serialize *index* and atomically replace *path* after a durable temp write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(index, temp_file, ensure_ascii=False, indent=2, allow_nan=False)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, path)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise
