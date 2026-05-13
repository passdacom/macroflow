"""Pure summary text helpers for the MacroFlow event editor."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def _summary_text(
    events: Sequence[Any],
    *,
    raw_total: int,
    display_count: int,
    is_edited: bool,
) -> str:
    """Return the event editor footer summary text."""
    total = len(events)
    move_count = sum(1 for event in events if event.type == "mouse_move")
    edited_tag = " [편집됨]" if is_edited else ""
    return (
        f"표시: {display_count}개  (원본: {total}개, raw: {raw_total}개)"
        f"  |  이동: {move_count}개{edited_tag}"
    )
