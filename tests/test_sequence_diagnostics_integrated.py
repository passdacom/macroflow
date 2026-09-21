"""Runtime diagnostics must not repeat user labels or exception payloads."""
from tests.test_shortcut_insertion import QT_SETUP, run_qt


def test_runtime_log_is_bounded_and_payload_free():
    run_qt(QT_SETUP + r'''
from macroflow.ui.sequencer import MacroSequencerWidget
widget = MacroSequencerWidget()
widget._active_generation = 7
widget._apply_node_start(7, "step_a", "PRIVATE_LABEL")
widget._apply_node_done(7, "step_a", False, "PRIVATE_PAYLOAD")
text = widget._log.toPlainText()
assert "PRIVATE" not in text
assert "step_a" in text
for i in range(400): widget._log_message("state")
assert widget._log.document().blockCount() <= 300
''')
