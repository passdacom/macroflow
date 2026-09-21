"""Selections are complete raw gestures, not arbitrary display-row hulls."""
import pytest

from macroflow.types import KeyEvent, MouseMoveEvent


def test_complete_chord_required_and_discontiguous_rejected():
    from macroflow.ui.editor_selection import resolve_selection
    events = [KeyEvent(id=str(i), type=kind, timestamp_ns=i, key=str(vk), vk_code=vk)
              for i, (kind, vk) in enumerate([
                  ("key_down", 17), ("key_down", 67), ("key_up", 67), ("key_up", 17)])]
    rows = [[0, 3], [1, 2]]
    assert resolve_selection(events, rows, [0, 1]) == (0, 4)
    for selected in ([0], [1], [], [2], [-1], [1, 0, 1]):
        with pytest.raises(ValueError):
            resolve_selection(events, rows, selected)


def test_hidden_moves_retained_inside_complete_range():
    from macroflow.ui.editor_selection import resolve_selection
    events = [KeyEvent(id="d", type="key_down", timestamp_ns=0, key="a", vk_code=65),
              MouseMoveEvent(id="m", type="mouse_move", timestamp_ns=1, x_ratio=.1, y_ratio=.1),
              KeyEvent(id="u", type="key_up", timestamp_ns=2, key="a", vk_code=65)]
    assert resolve_selection(events, [[0, 2]], [0]) == (0, 3)


def test_orphan_release_is_not_an_independent_action():
    from macroflow.ui.editor_selection import resolve_selection
    events = [KeyEvent(id="up", type="key_up", timestamp_ns=0, key="ctrl", vk_code=17)]
    with pytest.raises(ValueError):
        resolve_selection(events, [[0]], [0])
