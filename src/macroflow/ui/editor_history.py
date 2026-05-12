"""Undo/history helpers for the MacroFlow event editor.

This module is intentionally PyQt-free. It keeps snapshot/copy semantics for
editor undo/redo testable without loading the GUI runtime.
"""

from __future__ import annotations

import copy

from macroflow.types import AnyEvent, MacroData


def copy_events(events: list[AnyEvent]) -> list[AnyEvent]:
    """Return a deep copy suitable for undo/redo snapshots."""
    return copy.deepcopy(events)


def macro_with_events(macro: MacroData, events: list[AnyEvent], *, is_edited: bool = True) -> MacroData:
    """Return a MacroData copy with a replaced event list.

    Metadata, settings, and raw events are intentionally preserved by reference,
    matching the editor's previous _apply_events behavior.
    """
    return MacroData(
        meta=macro.meta,
        settings=macro.settings,
        raw_events=macro.raw_events,
        events=events,
        is_edited=is_edited,
    )
