"""Atomic persistence for the favorites index.

The UI owns index mutation semantics; this module only guarantees that a failed
serialization or filesystem write cannot truncate the last valid index file.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any


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
