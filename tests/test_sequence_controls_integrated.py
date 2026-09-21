"""Real Qt flow repeat controls and partial selection route."""
from tests.test_shortcut_insertion import QT_SETUP, run_qt


def test_flow_controls_and_selected_snapshot_once():
    run_qt(QT_SETUP + '''
from PyQt6.QtWidgets import QMessageBox
from macroflow.ui.sequencer import MacroSequencerWidget
from macroflow.sequence_model import WaitItem
import macroflow.ui.sequencer as module
seen = []
class Session:
    def __init__(self, path, **kw): self.kw = kw; seen.append(self)
    def start(self, flow): self.flow = flow
    def is_running(self): return False
    def stop(self): pass
    def request_stop(self): pass
    def pause_state(self): return "running"
module.SequenceRunSession = Session
widget = MacroSequencerWidget()
widget._items = [WaitItem(step_id=f"w{i}", duration_ms=i) for i in range(10)]
widget._refresh_all()
QMessageBox.question = lambda *a: QMessageBox.StandardButton.Yes
assert widget._flow_repeat_mode.currentIndex() == 0
widget._flow_repeat_mode.setCurrentIndex(2)
assert widget.run_sequence(selected_rows=[3,4,5,6])
assert seen[-1].kw["repeat_count"] == 1
assert seen[-1].flow.start_node_id == "w3"
assert set(seen[-1].flow.nodes) == {"w3","w4","w5","w6","end_success"}
widget.stop_sequence()
widget._flow_repeat_mode.setCurrentIndex(1); widget._flow_repeat_count.setValue(3)
assert widget.run_sequence()
assert seen[-1].kw["repeat_count"] == 3
widget.stop_sequence()
assert len(widget._items) == 10
''')


def test_main_routes_pause_and_stop_by_active_sequence_not_tab():
    run_qt(QT_SETUP + '''
from macroflow.ui.main_window import MainWindow
import tempfile, os
with tempfile.TemporaryDirectory() as folder:
    old = os.getcwd(); os.chdir(folder)
    try:
        window = MainWindow()
        class Engine:
            state = "running"
            def is_running(self): return True
            def pause_state(self): return self.state
            def pause(self): self.state = "paused"
            def resume(self): self.state = "running"
        engine = Engine(); window._sequencer._engine = engine
        window._toggle_pause(); assert engine.state == "paused"
        window._toggle_pause(); assert engine.state == "running"
        stopped = []
        window._stop_sequencer = lambda: stopped.append(True)
        for index in range(window._tabs.count()):
            window._tabs.setCurrentIndex(index)
            window._update_toolbar()
            assert window._act_play.isEnabled() and window._act_stop.isEnabled()
            assert window._act_pause.isEnabled()
        window._tabs.setCurrentWidget(window._editor)
        window._toggle_playback(); assert stopped == [True]
        window._sequencer._engine = None
        window.close()
    finally: os.chdir(old)
''')


def test_modal_infinite_confirmation_stop_prevents_late_start():
    run_qt(QT_SETUP + '''
from macroflow.ui.main_window import MainWindow
from macroflow.sequence_model import WaitItem
from PyQt6.QtWidgets import QMessageBox
import tempfile, os
with tempfile.TemporaryDirectory() as folder:
    old = os.getcwd(); os.chdir(folder)
    try:
        window = MainWindow()
        window._sequencer._items = [WaitItem(step_id="w", duration_ms=1)]
        window._sequencer._refresh_all()
        window._sequencer._flow_repeat_mode.setCurrentIndex(2)
        def confirm(*args):
            assert window._state == "flow_preparing"
            window._toggle_recording()
            assert window._state == "flow_preparing"
            window._toggle_playback()
            assert window._flow_preparation_cancelled
            return QMessageBox.StandardButton.Yes
        QMessageBox.question = confirm
        window._toggle_sequencer()
        assert window._state == "idle" and not window._sequencer.is_running()
        window.close()
    finally: os.chdir(old)
''')


def test_partial_context_menu_emits_exact_selection_and_rejects_stale():
    run_qt(QT_SETUP + '''
from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QMenu
from macroflow.ui.sequencer import MacroSequencerWidget
from macroflow.sequence_model import WaitItem
widget = MacroSequencerWidget()
widget._items = [WaitItem(step_id=f"w{i}", duration_ms=i) for i in range(10)]
widget._refresh_all()
for i in range(3,7): widget._list.item(i).setSelected(True)
seen = []; widget.partial_run_requested.connect(seen.append)
QMenu.exec = lambda self, *a: self.actions()[0].trigger()
widget._range_context_menu(QPoint())
assert seen == [[3,4,5,6]]
def stale(self, *args):
    widget._set_dirty(True)
    self.actions()[0].trigger()
QMenu.exec = stale
widget._range_context_menu(QPoint())
assert len(seen) == 1
''')
