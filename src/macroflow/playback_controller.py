"""Qt-free ownership and repeat orchestration for ordinary macro playback.

The player owns one input worker; this service owns a whole repeat request.
A player callback is not a join: every cycle waits for its owned worker to exit.
"""
from __future__ import annotations

import dataclasses
import logging
import threading
import time
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal

from macroflow.types import MacroData

if TYPE_CHECKING:
    from macroflow.player import PlaybackSession

logger = logging.getLogger(__name__)

@dataclasses.dataclass
class RepeatPlaybackSession:
    """State for one full repeat playback request.

    `cycle_index` is zero-based internally; user-facing labels are one-based.
    """

    total: int
    cycle_index: int = 0
    is_active: bool = False
    _stop_requested: threading.Event = dataclasses.field(default_factory=threading.Event)
    _start_gate: threading.Lock = dataclasses.field(
        default_factory=threading.Lock, init=False, repr=False
    )

    def mark_started(self) -> None:
        """Mark the repeat worker as active."""
        with self._start_gate:
            self.is_active = True
            self._stop_requested.clear()
            self.cycle_index = 0

    def mark_cycle_started(self, cycle_index: int) -> None:
        """Update the currently running repeat cycle."""
        self.is_active = True
        self.cycle_index = cycle_index

    def mark_between_cycles(self) -> None:
        """Keep the session active while no player thread is alive between cycles."""
        self.is_active = True

    def mark_finished(self) -> None:
        """Mark repeat playback as fully finished."""
        self.is_active = False

    def request_stop(self) -> None:
        """Request complete repeat-session stop, not just current cycle stop."""
        # Serialize with ``start_player_if_allowed`` so this method cannot
        # return while a worker is still between its final stop check and the
        # actual player start call.
        with self._start_gate:
            self._stop_requested.set()

    def start_player_if_allowed(self, start_player: Callable[[], object]) -> bool:
        """Atomically reject a stopped cycle or start its player.

        The callback must only perform the short player-start operation; it is
        intentionally invoked while the gate is held so ``request_stop`` can
        never report success before an in-flight start has completed.
        """
        with self._start_gate:
            if self._stop_requested.is_set():
                return False
            start_player()
            return True

    @property
    def was_stopped(self) -> bool:
        """Return whether a complete repeat-session stop was requested."""
        return self._stop_requested.is_set()

    @property
    def cycle_label(self) -> str:
        """Return user-facing repeat cycle label, e.g. '3/10회'."""
        total = max(1, self.total)
        current = min(max(0, self.cycle_index) + 1, total)
        return f"{current}/{total}회"

    def should_start_cycle(self, cycle_index: int) -> bool:
        """Return True when the repeat worker may start the given cycle."""
        return not self._stop_requested.is_set() and cycle_index < self.total

    def should_poll_wait_for_worker(self, *, player_is_playing: bool) -> bool:
        """Return True when UI polling should not complete playback yet.

        During repeat playback, the single-cycle player can be briefly inactive
        between cycles. The UI must keep overlay/state alive until the repeat
        worker itself finishes.
        """
        return self.is_active and not self.was_stopped and not player_is_playing


@dataclasses.dataclass(frozen=True)
class PlaybackOutcome:
    status: Literal["completed", "stopped", "failed"]
    error: BaseException | None = None


class PlaybackController:
    """One-shot repeat request, with an injectable player and active-time clock.

    Callbacks execute on the controller worker and must marshal UI work themselves.
    Stop serializes against player startup and only targets this request's handle.
    """

    def __init__(
        self,
        macro: MacroData,
        *,
        speed: float = 1.0,
        repeat_count: int = 1,
        interval_ms: int = 0,
        event_range: tuple[int, int] | None = None,
        on_event: Callable[[int, object], None] | None = None,
        on_cycle: Callable[[int, int], None] | None = None,
        on_finished: Callable[[PlaybackOutcome], None] | None = None,
        backend: Any = None,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        if backend is None:
            from macroflow import player
            backend = player
        self.session = RepeatPlaybackSession(total=max(1, repeat_count))
        self._backend = backend
        self._macro = macro
        self._speed = speed
        self._interval_s = max(0, interval_ms) / 1000
        self._event_range = event_range
        self._on_event = on_event
        self._on_cycle = on_cycle
        self._on_finished = on_finished
        self._monotonic = monotonic
        self._condition = threading.Condition(threading.RLock())
        self._paused = False
        self._pause_started = 0.0
        self._paused_time = 0.0
        self._player_session: PlaybackSession | None = None
        self._thread: threading.Thread | None = None
        self.outcome: PlaybackOutcome | None = None

    def start(self) -> None:
        with self._condition:
            if self._thread is not None or self.outcome is not None:
                raise RuntimeError("PlaybackController is a one-shot request")
            self.session.mark_started()
            self._thread = threading.Thread(target=self._run, daemon=True, name="RepeatPlayWorker")
            try:
                self._thread.start()
            except BaseException as exc:
                self._finish(PlaybackOutcome("failed", exc))

    def _active_now(self) -> float:
        now = self._pause_started if self._paused else self._monotonic()
        return now - self._paused_time

    def pause(self) -> None:
        with self._condition:
            if not self._paused:
                self._pause_started = self._monotonic()
                self._paused = True
                if self._player_session is not None:
                    self._backend.pause(session=self._player_session)
                self._condition.notify_all()

    def resume(self) -> None:
        with self._condition:
            if self._paused:
                self._paused_time += self._monotonic() - self._pause_started
                self._paused = False
                if self._player_session is not None:
                    self._backend.resume(session=self._player_session)
                self._condition.notify_all()

    def stop(self, timeout: float = 3.0) -> bool:
        with self._condition:
            self.session.request_stop()
            if self._thread is None:
                if self.outcome is None:
                    self._finish(PlaybackOutcome("stopped"))
                return True
            owned = self._player_session
            self._condition.notify_all()
        if owned is not None:
            self._backend.stop(session=owned)
        return self.wait(timeout)

    def wait(self, timeout: float | None = None) -> bool:
        thread = self._thread
        if thread is not None and thread.ident is not None:
            if thread is threading.current_thread():
                return False
            thread.join(timeout)
            return not thread.is_alive()
        return self.outcome is not None

    def _wait_active(self, duration: float) -> bool:
        with self._condition:
            deadline = self._active_now() + duration
            while not self.session.was_stopped:
                remaining = deadline - self._active_now()
                if not self._paused and remaining <= 0:
                    return True
                self._condition.wait(0.05 if self._paused else min(0.05, remaining))
            return False

    def _run(self) -> None:
        outcome = PlaybackOutcome("completed")
        try:
            for cycle in range(self.session.total):
                if not self._wait_active(0):
                    outcome = PlaybackOutcome("stopped")
                    break
                self.session.mark_cycle_started(cycle)
                if self._on_cycle is not None:
                    self._on_cycle(cycle + 1, self.session.total)
                with self._condition:
                    def start_player() -> None:
                        self._player_session = self._backend.play(
                            self._macro, speed=self._speed, event_range=self._event_range,
                            on_event_start=self._on_event,
                            start_pause_requested=lambda: self._paused,
                        )
                    if not self.session.start_player_if_allowed(start_player):
                        outcome = PlaybackOutcome("stopped")
                        break
                    owned = self._player_session
                assert owned is not None
                # Includes terminal callbacks and input cleanup, not just event dispatch.
                self._backend.wait_for_exit(owned)
                with self._condition:
                    self._player_session = None
                if owned.error is not None:
                    outcome = PlaybackOutcome("failed", owned.error)
                    break
                if self.session.was_stopped or owned.result == "stopped":
                    outcome = PlaybackOutcome("stopped")
                    break
                if owned.result != "completed":
                    raise RuntimeError("Player exited without a successful terminal result")
                if cycle + 1 < self.session.total:
                    self.session.mark_between_cycles()
                    if not self._wait_active(self._interval_s):
                        outcome = PlaybackOutcome("stopped")
                        break
        except BaseException as exc:
            outcome = PlaybackOutcome("failed", exc)
        finally:
            self._finish(outcome)

    def _finish(self, outcome: PlaybackOutcome) -> None:
        self.session.mark_finished()
        self.outcome = outcome
        if self._on_finished is not None:
            try:
                self._on_finished(outcome)
            except BaseException:
                # A notification failure must not create a second terminal outcome.
                logger.exception("Playback terminal notification failed")
