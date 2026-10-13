"""Owned worker outcomes survive runtime, callback and cleanup failures.

All documents contain valid runtime input and all native side effects are mocked.
Barriers, rather than sleeps, determine each stop/completion ordering.
"""
from __future__ import annotations

import threading
from collections.abc import Generator

import pytest

from macroflow import player
from macroflow.script_engine import FlowEngine, InlineEventsNode, MacroFlow
from macroflow.types import (
    AnyEvent,
    KeyEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    WaitEvent,
)


def document(events: list[AnyEvent] | None = None) -> MacroData:
    return MacroData(
        meta=MacroMeta(version="1.0", app_version="test", created_at="",
                       screen_width=100, screen_height=100, dpi_scale=1.0),
        settings=MacroSettings(), raw_events=[],
        events=events if events is not None else [
            KeyEvent(id="down", type="key_down", timestamp_ns=0, key="a", vk_code=65),
            WaitEvent(id="wait", type="wait", timestamp_ns=2_000_000, duration_ms=0),
        ],
    )


@pytest.fixture(autouse=True)
def native_safe(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    player.stop()
    for name in ("send_key", "send_mouse_button", "send_mouse_move", "send_mouse_wheel",
                 "send_paste", "set_clipboard_text"):
        monkeypatch.setattr(player, name, lambda *args, **kwargs: None)
    monkeypatch.setattr(player, "ratio_to_pixel", lambda *args: (10, 20))
    yield
    player.stop()


def fail(*args: object, **kwargs: object) -> None:
    raise RuntimeError("injected runtime fault")


@pytest.mark.parametrize("fault", ["start_pause", "initial_clock", "timing", "wait", "pause_boundary",
                                    "event_start", "event_done", "worker_wrapper"])
def test_every_worker_fault_publishes_failure_and_releases_inputs(
    monkeypatch: pytest.MonkeyPatch, fault: str,
) -> None:
    keys: list[tuple[int, bool]] = []
    errors: list[Exception] = []
    complete: list[bool] = []
    monkeypatch.setattr(player, "send_key", lambda vk, is_down: keys.append((vk, is_down)))
    callbacks = {}
    if fault == "start_pause":
        callbacks["start_pause_requested"] = fail
    elif fault == "initial_clock":
        monkeypatch.setattr(player, "_active_now_ns", fail)
    elif fault == "timing":
        monkeypatch.setattr(player, "_event_timing_compensation_ns", fail)
    elif fault == "wait":
        monkeypatch.setattr(player._playback_clock, "wait_until", fail)
        monkeypatch.setattr(player, "_active_now_ns", lambda: 0)
    elif fault == "pause_boundary":
        monkeypatch.setattr(player, "_apply_pending_pause_if_safe", fail)
    elif fault == "event_start":
        def start(index: int, event: AnyEvent) -> None:
            if index == 1:
                fail()
        callbacks["on_event_start"] = start
    elif fault == "event_done":
        callbacks["on_event"] = fail
    else:
        original = player._play_loop
        def wrapped(*args: object, **kwargs: object) -> None:
            original(*args, **kwargs)
            fail()
        monkeypatch.setattr(player, "_play_loop", wrapped)
    session = player.play(document(), on_complete=lambda: complete.append(True),
                          on_error=errors.append, **callbacks)
    assert session.wait(2), "every exit path must publish an owned terminal signal"
    assert player.wait_for_exit(session, 2)
    assert session.done and session.result == "failed"
    assert isinstance(session.error, RuntimeError)
    assert str(session.error) == "injected runtime fault"
    assert errors == [session.error] and complete == []
    assert keys == ([] if fault in {"start_pause", "initial_clock"} else [(65, True), (65, False)])
    assert player._active_play_state is None


@pytest.mark.parametrize("callback", ["complete", "error"])
def test_terminal_callback_failure_is_recorded_without_second_notification(
    monkeypatch: pytest.MonkeyPatch, callback: str,
) -> None:
    calls: list[str] = []
    if callback == "error":
        monkeypatch.setattr(player, "_event_timing_compensation_ns", fail)

    def completed() -> None:
        calls.append("complete")
        raise ValueError("host callback failed")

    def errored(exc: Exception) -> None:
        calls.append("error")
        raise ValueError("host callback failed")

    session = player.play(document(), on_complete=completed, on_error=errored)
    assert session.wait(2) and player.wait_for_exit(session, 2)
    assert session.result == "failed"
    assert calls == [callback]
    if callback == "complete":
        assert isinstance(session.error, ValueError)
    else:
        assert isinstance(session.error, ExceptionGroup)
        assert [type(exc) for exc in session.error.exceptions] == [RuntimeError, ValueError]


def test_release_faults_attempt_every_key_and_button_and_report_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    releases: list[object] = []
    errors: list[Exception] = []
    complete: list[bool] = []

    def key(vk: int, is_down: bool) -> None:
        if not is_down:
            releases.append(vk)
            raise OSError(f"release key {vk}")

    def mouse(x: int, y: int, button: str, down: bool) -> None:
        if not down:
            releases.append(button)
            raise OSError(f"release mouse {button}")

    monkeypatch.setattr(player, "send_key", key)
    monkeypatch.setattr(player, "send_mouse_button", mouse)
    events: list[AnyEvent] = [
        KeyEvent(id="a", type="key_down", timestamp_ns=0, key="a", vk_code=65),
        KeyEvent(id="b", type="key_down", timestamp_ns=0, key="b", vk_code=66),
        MouseButtonEvent(id="m", type="mouse_down", timestamp_ns=0,
                         x_ratio=.1, y_ratio=.2, button="left"),
    ]
    session = player.play(document(events), on_error=errors.append,
                          on_complete=lambda: complete.append(True))
    assert session.wait(2) and player.wait_for_exit(session, 2)
    assert set(releases) == {65, 66, "left"} and len(releases) == 3
    assert session.result == "failed" and isinstance(session.error, ExceptionGroup)
    assert len(session.error.exceptions) == 3
    assert errors == [session.error] and not complete


def test_cleanup_hook_failure_still_releases_held_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    keys: list[tuple[int, bool]] = []
    errors: list[Exception] = []
    monkeypatch.setattr(player, "send_key", lambda vk, is_down: keys.append((vk, is_down)))
    monkeypatch.setattr(player, "_release_active_inputs", fail)
    session = player.play(document(), on_error=errors.append)
    assert session.wait(2) and player.wait_for_exit(session, 2)
    assert keys == [(65, True), (65, False)]
    assert session.result == "failed" and errors == [session.error]


def test_stop_wins_before_terminal_commit_and_old_session_cannot_touch_next(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ready, release, stopping = (threading.Event() for _ in range(3))
    complete: list[bool] = []
    original = player._release_active_inputs
    notify = player._playback_clock.notify_stop

    def cleanup() -> None:
        if threading.current_thread().name == "PlaybackThread":
            ready.set()
            assert release.wait(2)
        original()

    def stopped() -> None:
        notify()
        stopping.set()

    monkeypatch.setattr(player, "_release_active_inputs", cleanup)
    monkeypatch.setattr(player._playback_clock, "notify_stop", stopped)
    first = player.play(document(), on_complete=lambda: complete.append(True))
    stopper = threading.Thread(target=player.stop, args=(first,))
    try:
        assert ready.wait(2)
        stopper.start()
        assert stopping.wait(2)
        release.set()
        stopper.join(2)
        assert not stopper.is_alive()
        assert first.done and first.result == "stopped" and first.error is None
        assert not complete
        second = player.play(document([WaitEvent(id="w", type="wait", timestamp_ns=0,
                                                  duration_ms=10000)]))
        assert player.wait_for_exit(first, 0)
        assert not player.stop(first)
        assert not player.pause(first)
        assert not player.resume(first)
        assert not player.is_paused()
        assert player.pause(second)
        assert player.is_paused()
        assert not player.resume(first)
        assert player.is_paused()
        assert player.resume(second)
        assert not second.done and player.is_playing()
        assert player.stop(second)
        assert player.wait_for_exit(second, 2) and second.result == "stopped"
    finally:
        release.set()
        if stopper.ident is not None:
            stopper.join(2)


def test_terminal_callback_can_reenter_stop_without_deadlocking() -> None:
    entered, release = threading.Event(), threading.Event()
    sessions: list[player.PlaybackSession] = []
    stop_results: list[bool] = []

    def start(*args: object) -> None:
        entered.set()
        assert release.wait(2)

    def complete() -> None:
        stop_results.append(player.stop(sessions[0]))

    sessions.append(player.play(document(), on_event_start=start, on_complete=complete))
    try:
        assert entered.wait(2)
        release.set()
        assert player.wait_for_exit(sessions[0], 2)
        assert sessions[0].result == "completed" and stop_results == [False]
    finally:
        release.set()


def test_wait_for_exit_joins_owned_worker_even_after_terminal_signal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    terminal, release = threading.Event(), threading.Event()
    original = player._run_session

    def wrapper(*args: object, **kwargs: object) -> None:
        original(*args, **kwargs)
        terminal.set()
        assert release.wait(2)

    monkeypatch.setattr(player, "_run_session", wrapper)
    session = player.play(document())
    try:
        assert terminal.wait(2) and session.done
        assert not player.wait_for_exit(session, 0)
        with pytest.raises(player.PlaybackError):
            player.play(document())
    finally:
        release.set()
    assert player.wait_for_exit(session, 2)


def test_flow_terminates_on_owned_failure_even_when_callbacks_are_not_delivered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    errors: list[str] = []
    completed: list[str] = []
    nodes: list[tuple[object, ...]] = []
    real_play = player.play

    def play_without_callbacks(*args: object, **kwargs: object) -> player.PlaybackSession:
        kwargs.pop("on_complete", None)
        kwargs.pop("on_error", None)
        return real_play(*args, **kwargs)

    monkeypatch.setattr(player, "play", play_without_callbacks)
    monkeypatch.setattr(player, "_event_timing_compensation_ns", fail)
    macro = document()
    flow = MacroFlow(version="1.1", name="fault", created_at="", start_node_id="inline",
                     nodes={"inline": InlineEventsNode(id="inline", label="inline",
                            events=macro.events, playback_settings=macro.settings)})
    engine = FlowEngine("test.macroflow", on_error=errors.append, on_complete=completed.append,
                        on_node_done=lambda *args: nodes.append(args))
    try:
        engine.start(flow)
        engine.join(2)
        assert not engine.is_running(), "flow must not depend solely on callback delivery"
        assert errors == ["injected runtime fault"] and not completed
        assert len(nodes) == 1 and nodes[0][:2] == ("inline", False)
    finally:
        engine.stop()


def test_direct_play_loop_keeps_cleanup_and_error_callback_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    keys: list[tuple[int, bool]] = []
    errors: list[Exception] = []
    monkeypatch.setattr(player, "send_key", lambda vk, is_down: keys.append((vk, is_down)))
    monkeypatch.setattr(player, "_event_timing_compensation_ns", fail)
    player._play_loop(document(), 1.0, None, None, errors.append, None)
    assert keys == [(65, True), (65, False)]
    assert len(errors) == 1 and str(errors[0]) == "injected runtime fault"


def test_stop_release_failure_is_in_owned_outcome(monkeypatch: pytest.MonkeyPatch) -> None:
    held, released = threading.Event(), threading.Event()
    keys: list[tuple[int, bool]] = []
    errors: list[Exception] = []
    completed: list[bool] = []

    def key(vk: int, is_down: bool) -> None:
        keys.append((vk, is_down))
        if not is_down:
            released.set()
            raise OSError("stop release failed")

    def event_done(*args: object) -> None:
        held.set()
        assert released.wait(2)

    monkeypatch.setattr(player, "send_key", key)
    session = player.play(document(), on_event=event_done, on_error=errors.append,
                          on_complete=lambda: completed.append(True))
    try:
        assert held.wait(2)
        assert player.stop(session)
        assert player.wait_for_exit(session, 2) and session.done
        assert session.result == "failed" and isinstance(session.error, OSError)
        assert errors == [session.error] and not completed
        assert keys == [(65, True), (65, False)]
    finally:
        released.set()


def test_worker_base_exception_still_publishes_terminal_outcome(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def exit_worker(*args: object) -> None:
        raise SystemExit("host aborted")

    monkeypatch.setattr(player, "_event_timing_compensation_ns", exit_worker)
    session = player.play(document())
    assert session.wait(2) and player.wait_for_exit(session, 2)
    assert session.result == "failed" and isinstance(session.error, player.PlaybackError)
    assert str(session.error) == "SystemExit: host aborted"


@pytest.mark.parametrize("terminal", ["complete", "error"])
def test_direct_terminal_callback_exception_never_escapes_worker_boundary(
    monkeypatch: pytest.MonkeyPatch, terminal: str,
) -> None:
    calls: list[str] = []
    if terminal == "error":
        monkeypatch.setattr(player, "_execute_event", fail)

    def complete() -> None:
        calls.append("complete")
        raise ValueError("completion notification failed")

    def error(exc: Exception) -> None:
        calls.append("error")
        raise ValueError("error notification failed")

    player._play_loop(document(), 1.0, None, complete, error, None)
    assert calls == [terminal]


@pytest.mark.parametrize("stop_at", ["held_input", "worker_join"])
def test_flow_stop_reports_release_failure_once(
    monkeypatch: pytest.MonkeyPatch, stop_at: str,
) -> None:
    ready, release, stopping = (threading.Event() for _ in range(3))
    errors: list[str] = []
    completed: list[str] = []
    nodes: list[tuple[object, ...]] = []
    keys: list[tuple[int, bool]] = []
    wait_active = player._wait_active
    wait_for_exit = player.wait_for_exit

    def key(vk: int, is_down: bool) -> None:
        keys.append((vk, is_down))
        if not is_down:
            raise OSError("flow stop release failed")

    def wait(seconds: float) -> bool:
        ready.set()
        return wait_active(seconds)

    def join(session: player.PlaybackSession, timeout: float | None = None) -> bool:
        if threading.current_thread().name == "FlowEngine":
            ready.set()
            assert release.wait(2)
        return wait_for_exit(session, timeout)

    monkeypatch.setattr(player, "send_key", key)
    if stop_at == "held_input":
        monkeypatch.setattr(player, "_wait_active", wait)
    else:
        monkeypatch.setattr(player, "wait_for_exit", join)
    macro = document([
        KeyEvent(id="a", type="key_down", timestamp_ns=0, key="a", vk_code=65),
        WaitEvent(id="w", type="wait", timestamp_ns=0,
                  duration_ms=10000 if stop_at == "held_input" else 0),
    ])
    flow = MacroFlow(version="1.1", name="fault", created_at="", start_node_id="inline",
                     nodes={"inline": InlineEventsNode(id="inline", label="inline",
                            events=macro.events, playback_settings=macro.settings)})
    engine = FlowEngine("test.macroflow", on_error=errors.append, on_complete=completed.append,
                        on_node_done=lambda *args: nodes.append(args))
    wake = engine._clock.wake

    def wake_stop() -> None:
        wake()
        stopping.set()

    monkeypatch.setattr(engine._clock, "wake", wake_stop)
    stopper = threading.Thread(target=engine.stop)
    try:
        engine.start(flow)
        assert ready.wait(2)
        stopper.start()
        assert stopping.wait(2)
        release.set()
        stopper.join(2)
        assert not stopper.is_alive() and not engine.is_running()
        assert errors == ["flow stop release failed"] and not completed
        assert nodes == [("inline", False, "flow stop release failed")]
        assert keys == [(65, True), (65, False)]
    finally:
        release.set()
        if stopper.ident is not None:
            stopper.join(2)
        engine.stop()
