"""Deterministic ownership tests for the Qt-free repeat controller."""
from __future__ import annotations

import threading
from types import SimpleNamespace

import pytest

from macroflow.playback_controller import PlaybackController


class FakePlayer:
    def __init__(self):
        self.calls = []
        self.started = threading.Condition()
        self.stops = []
        self.pauses = 0
        self.resumes = 0
        self.pause_owners = []
        self.resume_owners = []
        self.failure = None

    def play(self, macro, **kwargs):
        if self.failure:
            raise self.failure
        handle = SimpleNamespace(result=None, error=None, exited=threading.Event())
        with self.started:
            self.calls.append((handle, macro, kwargs))
            self.started.notify_all()
        return handle

    def wait_for_exit(self, handle):
        assert handle.exited.wait(2), "test did not release player worker"
        return True

    def stop(self, session):
        self.stops.append(session)
        self.finish(session, "stopped")

    def pause(self, session):
        self.pauses += 1
        self.pause_owners.append(session)

    def resume(self, session):
        self.resumes += 1
        self.resume_owners.append(session)

    def wait_start(self, count=1):
        with self.started:
            assert self.started.wait_for(lambda: len(self.calls) >= count, 1)
            return self.calls[count - 1][0]

    def finish(self, handle, result="completed", error=None):
        handle.result = result
        handle.error = error
        handle.exited.set()


def make_controller(**kwargs):
    backend = FakePlayer()
    outcomes = []
    controller = PlaybackController(object(), backend=backend, on_finished=outcomes.append, **kwargs)
    return controller, backend, outcomes


def test_repeat_waits_for_owned_worker_exit_and_forwards_options():
    controller, backend, outcomes = make_controller(repeat_count=2, speed=3, event_range=(2, 7))
    controller.start()
    first = backend.wait_start()
    # A terminal result is not proof that the worker has actually exited.
    first.result = "completed"
    assert len(backend.calls) == 1
    assert controller.session.is_active
    backend.finish(first)
    second = backend.wait_start(2)
    assert backend.calls[1][2]["event_range"] == (2, 7)
    assert backend.calls[1][2]["speed"] == 3
    backend.finish(second)
    assert controller.wait(1)
    assert [o.status for o in outcomes] == ["completed"]
    assert not controller.session.is_active


@pytest.mark.parametrize("status,error", [("failed", RuntimeError("cleanup")), ("stopped", None)])
def test_player_terminal_failure_or_stop_prevents_repeat(status, error):
    controller, backend, outcomes = make_controller(repeat_count=3)
    controller.start()
    backend.finish(backend.wait_start(), status, error)
    assert controller.wait(1)
    assert len(backend.calls) == 1
    assert outcomes[0].status == status
    assert outcomes[0].error is error
    assert not controller.session.is_active


def test_start_failure_finishes_once():
    controller, backend, outcomes = make_controller()
    backend.failure = ValueError("start failed")
    controller.start()
    assert controller.wait(1)
    assert len(outcomes) == 1
    assert outcomes[0].error is backend.failure
    assert not controller.session.is_active


def test_cycle_callback_failure_finishes_once_without_starting_player():
    def fail(*args):
        raise RuntimeError("cycle")
    controller, backend, outcomes = make_controller(on_cycle=fail)
    controller.start()
    assert controller.wait(1)
    assert outcomes[0].status == "failed"
    assert backend.calls == []
    assert not controller.session.is_active


def test_terminal_callback_failure_does_not_emit_second_outcome():
    controller, backend, outcomes = make_controller()
    def fail(outcome):
        outcomes.append(outcome)
        raise RuntimeError("notification")
    controller._on_finished = fail
    controller.start()
    backend.finish(backend.wait_start())
    assert controller.wait(1)
    assert len(outcomes) == 1
    assert not controller.session.is_active


def test_stop_before_first_cycle_while_paused_finishes_once():
    controller, backend, outcomes = make_controller(repeat_count=3)
    controller.pause()
    controller.start()
    assert controller.stop()
    assert not backend.calls
    assert not backend.stops
    assert [o.status for o in outcomes] == ["stopped"]
    assert not controller.session.is_active


def test_stop_targets_only_owned_player_and_blocks_next_cycle():
    controller, backend, outcomes = make_controller(repeat_count=3)
    controller.start()
    owned = backend.wait_start()
    controller.pause()
    controller.resume()
    assert controller.stop()
    assert backend.stops == [owned]
    assert backend.pauses == backend.resumes == 1
    assert backend.pause_owners == backend.resume_owners == [owned]
    assert len(backend.calls) == 1
    assert [o.status for o in outcomes] == ["stopped"]


def test_stop_serializes_with_player_start():
    controller, backend, outcomes = make_controller(repeat_count=3)
    entered, release, stopped = (threading.Event() for _ in range(3))
    original_play = backend.play
    def blocked_play(*args, **kwargs):
        entered.set()
        assert release.wait(1)
        return original_play(*args, **kwargs)
    backend.play = blocked_play
    controller.start()
    assert entered.wait(1)
    stopper = threading.Thread(target=lambda: (controller.stop(), stopped.set()))
    stopper.start()
    assert not stopped.wait(0.02)
    release.set()
    assert stopped.wait(1)
    stopper.join()
    assert len(backend.calls) == len(backend.stops) == 1
    assert len(outcomes) == 1


def test_interval_uses_active_time_and_stop_wakes_paused_interval():
    now = [0.0]
    controller, backend, outcomes = make_controller(repeat_count=3, interval_ms=1000, monotonic=lambda: now[0])
    between = threading.Event()
    original = controller.session.mark_between_cycles
    def mark_between():
        original()
        between.set()
    controller.session.mark_between_cycles = mark_between
    controller.start()
    backend.finish(backend.wait_start())
    assert between.wait(1)
    # Hold the condition while moving time so worker cannot observe partial updates.
    with controller._condition:
        now[0] = 0.4
        controller.pause()
        now[0] = 100.4
        assert controller._active_now() == pytest.approx(0.4)
        controller.resume()
        assert controller._active_now() == pytest.approx(0.4)
    assert len(backend.calls) == 1
    controller.pause()
    assert controller.stop()
    assert [o.status for o in outcomes] == ["stopped"]
    assert len(backend.calls) == 1


def test_one_shot_rejects_restart():
    controller, backend, _ = make_controller()
    controller.start()
    backend.finish(backend.wait_start())
    assert controller.wait(1)
    with pytest.raises(RuntimeError, match="one-shot"):
        controller.start()


def test_stop_before_start_cannot_be_cleared_by_later_start():
    controller, backend, outcomes = make_controller()
    assert controller.stop()
    with pytest.raises(RuntimeError, match="one-shot"):
        controller.start()
    assert not backend.calls
    assert [o.status for o in outcomes] == ["stopped"]


def test_thread_start_failure_is_terminal(monkeypatch):
    controller, backend, outcomes = make_controller()
    def fail_start(self):
        raise RuntimeError("thread unavailable")
    monkeypatch.setattr(threading.Thread, "start", fail_start)
    controller.start()
    assert controller.wait(0)
    assert [o.status for o in outcomes] == ["failed"]
    assert not controller.session.is_active
    assert not backend.calls


def test_event_callback_is_forwarded_and_missing_terminal_result_fails():
    events = []
    controller, backend, outcomes = make_controller(on_event=lambda *event: events.append(event))
    controller.start()
    handle = backend.wait_start()
    backend.calls[0][2]["on_event_start"](7, "event")
    backend.finish(handle, None)
    assert controller.wait(1)
    assert events == [(7, "event")]
    assert [o.status for o in outcomes] == ["failed"]


def test_interval_deadline_excludes_entire_pause_duration():
    now = [0.0]
    controller, _, _ = make_controller(monotonic=lambda: now[0])
    waiting, finished = threading.Event(), threading.Event()
    original_wait = controller._condition.wait
    def wait(timeout=None):
        waiting.set()
        return original_wait(timeout)
    controller._condition.wait = wait
    thread = threading.Thread(target=lambda: (controller._wait_active(1), finished.set()))
    thread.start()
    assert waiting.wait(1)
    with controller._condition:
        now[0] = 0.4
        controller.pause()
        now[0] = 100.4
        controller.resume()
        now[0] = 100.9
        controller._condition.notify_all()
    assert not finished.wait(0.02)
    with controller._condition:
        now[0] = 101.0
        controller._condition.notify_all()
    assert finished.wait(1)
    thread.join()


def real_macro(duration_ms=1):
    from macroflow.types import MacroData, MacroMeta, MacroSettings, WaitEvent
    event = WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=duration_ms)
    return MacroData(
        meta=MacroMeta(version="1", app_version="test", created_at="now",
                      screen_width=1920, screen_height=1080, dpi_scale=1),
        settings=MacroSettings(), raw_events=[event], events=[event],
    )


def test_real_player_repeat_uses_terminal_result_and_exits():
    from macroflow import player
    cycles, outcomes = [], []
    controller = PlaybackController(real_macro(), repeat_count=3,
                                    on_cycle=lambda *cycle: cycles.append(cycle),
                                    on_finished=outcomes.append)
    controller.start()
    assert controller.wait(2)
    assert cycles == [(1, 3), (2, 3), (3, 3)]
    assert [o.status for o in outcomes] == ["completed"]
    assert not player.is_playing()


def test_stale_controller_pause_resume_cannot_affect_new_player():
    from macroflow import player
    old_exited, release_join = threading.Event(), threading.Event()
    def delayed_wait(session):
        result = player.wait_for_exit(session)
        old_exited.set()
        assert release_join.wait(2)
        return result
    backend = SimpleNamespace(play=player.play, wait_for_exit=delayed_wait,
                              stop=player.stop, pause=player.pause, resume=player.resume)
    controller = PlaybackController(real_macro(), backend=backend)
    controller.start()
    assert old_exited.wait(1)
    replacement = player.play(real_macro(10000))
    try:
        controller.pause()
        assert not player.is_paused()
        player.pause(session=replacement)
        assert player.is_paused()
        controller.resume()
        assert player.is_paused()
    finally:
        release_join.set()
        player.stop(session=replacement)
        assert controller.wait(1)
