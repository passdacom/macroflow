"""Windows HookPump lifecycle regressions with a deterministic fake user32 backend."""

from __future__ import annotations

import importlib
import sys
import threading
from collections import deque
from collections.abc import Iterator
from typing import Any

import pytest

if sys.platform != "win32":
    pytest.skip("requires the Windows hooks module", allow_module_level=True)

hooks: Any = importlib.import_module("macroflow.win32.hooks")


class _FakeKernel32:
    def GetCurrentThreadId(self) -> int:  # noqa: N802
        return 123

    def GetModuleHandleW(self, _name: object) -> None:  # noqa: N802
        return None


class _FakeUser32:
    def __init__(self, hook_ids: list[int]) -> None:
        self._hook_ids = iter(hook_ids)
        self.bootstrap_requested = threading.Event()
        self.bootstrap_consumed = False
        self.quit_requested = threading.Event()
        self.unhooked: list[int] = []

    def PeekMessageW(self, *_args: object) -> int:  # noqa: N802
        return 0

    def SetWindowsHookExW(self, *_args: object) -> int:  # noqa: N802
        return next(self._hook_ids)

    def GetMessageW(self, *_args: object) -> int:  # noqa: N802
        if self.bootstrap_requested.is_set() and not self.bootstrap_consumed:
            self.bootstrap_consumed = True
            return 1
        self.quit_requested.wait(timeout=2.0)
        return 0

    def TranslateMessage(self, *_args: object) -> int:  # noqa: N802
        return 1

    def DispatchMessageW(self, *_args: object) -> int:  # noqa: N802
        return 1

    def PostThreadMessageW(self, *_args: object) -> int:  # noqa: N802
        message = _args[1]
        if message == hooks.WM_QUIT:
            self.quit_requested.set()
        else:
            self.bootstrap_requested.set()
        return 1

    def UnhookWindowsHookEx(self, hook_id: int) -> int:  # noqa: N802
        self.unhooked.append(hook_id)
        return 1


@pytest.fixture(autouse=True)
def _reset_hook_state(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setattr(hooks, "_kernel32", _FakeKernel32())
    hooks._event_queue = None
    hooks._mouse_hook_id = None
    hooks._keyboard_hook_id = None
    hooks._pump_thread = None
    hooks._pump_tid = 0
    hooks._hook_ready = threading.Event()
    hooks._hook_start_error = None
    hooks._hook_cancel_start = threading.Event()
    hooks._emg_hook_id = None
    hooks._emg_pump_thread = None
    hooks._emg_pump_tid = 0
    hooks._emg_hook_ready = threading.Event()
    hooks._emg_hook_start_error = None
    hooks._emg_hook_cancel_start = threading.Event()
    hooks._emg_callback = None
    yield
    worker = hooks._pump_thread
    if worker is not None and worker.is_alive():
        try:
            hooks.stop_hook()
        except RuntimeError:
            pass
    hooks._pump_thread = None
    hooks._event_queue = None
    hooks._pump_tid = 0
    hooks._emg_pump_thread = None
    hooks._emg_pump_tid = 0
    hooks._emg_callback = None


def test_partial_registration_rolls_back_the_registered_hook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user32 = _FakeUser32([101, 0])
    monkeypatch.setattr(hooks, "_user32", user32)

    hooks._message_pump()

    assert hooks._hook_ready.is_set()
    assert hooks._hook_start_error == "Hook registration failed: keyboard"
    assert user32.unhooked == [101]
    assert hooks._mouse_hook_id is None
    assert hooks._keyboard_hook_id is None


def test_start_waits_for_both_hooks_and_stop_reaps_the_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user32 = _FakeUser32([101, 202])
    monkeypatch.setattr(hooks, "_user32", user32)
    queue: deque[tuple[str, int, int, tuple[int, int, int]]] = deque()

    hooks.start_hook(queue)

    worker: Any = hooks._pump_thread
    assert worker is not None and worker.is_alive()
    assert hooks._hook_start_error is None
    assert hooks._event_queue is queue

    hooks.stop_hook()

    assert user32.unhooked == [101, 202]
    assert hooks._pump_thread is None
    assert hooks._event_queue is None


def test_stop_timeout_keeps_hook_worker_and_queue_for_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StuckThread:
        def __init__(self) -> None:
            self.join_timeouts: list[float | None] = []

        def is_alive(self) -> bool:
            return True

        def join(self, timeout: float | None = None) -> None:
            self.join_timeouts.append(timeout)

    user32 = _FakeUser32([])
    worker = StuckThread()
    queue: deque[tuple[str, int, int, tuple[int, int, int]]] = deque()
    monkeypatch.setattr(hooks, "_user32", user32)
    hooks._pump_tid = 123
    hooks._pump_thread = worker
    hooks._event_queue = queue

    with pytest.raises(RuntimeError, match="did not stop"):
        hooks.stop_hook()

    assert worker.join_timeouts == [2.0]
    assert hooks._pump_thread is worker
    assert hooks._event_queue is queue


def test_start_timeout_keeps_unreaped_worker_and_queue_poisoned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class StuckThread:
        def __init__(self) -> None:
            self.join_timeouts: list[float | None] = []

        def start(self) -> None:
            hooks._pump_tid = 123

        def is_alive(self) -> bool:
            return True

        def join(self, timeout: float | None = None) -> None:
            self.join_timeouts.append(timeout)

    class FailedShutdownUser32(_FakeUser32):
        def PostThreadMessageW(self, *_args: object) -> int:  # noqa: N802
            return 0

    worker = StuckThread()
    queue: deque[tuple[str, int, int, tuple[int, int, int]]] = deque()
    monkeypatch.setattr(hooks, "_user32", FailedShutdownUser32([]))
    monkeypatch.setattr(hooks, "_HOOK_START_TIMEOUT_S", 0.0)
    monkeypatch.setattr(hooks.threading, "Thread", lambda **_kwargs: worker)

    with pytest.raises(RuntimeError, match="shutdown request failed"):
        hooks.start_hook(queue)

    assert worker.join_timeouts == [2.0]
    assert hooks._pump_thread is worker
    assert hooks._event_queue is queue
    assert hooks._hook_cancel_start.is_set()


def test_emergency_hook_registration_failure_is_reported_and_cleaned(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user32 = _FakeUser32([0])
    monkeypatch.setattr(hooks, "_user32", user32)

    with pytest.raises(RuntimeError, match="Emergency keyboard hook registration failed"):
        hooks.start_emergency_hook(lambda: None)

    assert hooks._emg_hook_id is None
    assert hooks._emg_pump_thread is None
    assert hooks._emg_callback is None


def test_message_pump_error_during_readiness_is_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MessageErrorUser32(_FakeUser32):
        def GetMessageW(self, *_args: object) -> int:  # noqa: N802
            return -1

    user32 = MessageErrorUser32([101, 202])
    monkeypatch.setattr(hooks, "_user32", user32)

    with pytest.raises(RuntimeError, match="failed during readiness probe"):
        hooks.start_hook(deque())

    assert user32.unhooked == [101, 202]
    assert hooks._pump_thread is None
    assert hooks._event_queue is None
