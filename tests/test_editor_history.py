"""Editor undo/history pure helper tests."""

from __future__ import annotations

import subprocess
import sys

from macroflow.types import MacroData, MacroMeta, MacroSettings, MouseButtonEvent
from macroflow.ui.editor_history import copy_events, macro_with_events


def _event(event_id: str, x_ratio: float = 0.1) -> MouseButtonEvent:
    return MouseButtonEvent(
        id=event_id,
        type="mouse_down",
        timestamp_ns=1_000_000_000,
        x_ratio=x_ratio,
        y_ratio=0.2,
        button="left",
    )


def _macro(events: list[MouseButtonEvent], *, is_edited: bool = False) -> MacroData:
    return MacroData(
        meta=MacroMeta(
            version="1.0",
            app_version="1.2.0",
            created_at="2026-05-12T00:00:00",
            screen_width=1920,
            screen_height=1080,
            dpi_scale=1.0,
        ),
        settings=MacroSettings(),
        raw_events=[_event("raw")],
        events=events,
        is_edited=is_edited,
    )


def test_editor_history_import_does_not_eagerly_import_pyqt_widgets() -> None:
    code = "import sys; from macroflow.ui.editor_history import copy_events; print(copy_events.__name__); print('PyQt6' in sys.modules)"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["copy_events", "False"]


def test_copy_events_returns_deep_copy_for_undo_snapshot() -> None:
    original = [_event("a")]
    copied = copy_events(original)

    assert copied == original
    assert copied is not original
    assert copied[0] is not original[0]

    copied[0].x_ratio = 0.9
    assert original[0].x_ratio == 0.1


def test_macro_with_events_preserves_metadata_settings_and_raw_events() -> None:
    old_events = [_event("old")]
    new_events = [_event("new")]
    macro = _macro(old_events)

    updated = macro_with_events(macro, new_events)

    assert updated is not macro
    assert updated.meta is macro.meta
    assert updated.settings is macro.settings
    assert updated.raw_events is macro.raw_events
    assert updated.events == new_events
    assert updated.is_edited is True
    assert macro.events == old_events
    assert macro.is_edited is False
