"""Controlled real-worker regressions; all native input is replaced."""
import threading
import time

import pytest

from macroflow import player
from macroflow.script_engine import FlowEngine, InlineEventsNode, MacroFlow
from macroflow.types import KeyEvent, MacroSettings, MouseButtonEvent, WaitEvent


def wait_for(predicate):
    deadline = time.monotonic() + 2
    while not predicate() and time.monotonic() < deadline:
        time.sleep(.001)
    assert predicate()


@pytest.mark.parametrize("kind", ["key", "mouse"])
@pytest.mark.parametrize("action", ["release", "resume", "stop"])
def test_flow_reports_requested_until_original_release(monkeypatch, kind, action):
    held, release = threading.Event(), threading.Event()
    calls = []
    monkeypatch.setattr(player, "send_key", lambda vk, is_down: calls.append((vk, is_down)))
    monkeypatch.setattr(player, "ratio_to_pixel", lambda *a: (10, 20))
    monkeypatch.setattr(player, "send_mouse_move", lambda *a: None)
    monkeypatch.setattr(player, "send_mouse_button",
                        lambda x, y, button, *, down: calls.append((button, down)))
    if kind == "key":
        events = [KeyEvent(id=t, type=t, timestamp_ns=0, key="ctrl", vk_code=17)
                  for t in ("key_down", "key_up")]
        identity = 17
    else:
        events = [MouseButtonEvent(id=t, type=t, timestamp_ns=0, button="left",
                                   x_ratio=.1, y_ratio=.2)
                  for t in ("mouse_down", "mouse_up")]
        identity = "left"
    events.append(WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=100))
    original = player._execute_event

    def execute(event, settings, state):
        original(event, settings, state)
        if event is events[0]:
            held.set()
            assert release.wait(2)

    monkeypatch.setattr(player, "_execute_event", execute)
    flow = MacroFlow(version="1.1", name="test", created_at="", start_node_id="i",
        nodes={"i": InlineEventsNode(id="i", label="input", events=events,
                                    playback_settings=MacroSettings())})
    engine = FlowEngine("test.macroflow")
    try:
        engine.start(flow)
        assert held.wait(2)
        engine.pause()
        assert player.is_paused(), "compatibility accessor includes pending"
        assert not player._playback_clock.is_paused()
        assert engine.pause_state() == "requested"
        assert player.pause_state() == "requested"
        assert calls == [(identity, True)], "pause must not synthesize release"
        if action == "resume":
            engine.resume()
            assert engine.pause_state() == player.pause_state() == "running"
            release.set()
            engine.join(2)
            assert not engine.is_running()
            assert calls == [(identity, True), (identity, False)]
            return
        if action == "stop":
            stopper = threading.Thread(target=engine.stop)
            stopper.start()
            assert engine._stop_flag.wait(1)
            wait_for(lambda: len(calls) == 2)
            release.set()
            stopper.join(2)
            assert not stopper.is_alive()
            assert calls == [(identity, True), (identity, False)]
            assert not player.is_paused()
            assert player.pause_state() == "running"
            return
        release.set()
        wait_for(player._playback_clock.is_paused)
        assert engine.pause_state() == "paused"
        assert calls == [(identity, True), (identity, False)]
        engine.resume()
        engine.join(2)
        assert not engine.is_running()
        assert calls == [(identity, True), (identity, False)]
    finally:
        release.set()
        engine.stop()
        player.stop()


@pytest.mark.parametrize("transition", ["pause", "aba", "stop"])
def test_color_discards_inflight_sample(monkeypatch, transition):
    from macroflow import win32
    from macroflow.script_engine import ColorCheckNode, EndNode

    entered = [threading.Event() for _ in range(3)]
    release = [threading.Event() for _ in range(3)]
    returned = threading.Event()
    done, complete, errors, starts = [], [], [], []
    screen = [(255, 255, 255)]
    calls = []

    def pixel(x, y):
        # One callable throughout: capture what the screen showed at read start.
        value = screen[0]
        index = len(calls)
        calls.append(value)
        assert index < 3, "unexpected extra sample"
        entered[index].set()
        assert release[index].wait(3)
        if index == 0:
            returned.set()
        return value

    monkeypatch.setattr(win32, "get_pixel_color", pixel)
    monkeypatch.setattr(win32, "ratio_to_pixel", lambda *a: (0, 0))
    flow = MacroFlow(version="1.1", name="color", created_at="", start_node_id="c",
        nodes={"c": ColorCheckNode(id="c", label="color", x_ratio=0, y_ratio=0,
            target_color="#FFFFFF", timeout_ms=0, check_interval_ms=1, on_match="end"),
            "end": EndNode(id="end", label="end")})
    engine = FlowEngine("test.macroflow", on_node_done=lambda *a: done.append(a),
                        on_complete=complete.append, on_error=errors.append,
                        on_node_start=lambda node, label: starts.append(node))
    stopper = None
    try:
        engine.start(flow)
        assert entered[0].wait(2)
        if transition == "stop":
            stopper = threading.Thread(target=engine.stop)
            stopper.start()
            assert engine._stop_flag.wait(1)
        else:
            engine.pause()
        screen[0] = (0, 0, 0)
        if transition == "aba":
            engine.resume()
        release[0].set()
        assert returned.wait(1)
        if transition == "stop":
            stopper.join(1)
            assert not stopper.is_alive()
            assert done == complete == errors == []
            assert starts == ["c"]
            return
        if transition == "pause":
            assert not entered[1].wait(.05)
            assert done == [], "stale matching sample committed while paused"
            engine.resume()
        assert entered[1].wait(1), "must reread instead of accepting stale success"
        assert calls == [(255, 255, 255), (0, 0, 0)]
        assert done == complete == []
        screen[0] = (255, 255, 255)
        release[1].set()
        assert entered[2].wait(1)
        assert done == complete == [], "fresh nonmatch must not complete"
        release[2].set()
        engine.join(2)
        assert not engine.is_running()
        assert [item[:2] for item in done] == [("c", True), ("end", True)]
        assert complete == ["success"] and errors == []
    finally:
        for event in release:
            event.set()
        engine.stop()
        if stopper is not None:
            stopper.join(2)


def test_pause_during_inner_terminal_handoff_defers_node_done(monkeypatch):
    terminal, release = threading.Event(), threading.Event()
    done = []
    original = player._play_loop

    def delayed_exit(*args, **kwargs):
        original(*args, **kwargs)
        terminal.set()
        assert release.wait(2)

    monkeypatch.setattr(player, "_play_loop", delayed_exit)
    flow = MacroFlow(version="1.1", name="test", created_at="", start_node_id="i",
        nodes={"i": InlineEventsNode(id="i", label="wait", events=[
            WaitEvent(id="w", type="wait", timestamp_ns=0, duration_ms=0)],
            playback_settings=MacroSettings())})
    engine = FlowEngine("test.macroflow", on_node_done=lambda *a: done.append(a))
    try:
        engine.start(flow)
        assert terminal.wait(1)
        engine.pause()
        assert engine.pause_state() == "paused", "no held input at terminal handoff"
        release.set()
        wait_for(lambda: not player.is_playing())
        assert engine.pause_state() == "paused"
        assert not threading.Event().wait(.08)
        assert done == [], "inner terminal signal must not bypass the flow gate"
        engine.resume()
        engine.join(2)
        assert [item[:2] for item in done] == [("i", True)]
    finally:
        release.set()
        engine.stop()
        player.stop()
