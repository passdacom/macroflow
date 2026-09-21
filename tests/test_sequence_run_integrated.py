"""Whole-session repeat must wait for worker exit and stop/error terminates it."""
import threading

from macroflow.script_engine import EndNode, MacroFlow, WaitFixedNode


def flow():
    return MacroFlow(version="1.0", name="test", created_at="", start_node_id="w",
        nodes={"w": WaitFixedNode(id="w", label="wait", duration_ms=1, next="end"),
               "end": EndNode(id="end", label="end", status="success")})


def test_three_cycles_and_pause_gap_stop():
    from macroflow.sequence_run import SequenceRunSession
    cycles, errors = [], []
    complete = threading.Event()
    session = SequenceRunSession("test.macroflow", repeat_count=3, interval_ms=1,
        on_cycle=lambda n: cycles.append(n), on_complete=lambda s: complete.set(),
        on_error=errors.append)
    session.start(flow())
    assert complete.wait(2)
    session.join(1)
    assert cycles == [1,2,3] and not errors and not session.is_running()
    gap = threading.Event()
    session = SequenceRunSession("test.macroflow", repeat_count=None, interval_ms=500,
        on_cycle=lambda n: gap.set())
    session.start(flow())
    assert gap.wait(1)
    session.pause()
    session.stop()
    assert not session.is_running()


def test_request_stop_retains_slow_stop_worker_without_blocking_caller():
    from macroflow.sequence_run import SequenceRunSession
    entered, release = threading.Event(), threading.Event()
    class SlowEngine:
        def stop(self):
            entered.set()
            release.wait(2)
    session = SequenceRunSession("test.macroflow")
    session._engine = SlowEngine()
    try:
        session.request_stop()
        assert entered.wait(1)
        assert session.is_running()
    finally:
        release.set()
        session._stop_thread.join(1)
    assert not session.is_running()
