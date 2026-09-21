"""Deadline, callback lock order and bounded-stop color regressions."""
import threading
import time

import pytest

from macroflow import win32
from macroflow.script_engine import ColorCheckNode, FlowEngine, MacroFlow


@pytest.mark.parametrize("expired", [False, True])
def test_color_active_deadline_and_unlocked_notification(monkeypatch, expired):
    entered, release = threading.Event(), threading.Event()
    calls, done = [], []
    engine = FlowEngine("test.macroflow")
    node = ColorCheckNode(id="c", label="color", x_ratio=0, y_ratio=0,
                         target_color="#FFFFFF", timeout_ms=100,
                         on_match="yes", on_timeout="no")

    def pixel(*args):
        calls.append(True)
        if len(calls) == 1:
            entered.set()
            assert release.wait(2)
        return (255, 255, 255)

    def notify(*args):
        assert engine._lifecycle_lock.acquire(blocking=False)
        engine._lifecycle_lock.release()
        engine.pause()
        engine.resume()
        done.append(args)

    engine._on_node_done = notify
    monkeypatch.setattr(win32, "ratio_to_pixel", lambda *a: (0, 0))
    monkeypatch.setattr(win32, "get_pixel_color", pixel)
    result = []
    worker = threading.Thread(target=lambda: result.append(engine._run_color_check_node(node)))
    worker.start()
    try:
        assert entered.wait(1)
        if not expired:
            engine.pause()
            before = engine._clock.now()
        time.sleep(.15)
        if not expired:
            assert engine._clock.now() == before
            engine.resume()
        release.set()
        worker.join(2)
        assert not worker.is_alive()
        assert result == ["no" if expired else "yes"]
        assert len(calls) == (1 if expired else 2)
        assert len(done) == 1 and done[0][1] is not expired
    finally:
        release.set()
        engine.stop()
        worker.join(2)


def test_stop_remains_bounded_with_blocked_pixel(monkeypatch):
    entered, release = threading.Event(), threading.Event()
    done, complete = [], []

    def pixel(*args):
        entered.set()
        assert release.wait(8)
        return (255, 255, 255)

    monkeypatch.setattr(win32, "ratio_to_pixel", lambda *a: (0, 0))
    monkeypatch.setattr(win32, "get_pixel_color", pixel)
    engine = FlowEngine("test.macroflow", on_node_done=lambda *a: done.append(a),
                        on_complete=complete.append)
    flow = MacroFlow(version="1.1", name="stop", created_at="", start_node_id="c",
        nodes={"c": ColorCheckNode(id="c", label="c", x_ratio=0, y_ratio=0,
                                  target_color="#FFFFFF", timeout_ms=0)})
    try:
        engine.start(flow)
        assert entered.wait(1)
        started = time.monotonic()
        engine.stop()
        assert time.monotonic() - started < 5.5
        assert engine.is_running(), "blocked native read remains owned until return"
        with pytest.raises(RuntimeError):
            engine.start(flow)
        release.set()
        engine.join(1)
        assert not engine.is_running()
        assert done == complete == []
    finally:
        release.set()
        engine.stop()
