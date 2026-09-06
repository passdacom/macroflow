"""Shortcut authoring is data-only; Qt checks run outside fake-module tests."""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap

import pytest

from macroflow.types import KeyEvent


def test_chord_order_timing_ids_and_existing_events():
    from macroflow.ui.shortcut_events import insert_shortcut_events

    original = [KeyEvent(id="old", type="key_up", timestamp_ns=10,
                         key="a", vk_code=65),
                KeyEvent(id="tail", type="key_down", timestamp_ns=100,
                         key="b", vk_code=66)]
    ids = iter([f"new{i}" for i in range(6)])
    result = insert_shortcut_events(original, 0, "v", ("ctrl", "shift"),
                                    delay_ms=1000, id_factory=lambda: next(ids))
    added = result[1:-1]
    assert [(e.type, e.vk_code) for e in added] == [
        ("key_down", 17), ("key_down", 16), ("key_down", 86),
        ("key_up", 86), ("key_up", 16), ("key_up", 17)]
    assert [e.id for e in added] == [f"new{i}" for i in range(6)]
    assert added[0].timestamp_ns == 1_000_000_010
    assert added[-1].timestamp_ns == 1_100_000_010
    assert result[-1].timestamp_ns == 1_100_000_100
    assert [e.delay_override_ms for e in added] == [1000, None, None, None, None, None]
    assert original[-1].timestamp_ns == 100
    assert result[0] is original[0]


@pytest.mark.parametrize("key,modifiers", [("", ()), ("unknown", ()),
    ("c", ("bogus",)), ("c", ("ctrl", "control")), ("ctrl", ("ctrl",))])
def test_invalid_chords_rejected(key, modifiers):
    from macroflow.ui.shortcut_events import insert_shortcut_events
    with pytest.raises(ValueError):
        insert_shortcut_events([], -1, key, modifiers)


@pytest.mark.parametrize("delay", [-1, 0, 1000])
def test_all_supported_single_keys_and_presets(delay):
    from macroflow.ui.editor_keys import NAME_TO_VK
    from macroflow.ui.shortcut_events import SHORTCUT_PRESETS, insert_shortcut_events
    for key, vk in NAME_TO_VK.items():
        events = insert_shortcut_events([], -1, key, (), delay_ms=delay)
        assert [e.vk_code for e in events] == [vk, vk]
        assert [e.type for e in events] == ["key_down", "key_up"]
        assert events[0].delay_override_ms == (None if delay == -1 else delay)
        assert events[1].timestamp_ns - events[0].timestamp_ns == 100_000_000
        assert len({e.id for e in events}) == 2
    chords = {(key, modifiers) for _, key, modifiers in SHORTCUT_PRESETS}
    assert {( "c", ("ctrl",)), ("v", ("ctrl",)), ("v", ("lwin",)), ("esc", ())} <= chords
    for _, key, modifiers in SHORTCUT_PRESETS:
        assert insert_shortcut_events([], -1, key, modifiers, delay_ms=delay)


def run_qt(script):
    result = subprocess.run([sys.executable, "-c", textwrap.dedent(script)],
        env={**os.environ, "QT_QPA_PLATFORM": "offscreen"},
        capture_output=True, text=True, timeout=40)
    assert result.returncode == 0, result.stdout + result.stderr


QT_SETUP = '''
from PyQt6.QtWidgets import QApplication, QDialog, QWidget
from macroflow.types import MacroData, MacroMeta, MacroSettings
from macroflow.ui.editor import EventEditorWidget
from macroflow.ui.shortcut_dialog import ShortcutDialog
app = QApplication([])
def blank():
    return MacroData(meta=MacroMeta(version="1.0", app_version="1.9.0",
        created_at="2026-09-06T00:00:00", screen_width=1920, screen_height=1080,
        dpi_scale=1.0), settings=MacroSettings(), events=[], raw_events=[])
'''


def test_editor_insert_undo_redo_selection_roundtrip(tmp_path):
    run_qt(QT_SETUP + f'''
from macroflow.macro_file import save, load
editor = EventEditorWidget()
editor.load_macro(blank())
changes = []
editor.macro_changed.connect(changes.append)
assert editor._act_insert_shortcut.isEnabled()
assert editor._act_insert_shortcut.shortcut().isEmpty()
def accept(self):
    self.preset.setCurrentIndex(0)
    return QDialog.DialogCode.Accepted
ShortcutDialog.exec = accept
editor._act_insert_shortcut.trigger()
first = editor.current_macro()
assert [(e.type, e.key) for e in first.events] == [
    ("key_down", "ctrl"), ("key_down", "c"), ("key_up", "c"), ("key_up", "ctrl")]
assert first.raw_events == [] and first.is_edited
assert len(changes) == 1 and len(editor._undo_stack) == 1
editor._undo()
assert editor.current_macro().events == []
editor._redo()
assert editor.current_macro().events == first.events
editor._table.clearSelection()
editor.insert_shortcut_action()
assert [e.id for e in editor.current_macro().events[:4]] == [e.id for e in first.events]
editor._table.selectRow(0)
anchor = editor._selected_insert_after_event_idx()
before = list(editor.current_macro().events)
editor.insert_shortcut_action()
after = editor.current_macro().events
assert [e.id for e in after[:anchor+1]] == [e.id for e in before[:anchor+1]]
assert [e.id for e in after[anchor+5:]] == [e.id for e in before[anchor+1:]]
save(editor.current_macro(), {str(tmp_path / 'shortcuts.json')!r})
assert load({str(tmp_path / 'shortcuts.json')!r}) == editor.current_macro()
''')


def test_every_preset_and_custom_chord_roundtrips(tmp_path):
    run_qt(QT_SETUP + f'''
from macroflow.ui.shortcut_events import SHORTCUT_PRESETS
from macroflow.ui.editor_keys import NAME_TO_VK
from macroflow.macro_file import save, load
editor = EventEditorWidget()
editor.load_macro(blank())
for index in range(len(SHORTCUT_PRESETS) + 1):
    def accept(self):
        self.preset.setCurrentIndex(index)
        if index == len(SHORTCUT_PRESETS):
            self.key.setCurrentText("f6")
            for name, box in self.modifiers.items():
                box.setChecked(name in ("ctrl", "alt", "shift", "lwin"))
        return QDialog.DialogCode.Accepted
    ShortcutDialog.exec = accept
    editor._table.clearSelection()
    count = len(editor.current_macro().events)
    editor.insert_shortcut_action()
    added = editor.current_macro().events[count:]
    if index < len(SHORTCUT_PRESETS):
        _, key, modifiers = SHORTCUT_PRESETS[index]
    else:
        key, modifiers = "f6", ("ctrl", "alt", "shift", "lwin")
    names = [*modifiers, key]
    assert [e.key for e in added] == names + list(reversed(names))
    assert [e.vk_code for e in added] == [NAME_TO_VK[n] for n in names + list(reversed(names))]
    assert len(set(e.id for e in editor.current_macro().events)) == len(editor.current_macro().events)
save(editor.current_macro(), {str(tmp_path / 'all-shortcuts.json')!r})
assert load({str(tmp_path / 'all-shortcuts.json')!r}) == editor.current_macro()
''')


def test_dialog_custom_no_capture_and_cancel_runtime_stale_guards():
    run_qt(QT_SETUP + '''
from PyQt6.QtWidgets import QComboBox, QCheckBox
class Host(QWidget):
    busy = False
    def _dispatch_editor_insert(self, callback):
        if not self.busy:
            callback()
host = Host()
editor = EventEditorWidget(host)
editor.load_macro(blank())
dialog = ShortcutDialog(editor)
assert not dialog.key.isEditable()
assert dialog.delay.value() == 1000
dialog.key.setCurrentText("f6")
dialog.modifiers["ctrl"].setChecked(False)
dialog.modifiers["lwin"].setChecked(True)
assert dialog.shortcut() == ("f6", ("lwin",), 1000)
for mode in ("cancel", "reload", "edit", "disabled", "busy"):
    host.busy = False
    editor.setEnabled(True)
    editor.load_macro(blank())
    def exec_dialog(self):
        if mode == "reload": editor.load_macro(blank())
        if mode == "edit": editor.macro_changed.emit(editor.current_macro())
        if mode == "disabled": editor.setEnabled(False)
        if mode == "busy": host.busy = True
        return QDialog.DialogCode.Rejected if mode == "cancel" else QDialog.DialogCode.Accepted
    ShortcutDialog.exec = exec_dialog
    editor.insert_shortcut_action()
    assert editor.current_macro().events == [], mode
    assert len(editor._undo_stack) == 0, mode
# Runtime gating happens before a dialog opens, too.
def unexpected(self): raise AssertionError("dialog opened during runtime")
ShortcutDialog.exec = unexpected
editor.setEnabled(True)
host.busy = True
editor.insert_shortcut_action()
''')
