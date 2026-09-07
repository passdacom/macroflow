from tests.test_shortcut_insertion import QT_SETUP, run_qt


def test_captured_click_can_be_changed_to_right_click_and_undone():
    run_qt(QT_SETUP + '''
from PyQt6.QtWidgets import QComboBox
editor = EventEditorWidget(); editor.load_macro(blank())
editor.insert_click_action(); editor.consume_f6_capture(.2, .3, "#123456")
def accept(dialog):
    combo = dialog.findChild(QComboBox, "click_button")
    assert combo is not None, "no button editing control"
    combo.setCurrentIndex(combo.findData("right"))
    return QDialog.DialogCode.Accepted
QDialog.exec = accept
editor._edit_position(0)
assert [e.button for e in editor.current_macro().events] == ["right", "right"]
editor._undo()
assert [e.button for e in editor.current_macro().events] == ["left", "left"]
''')
