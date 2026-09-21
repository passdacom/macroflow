"""Public player barrier tests: all native reads/inputs are synthetic mocks."""
import threading

import pytest

from macroflow import player
from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
)


def macro(kind):
    events: list[AnyEvent]
    if kind == "trigger":
        events = [ColorTriggerEvent(id="color", type="color_trigger", timestamp_ns=0,
            x_ratio=.5, y_ratio=.5, target_color="#FFFFFF", timeout_ms=0, check_interval_ms=1)]
    else:
        events = [MouseButtonEvent(id="down", type="mouse_down", timestamp_ns=0,
            x_ratio=.5, y_ratio=.5, button="left", recorded_color="#FFFFFF",
            color_check_enabled=True, color_check_on_mismatch="stop"),
            MouseButtonEvent(id="up", type="mouse_up", timestamp_ns=0,
                x_ratio=.5, y_ratio=.5, button="left")]
    return MacroData(meta=MacroMeta(version="1.0", app_version="1.11.0", created_at="",
        screen_width=1920, screen_height=1080, dpi_scale=1.0),
        settings=MacroSettings(color_check_click_stop_timeout_ms=0,
                               color_check_click_interval_ms=1), events=events, raw_events=[])


@pytest.fixture(autouse=True)
def native_safe(monkeypatch):
    player.stop()
    for name in ("send_mouse_move", "send_mouse_button", "send_mouse_wheel", "send_mouse_drag",
                 "send_key", "send_paste", "set_clipboard_text", "find_window"):
        monkeypatch.setattr(player, name, lambda *a, **kw: None)
    monkeypatch.setattr(player, "ratio_to_pixel", lambda *a: (100, 100))
    monkeypatch.setattr(player, "get_pixel_color", lambda *a: (255, 255, 255))
    yield
    player.stop()


@pytest.mark.parametrize("kind", ["trigger", "click"])
def test_coordinate_lookup_pause_defers_move_and_resume_keeps_event(monkeypatch, kind):
    lookup, release, boundary = (threading.Event() for _ in range(3))
    moves, completed, errors = [], [], []
    real_gate = player._playback_clock.wait_until_resumed

    def ratio(*args):
        lookup.set()
        assert release.wait(2)
        return 100, 100

    def gate():
        if release.is_set():
            boundary.set()
        return real_gate()

    def move(x, y):
        moves.append((x, y, player.is_paused()))
        boundary.set()

    monkeypatch.setattr(player, "ratio_to_pixel", ratio)
    monkeypatch.setattr(player._playback_clock, "wait_until_resumed", gate)
    monkeypatch.setattr(player, "send_mouse_move", move)
    session = player.play(macro(kind), on_complete=lambda: completed.append(True), on_error=errors.append)
    try:
        assert lookup.wait(2)
        assert player.pause()
        release.set()
        assert boundary.wait(2)
        assert moves == [], "coordinate lookup must end at the final atomic input gate"
        assert player.resume()
        assert player.wait_for_exit(session, 2)
        assert completed == [True] and not errors
        assert moves and all(not paused for _, _, paused in moves)
    finally:
        release.set()
        player.stop(session)


@pytest.mark.parametrize("kind", ["trigger", "click"])
@pytest.mark.parametrize("control", ["resume", "stop", "stop-running"])
def test_nudge_away_pause_retains_active_dwell_or_stop_cancels_return(monkeypatch, kind, control):
    # Pause in the actual dwell after some active time has elapsed. No lock is held
    # at this barrier; public pause and stop must remain callable from this thread.
    away, dwell, release = (threading.Event() for _ in range(3))
    moves, buttons, completed, errors = [], [], [], []
    real_wait_until = player._playback_clock.wait_until
    real_stop_wait = player._stop_flag.wait
    returned = threading.Event()
    dwell_start = []
    active_return = []
    monkeypatch.setattr(player, "_COLOR_WAIT_NUDGE_AFTER_NS", 0)
    monkeypatch.setattr(player, "_COLOR_WAIT_NUDGE_DWELL_S", .15)

    def move(x, y):
        moves.append((x, y, player.is_paused(), player._stop_flag.is_set()))
        if x == 92:
            dwell_start.append(player._active_now_ns())
            away.set()
        elif away.is_set():
            active_return.append(player._active_now_ns())
            returned.set()

    def wait_until(deadline):
        if away.is_set() and not dwell.is_set():
            assert real_wait_until(min(deadline, player._active_now_ns() + 20_000_000))
            dwell.set()
            assert release.wait(2)
        return real_wait_until(deadline)

    def stop_wait(timeout=None):
        if away.is_set() and not dwell.is_set():
            dwell.set()
            assert release.wait(2)
        return real_stop_wait(timeout)

    monkeypatch.setattr(player, "send_mouse_move", move)
    monkeypatch.setattr(player, "send_mouse_button", lambda *a, **kw: buttons.append((a, kw)))
    monkeypatch.setattr(player._playback_clock, "wait_until", wait_until)
    monkeypatch.setattr(player._stop_flag, "wait", stop_wait)
    monkeypatch.setattr(player, "get_pixel_color",
                        lambda *a: (255, 255, 255) if active_return else (0, 0, 0))
    session = player.play(macro(kind), on_complete=lambda: completed.append(True), on_error=errors.append)
    worker = player._playback_thread
    assert worker is not None
    try:
        assert away.wait(2)
        assert dwell.wait(.5), "nudge must use interruptible active-time dwell"
        if control != "stop-running":
            assert player.pause()
        count = len(moves)
        # Let paused wall time exceed the entire dwell; active remainder is retained.
        assert not threading.Event().wait(.2)
        assert len(moves) == count and not buttons and not completed
        if control == "resume":
            release.set()
            assert not returned.wait(.2), "return move must remain gated during pause"
            assert player.resume()
            assert player.wait_for_exit(session, 2)
            assert active_return[0] - dwell_start[0] >= 150_000_000
            assert completed == [True] and not errors
            assert len(buttons) == (2 if kind == "click" else 0)
        else:
            stopped = threading.Event()
            original_notify = player._playback_clock.notify_stop

            def notify():
                original_notify()
                stopped.set()

            monkeypatch.setattr(player._playback_clock, "notify_stop", notify)
            stopper = threading.Thread(target=player.stop, args=(session,))
            stopper.start()
            assert stopped.wait(2)
            release.set()
            stopper.join(2)
            assert not stopper.is_alive() and not worker.is_alive()
            assert not active_return and len(moves) == count
            assert not completed and not errors and not buttons
            assert player.wait_for_exit(session, 0)
        assert all(not paused and not stopped for _, _, paused, stopped in moves)
    finally:
        release.set()
        player.stop(session)


@pytest.mark.parametrize("kind", ["trigger", "click"])
def test_stop_during_coordinate_lookup_cancels_initial_move(monkeypatch, kind):
    lookup, release, stopping = (threading.Event() for _ in range(3))
    moves, completed = [], []

    def ratio(*args):
        lookup.set()
        assert release.wait(2)
        return 100, 100

    original_notify = player._playback_clock.notify_stop

    def notify():
        original_notify()
        stopping.set()

    monkeypatch.setattr(player, "ratio_to_pixel", ratio)
    monkeypatch.setattr(player, "send_mouse_move", lambda *a: moves.append(a))
    monkeypatch.setattr(player._playback_clock, "notify_stop", notify)
    session = player.play(macro(kind), on_complete=lambda: completed.append(True))
    worker = player._playback_thread
    assert worker is not None
    stopper = threading.Thread(target=player.stop, args=(session,))
    try:
        assert lookup.wait(2)
        stopper.start()
        assert stopping.wait(2)
        release.set()
        stopper.join(2)
        assert not stopper.is_alive() and not worker.is_alive()
        assert not moves and not completed
    finally:
        release.set()
        if stopper.ident is not None:
            stopper.join(2)
        player.stop(session)


@pytest.mark.parametrize("kind", ["trigger", "click"])
def test_deadline_recomputed_after_active_nudge_dwell(monkeypatch, kind):
    now = [0]
    waits, pixels = [], []

    def wait(seconds):
        waits.append(seconds)
        now[0] += round(seconds * 1_000_000_000)
        return True

    monkeypatch.setattr(player, "_active_now_ns", lambda: now[0])
    monkeypatch.setattr(player, "_wait_active", wait)
    monkeypatch.setattr(player, "_COLOR_WAIT_NUDGE_AFTER_NS", 0)
    monkeypatch.setattr(player, "get_pixel_color", lambda *a: pixels.append(a) or (0, 0, 0))
    if kind == "trigger":
        event = macro(kind).events[0]
        assert isinstance(event, ColorTriggerEvent)
        event.timeout_ms = 30
        event.on_timeout = "skip"
        player._wait_for_color(event)
        assert waits == [.05, .05]  # initial hover and dwell; no stale polling budget
    else:
        settings = MacroSettings(color_check_click_skip_timeout_ms=30)
        assert not player._wait_for_click_color_check(100, 100, (255, 255, 255), settings)
        assert waits == [.05]
    assert len(pixels) == 1
