"""Stop preserves owned cleanup failure through session and queued Qt delivery."""
from __future__ import annotations

import threading

import pytest

from macroflow import player
from macroflow.script_engine import InlineEventsNode, MacroFlow
from macroflow.sequence_run import SequenceRunSession
from macroflow.types import KeyEvent, MacroSettings, WaitEvent
from tests.test_shortcut_insertion import QT_SETUP, run_qt


def held_flow() -> MacroFlow:
    return MacroFlow(version="1.1", name="held input", created_at="", start_node_id="input",
                     nodes={"input": InlineEventsNode(id="input", label="input", playback_settings=MacroSettings(), events=[
                         KeyEvent(id="key", type="key_down", timestamp_ns=0, key="a", vk_code=65),
                         WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=10000),
                     ])})


@pytest.mark.parametrize("failed", [False, True])
@pytest.mark.parametrize("asynchronous", [False, True])
def test_real_sequence_stop_retains_cleanup_outcome(monkeypatch, failed, asynchronous):
    ready = threading.Event()
    original_wait = player._wait_active
    keys, errors, completed = [], [], []

    def send_key(vk, is_down):
        keys.append((vk, is_down))
        if failed and not is_down:
            raise OSError("sequence input release failed")

    def wait(seconds):
        ready.set()
        return original_wait(seconds)

    monkeypatch.setattr(player, "send_key", send_key)
    monkeypatch.setattr(player, "_wait_active", wait)
    session = SequenceRunSession("test.macroflow", repeat_count=3,
                                 on_error=errors.append, on_complete=completed.append)
    try:
        session.start(held_flow())
        assert ready.wait(2)
        if asynchronous:
            session.request_stop()
            session._stop_thread.join(2)
        else:
            session.stop()
        session.join(2)
        assert not session.is_running()
        assert session.cycle == 1 and completed == []
        assert keys == [(65, True), (65, False)]
        expected = "sequence input release failed" if failed else None
        assert session.terminal_error == expected
        assert errors == ([expected] if failed else [])
        session.stop()
        assert errors == ([expected] if failed else [])
    finally:
        session.stop()


@pytest.mark.parametrize("delivery", ["poll_first", "queued_first", "synchronous"])
@pytest.mark.parametrize("failed", [False, True])
def test_qt_stop_checks_retained_outcome_before_discarding_generation(delivery, failed):
    run_qt(QT_SETUP + f'''
import threading
from PyQt6.QtWidgets import QMessageBox
from macroflow import player
from macroflow.sequence_run import SequenceRunSession
from macroflow.ui.sequencer import MacroSequencerWidget
from tests.test_sequence_stop_errors import held_flow
ready, releasing, release = (threading.Event() for _ in range(3))
original_wait = player._wait_active
failed = {failed!r}
delivery = {delivery!r}
def key(vk, is_down):
    if not is_down:
        releasing.set()
        assert release.wait(2)
        if failed:
            raise OSError("sequence input release failed")
def wait(seconds):
    ready.set()
    return original_wait(seconds)
player.send_key = key
player._wait_active = wait
widget = MacroSequencerWidget()
warnings, errors, completed = [], [], []
QMessageBox.warning = lambda *args: warnings.append(args[-1])
widget.sequence_error.connect(errors.append)
widget.sequence_complete.connect(completed.append)
widget._active_generation = 7
session = SequenceRunSession("test.macroflow", repeat_count=3,
    on_error=lambda message: widget._sequence_failed.emit(7, message),
    on_complete=lambda status: widget._sequence_finished.emit(7, status))
widget._engine = session
try:
    session.start(held_flow())
    assert ready.wait(2)
    # Cleanup blocks deterministically: requesting stop must return to the GUI.
    assert widget._stop_sequence() is False
    assert releasing.wait(2)
    assert widget._engine is session
    release.set()
    session._stop_thread.join(2)
    session.join(2)
    assert not session.is_running()
    # No processEvents yet: the worker's error signal is still queued.
    if delivery == "queued_first":
        app.processEvents()
    elif delivery == "synchronous":
        # Exercise the already-reaped immediate-stop path deterministically.
        session.request_stop = lambda: None
        assert widget._stop_sequence() is True
    else:
        widget._poll_stopping_engine()
    app.processEvents()
    widget._poll_stopping_engine()
    app.processEvents()
    assert widget._engine is None and widget._active_generation is None
    expected = ["sequence input release failed"] if failed else []
    assert warnings == expected and errors == expected
    assert "success" not in completed
    if failed:
        assert completed == []
    # A late signal from the old session cannot affect a newer generation.
    widget._active_generation = 8
    widget._sequence_failed.emit(7, "stale failure")
    app.processEvents()
    assert warnings == expected and errors == expected
    assert widget._active_generation == 8
finally:
    release.set()
    session.stop()
    widget._engine = None
    widget._active_generation = None
    widget.close()
''')
