"""Data-only keyboard action authoring; never registers or sends native input."""
from __future__ import annotations

from collections.abc import Sequence

from macroflow.event_insertions import (
    IdFactory,
    _base_timestamp_ns,
    _default_id,
    _insert_and_shift_events,
)
from macroflow.types import AnyEvent, KeyEvent
from macroflow.ui.editor_keys import NAME_TO_VK

SHORTCUT_PRESETS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("복사 · Copy (Ctrl+C)", "c", ("ctrl",)),
    ("붙여넣기 · Paste (Ctrl+V)", "v", ("ctrl",)),
    ("클립보드 기록 (Win+V)", "v", ("lwin",)),
    ("취소 (Esc)", "esc", ()),
    ("잘라내기 (Ctrl+X)", "x", ("ctrl",)),
    ("전체 선택 (Ctrl+A)", "a", ("ctrl",)),
    ("실행 취소 (Ctrl+Z)", "z", ("ctrl",)),
    ("다시 실행 (Ctrl+Y)", "y", ("ctrl",)),
    ("저장 (Ctrl+S)", "s", ("ctrl",)),
    ("찾기 (Ctrl+F)", "f", ("ctrl",)),
    ("창 전환 (Alt+Tab)", "tab", ("alt",)),
    ("확인 (Enter)", "enter", ()),
    ("다음 항목 (Tab)", "tab", ()),
    ("이전 항목 (Shift+Tab)", "tab", ("shift",)),
)
_MODIFIER_VKS = {0x10, 0x11, 0x12, 0x5B, 0x5C, *range(0xA0, 0xA6)}


def insert_shortcut_events(
    events: Sequence[AnyEvent],
    insert_after_event_idx: int,
    key: str,
    modifiers: Sequence[str] = (),
    *,
    delay_ms: int = 1000,
    id_factory: IdFactory = _default_id,
) -> list[AnyEvent]:
    """Insert RAW downs then reverse ups with a 100ms hold, in one batch.

    Use the editor's explicit VK names, not layout-dependent character inference.
    Original recording events are never changed. Only the first down gets a delay
    override, like click insertion; later source timestamps retain their gaps.
    """
    if not -1 <= insert_after_event_idx < len(events):
        raise ValueError("삽입 위치가 범위를 벗어났습니다")
    if delay_ms < -1:
        raise ValueError("대기는 -1 또는 0 이상이어야 합니다")
    names = [name.lower() for name in (*modifiers, key)]
    if any(name not in NAME_TO_VK for name in names):
        raise ValueError("지원하지 않는 키 이름입니다")
    codes = [NAME_TO_VK[name] for name in names]
    if any(code not in _MODIFIER_VKS for code in codes[:-1]):
        raise ValueError("수식 키만 함께 선택할 수 있습니다")
    if len(set(codes)) != len(codes):
        raise ValueError("같은 키를 중복 선택할 수 없습니다")
    budget = max(delay_ms * 1_000_000, 1_000_000)
    start = _base_timestamp_ns(events, insert_after_event_idx) + budget
    keys = list(zip(names, codes, strict=True))
    added: list[AnyEvent] = []
    for event_type, pairs, timestamp in (
        ("key_down", keys, start),
        ("key_up", list(reversed(keys)), start + 100_000_000),
    ):
        for name, code in pairs:
            added.append(KeyEvent(
                id=id_factory(), type=event_type, timestamp_ns=timestamp,
                key=name, vk_code=code,
                delay_override_ms=delay_ms if not added and delay_ms >= 0 else None,
            ))
    return _insert_and_shift_events(
        events, insert_after_event_idx, added, budget + 100_000_000,
    )
