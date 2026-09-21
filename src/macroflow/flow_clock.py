"""Interruptible active-time clock for flow orchestration (not input ownership)."""
from __future__ import annotations

import threading
import time


class FlowClock:
    def __init__(self, stop: threading.Event) -> None:
        self.stop = stop
        self.condition = threading.Condition()
        self.paused = False
        self.started = 0.0
        self.excluded = 0.0

    def now(self) -> float:
        with self.condition:
            return (self.started if self.paused else time.monotonic()) - self.excluded

    def pause(self) -> None:
        with self.condition:
            if not self.paused:
                self.started = time.monotonic()
                self.paused = True
            self.condition.notify_all()

    def resume(self) -> None:
        with self.condition:
            if self.paused:
                self.excluded += time.monotonic() - self.started
                self.paused = False
            self.condition.notify_all()

    def wake(self) -> None:
        with self.condition:
            self.condition.notify_all()

    def wait(self, seconds: float = 0.0) -> bool:
        with self.condition:
            deadline = self.now() + max(0, seconds)
            while not self.stop.is_set():
                if self.paused:
                    self.condition.wait()
                    continue
                remaining = deadline - self.now()
                if remaining <= 0:
                    return True
                self.condition.wait(remaining)
            return False
