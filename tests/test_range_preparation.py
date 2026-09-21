"""Preparation must cancel/stale-reject before any partial playback starts."""
from tests.test_shortcut_insertion import QT_SETUP, run_qt


def test_preparation_cancellation_and_generation_in_real_qt():
    run_qt(QT_SETUP + '''
import copy

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox
from macroflow.ui.main_window import MainWindow
import macroflow.ui.range_preparation as prep
from macroflow.types import WaitEvent
import tempfile, os
with tempfile.TemporaryDirectory() as folder:
    old = os.getcwd(); os.chdir(folder)
    try:
        window = MainWindow()
        macro = blank(); macro.events = [WaitEvent(id="w", type="wait", timestamp_ns=0, duration_ms=1)]
        window._macro = macro; window._editor.load_macro(macro)
        started = []
        window._start_playback = lambda **kw: started.append(kw)
        QMessageBox.warning = lambda *a: None
        prep.external_target_ready = lambda: True
        original = prep.RangePreparationDialog.exec
        def cancel(self):
            assert window._state == "preparing"
            window._emergency_stop()
            assert window._state == "preparing", "reservation must survive nested cancel"
            return QDialog.DialogCode.Rejected
        prep.RangePreparationDialog.exec = cancel
        window._on_play_event_range(0,1)
        assert started == [] and window._state == "idle"
        def stale(self):
            window._editor.load_macro(copy.deepcopy(macro))
            return QDialog.DialogCode.Accepted
        prep.RangePreparationDialog.exec = stale
        window._on_play_event_range(0,1)
        assert started == []
        prep.RangePreparationDialog.exec = lambda self: QDialog.DialogCode.Accepted
        window._on_play_event_range(0,1)
        assert len(started) == 1
        assert started[0]["playback_macro"] is not macro
        assert started[0]["options"].event_range == (0,1)
        window._state = "idle"
        QMessageBox.question = lambda *a: QMessageBox.StandardButton.Discard
        window.close()
    finally:
        os.chdir(old)
''')
