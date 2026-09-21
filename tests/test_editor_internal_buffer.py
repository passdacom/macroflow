"""Real Qt internal-buffer actions, isolated from suite fake Qt modules."""
from tests.test_shortcut_insertion import QT_SETUP, run_qt


def test_internal_copy_paste_transaction_and_menu():
    run_qt(QT_SETUP + '''
import copy
from PyQt6.QtWidgets import QMenu, QMessageBox
from macroflow.types import KeyEvent
editor = EventEditorWidget(); source = blank()
source.events = [KeyEvent(id=str(i), type=kind, timestamp_ns=i*1000000,
                         key=str(vk), vk_code=vk, remark="preserved")
                 for i, (kind, vk) in enumerate([
                     ("key_down",17),("key_down",67),("key_up",67),("key_up",17)])]
editor.load_macro(source)
editor._table.selectAll()
before = copy.deepcopy(editor.current_macro())
menus = []
def choose_copy(self, *args):
    menus.extend(a.text() for a in self.actions())
    next(a for a in self.actions() if a.text() == "동작 복사").trigger()
QMenu.exec = choose_copy
editor._context_menu(None)
assert "선택 구간 1회 재생" in menus
assert editor.current_macro() == before and not editor._undo_stack
editor._paste_fragment(len(source.events))
after = copy.deepcopy(editor.current_macro())
assert len(after.events) == 8 and len({e.id for e in after.events}) == 8
assert after.raw_events == before.raw_events
assert [e.remark for e in after.events] == ["preserved"] * 8
assert len(editor._undo_stack) == 1
editor._undo(); assert editor.current_macro().events == before.events
editor._redo(); assert editor.current_macro() == after
editor.load_macro(blank()); editor._paste_fragment(0)
assert editor.current_macro().events == []
''')


def test_all_partial_routes_reject_incomplete_chord():
    run_qt(QT_SETUP + '''
from PyQt6.QtWidgets import QMessageBox
from macroflow.types import KeyEvent
editor = EventEditorWidget(); source = blank()
source.events = [KeyEvent(id=str(i), type=kind, timestamp_ns=i, key=str(vk), vk_code=vk)
 for i, (kind,vk) in enumerate([("key_down",17),("key_down",67),("key_up",67),("key_up",17)])]
editor.load_macro(source)
warnings, played = [], []
QMessageBox.warning = lambda *args: warnings.append(True)
editor.play_event_range.connect(lambda *args: played.append(args))
editor._play_single_event(0); editor._play_single_event(1)
editor._play_from_row_to_end(1)
assert editor.get_event_range_for_rows(2,2) is None
assert played == []
editor._play_selected_rows([0,1]); assert played == [(0,4)]
assert editor.get_event_range_for_rows(1,2) == (0,4)
''')


def test_merge_release_summary_survives_grouping():
    run_qt(QT_SETUP + '''
from macroflow.macro_file import merge_macros
from macroflow.types import KeyEvent
source = blank()
source.events = [KeyEvent(id="d", type="key_down", timestamp_ns=0, key="ctrl", vk_code=17)]
editor = EventEditorWidget(); editor.load_macro(merge_macros([(source,"a")]))
assert "병합 경계 키 해제: 1개" in editor._summary.text()
''')
