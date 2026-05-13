"""Event editor summary text helper regression tests."""

from __future__ import annotations

from types import SimpleNamespace

from macroflow.ui.editor_summary import _summary_text


def test_summary_text_matches_current_refresh_format_without_edited_tag() -> None:
    events = [
        SimpleNamespace(type="mouse_down"),
        SimpleNamespace(type="mouse_move"),
        SimpleNamespace(type="mouse_up"),
    ]

    assert _summary_text(events, raw_total=5, display_count=2, is_edited=False) == (
        "표시: 2개  (원본: 3개, raw: 5개)  |  이동: 1개"
    )


def test_summary_text_appends_edited_tag_when_macro_is_edited() -> None:
    events = [SimpleNamespace(type="mouse_move"), SimpleNamespace(type="mouse_move")]

    assert _summary_text(events, raw_total=2, display_count=1, is_edited=True) == (
        "표시: 1개  (원본: 2개, raw: 2개)  |  이동: 2개 [편집됨]"
    )
