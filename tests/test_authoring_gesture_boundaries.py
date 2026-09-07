"""User authoring sequences must not split a held shortcut gesture."""
from __future__ import annotations

import pytest

from macroflow.event_insertions import _selected_insert_after_event_idx
from tests.test_shortcut_insertion import QT_SETUP, run_qt


@pytest.mark.parametrize('selected', [[0], [1], [0, 1]])
def test_insertion_after_either_chord_row_waits_for_modifier_release(selected):
    # Ctrl-down C-down C-up Ctrl-up; both rows belong to one held gesture.
    assert _selected_insert_after_event_idx([[0, 3], [1, 2]], selected, 4) == 3


def test_overlapping_gesture_boundary_expands_to_fixed_point():
    assert _selected_insert_after_event_idx([[0, 3], [2, 5], [4, 7]], [0], 8) == 7
    assert _selected_insert_after_event_idx([[0, 1], [2, 3]], [0], 4) == 1


def test_click_add_starts_capture_without_dialog_and_is_single_undo():
    run_qt(QT_SETUP + '''
editor = EventEditorWidget(); editor.load_macro(blank())
def no_dialog(self): raise AssertionError("click add opened a dialog")
QDialog.exec = no_dialog
started, ended = [], []
editor.f6_capture_started.connect(lambda: started.append(True))
editor.f6_capture_ended.connect(lambda: ended.append(True))
editor.insert_click_action()
assert editor.is_f6_capture_active() and editor.current_macro().events == []
assert editor.consume_f6_capture(.2, .3, "#123456")
events = editor.current_macro().events
assert [(e.type, e.button) for e in events] == [("mouse_down", "left"), ("mouse_up", "left")]
assert all(e.x_ratio == .2 and e.y_ratio == .3 for e in events)
assert events[0].recorded_color == "#123456"
assert events[0].delay_override_ms == 1000
assert started == ended == [True]
assert not editor.consume_f6_capture(.4, .5, "#654321")
assert len(editor._undo_stack) == 1
editor._undo(); assert editor.current_macro().events == []
editor._redo(); assert editor.current_macro().events == events
editor.insert_click_action(); editor.cancel_f6_capture()
assert not editor.consume_f6_capture(.4, .5, "#654321")
assert editor.current_macro().events == events
''')


def test_click_capture_rejects_busy_disabled_and_changed_document():
    run_qt(QT_SETUP + '''
from PyQt6.QtWidgets import QMessageBox
QMessageBox.warning = lambda *a: None
class Host(QWidget):
    busy = False
    def _dispatch_editor_insert(self, callback):
        if not self.busy: callback()
host = Host(); editor = EventEditorWidget(host)
def no_dialog(self): raise AssertionError("click add opened a dialog")
QDialog.exec = no_dialog
for mode in ("busy", "disabled", "reload", "edit"):
    host.busy = False; editor.setEnabled(True); editor.load_macro(blank())
    editor.insert_click_action()
    assert editor.is_f6_capture_active()
    if mode == "busy": host.busy = True
    if mode == "disabled": editor.setEnabled(False)
    if mode == "reload": editor.load_macro(blank())
    if mode == "edit": editor.macro_changed.emit(editor.current_macro())
    editor.consume_f6_capture(.2, .3, "#123456")
    assert editor.current_macro().events == [], mode
    assert not editor._undo_stack, mode
host.busy = True; editor.setEnabled(True)
editor.insert_click_action(); assert not editor.is_f6_capture_active()
''')


def test_copy_click_paste_is_balanced_after_selecting_inner_key(tmp_path):
    run_qt(QT_SETUP + f'''
from macroflow.macro_file import save, load
from macroflow.types import KeyEvent, MouseButtonEvent
editor = EventEditorWidget(); editor.load_macro(blank())
QDialog.exec = lambda self: (_ for _ in ()).throw(AssertionError("unexpected click dialog"))
def click(x):
    editor.insert_click_action()
    assert editor.consume_f6_capture(x, .3, "#123456")
def shortcut(index):
    def accept(self):
        self.preset.setCurrentIndex(index)
        return QDialog.DialogCode.Accepted
    ShortcutDialog.exec = accept
    editor.insert_shortcut_action()
click(.1); shortcut(0)
# A user selects the visually last C row, not the enclosing Ctrl row.
editor._table.selectRow(len(editor._rows) - 1)
click(.5); shortcut(1)
macro = editor.current_macro()
save(macro, {str(tmp_path / 'copy-paste.json')!r})
macro = load({str(tmp_path / 'copy-paste.json')!r})
held = set(); clicks = []
for event in macro.events:
    if isinstance(event, KeyEvent):
        if event.type == "key_down": held.add(event.vk_code)
        else: held.discard(event.vk_code)
    if isinstance(event, MouseButtonEvent) and event.type == "mouse_down":
        assert not held, (event.x_ratio, held)
        clicks.append(event.x_ratio)
assert clicks == [.1, .5] and not held
# Execute the persisted sequence through the real player with a fake OS boundary.
import dataclasses
from macroflow import player
runtime_held, runtime_clicks, errors = set(), [], []
def key(vk, is_down):
    if is_down: runtime_held.add(vk)
    else: runtime_held.discard(vk)
def mouse(x, y, button, down):
    if down:
        assert not runtime_held, runtime_held
        runtime_clicks.append(x)
player.send_key = key
player.send_mouse_button = mouse
player.send_mouse_move = lambda *a: None
player.ratio_to_pixel = lambda x, y: (int(x * 1000), int(y * 1000))
macro = dataclasses.replace(macro, events=[
    dataclasses.replace(e, timestamp_ns=0, delay_override_ms=0) for e in macro.events])
player.play(macro, on_error=errors.append)
player._playback_thread.join(3)
assert not player.is_playing()
assert not errors and not runtime_held and runtime_clicks == [100, 500]
player.stop()
''')
