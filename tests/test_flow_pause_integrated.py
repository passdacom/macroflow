"""Flow pause uses active time for fixed waits and stop always wakes it."""
import threading
import time

from macroflow.script_engine import EndNode, FlowEngine, MacroFlow, WaitFixedNode


def test_fixed_wait_pause_preserves_remaining_and_stop_unblocks():
    entered = threading.Event()
    done = threading.Event()
    flow = MacroFlow(version="1.0", name="test", created_at="", start_node_id="w",
        nodes={"w": WaitFixedNode(id="w", label="wait", duration_ms=150, next="end"),
               "end": EndNode(id="end", label="end", status="success")})
    engine = FlowEngine("test.macroflow", on_node_start=lambda *a: entered.set(),
                        on_complete=lambda *a: done.set())
    engine.start(flow)
    assert entered.wait(1)
    engine.pause()
    assert not done.wait(.2)
    engine.resume()
    assert done.wait(1)
    engine.stop()
    assert not engine.is_running()
    engine = FlowEngine("test.macroflow")
    engine.pause()
    engine.start(flow)
    time.sleep(.02)
    engine.stop()
    assert not engine.is_running()


def test_engine_retains_worker_until_player_exits(monkeypatch):
    from macroflow import player
    from macroflow.script_engine import InlineEventsNode
    from macroflow.types import MacroSettings, WaitEvent
    terminal, release, completed = threading.Event(), threading.Event(), threading.Event()
    original = player._play_loop
    def delayed_exit(*args, **kwargs):
        original(*args, **kwargs)
        terminal.set()
        release.wait(2)
    monkeypatch.setattr(player, "_play_loop", delayed_exit)
    flow = MacroFlow(version="1.1", name="test", created_at="", start_node_id="inline",
        nodes={"inline": InlineEventsNode(id="inline", label="inline", playback_settings=MacroSettings(), events=[
            WaitEvent(id="w", type="wait", timestamp_ns=0, duration_ms=0)])})
    engine = FlowEngine("test.macroflow", on_complete=lambda *a: completed.set())
    try:
        engine.start(flow)
        assert terminal.wait(1)
        assert not completed.wait(.1), "terminal callback is not worker exit"
        assert engine.is_running()
    finally:
        release.set()
        engine.stop()
