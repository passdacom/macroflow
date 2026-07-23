"""FlowEngine lifecycle and terminal-callback regression tests."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from macroflow.script_engine import (
    ColorCheckNode,
    EndNode,
    FlowEngine,
    MacroFlow,
    MacroNode,
    WaitFixedNode,
)


def test_missing_macro_reports_node_failure_once(tmp_path: Path) -> None:
    done_calls: list[tuple[str, bool, str]] = []
    errors: list[str] = []
    flow = MacroFlow(
        version="1.0",
        name="missing macro",
        created_at="2026-07-13T00:00:00",
        start_node_id="macro_000",
        nodes={
            "macro_000": MacroNode(
                id="macro_000",
                label="missing.json",
                macro_path="missing.json",
                next_on_success="end_success",
                next_on_failure="end_error",
            ),
            "end_success": EndNode(id="end_success", label="done"),
            "end_error": EndNode(id="end_error", label="error", status="error"),
        },
    )
    engine = FlowEngine(
        str(tmp_path / "sequence.macroflow"),
        on_node_done=lambda *args: done_calls.append(args),
        on_error=errors.append,
    )

    engine._run(flow)

    assert len(done_calls) == 1
    assert done_calls[0][0:2] == ("macro_000", False)
    assert len(errors) == 1


def test_stop_interrupts_fixed_wait_without_success_callback(tmp_path: Path) -> None:
    entered_wait = threading.Event()
    done_calls: list[tuple[str, bool, str]] = []
    flow = MacroFlow(
        version="1.0",
        name="interrupt wait",
        created_at="2026-07-13T00:00:00",
        start_node_id="wait_000",
        nodes={
            "wait_000": WaitFixedNode(
                id="wait_000",
                label="wait",
                duration_ms=500,
                next="end_success",
            ),
            "end_success": EndNode(id="end_success", label="done"),
        },
    )
    engine = FlowEngine(
        str(tmp_path / "sequence.macroflow"),
        on_node_start=lambda _node_id, _label: entered_wait.set(),
        on_node_done=lambda *args: done_calls.append(args),
    )
    engine.start(flow)
    assert entered_wait.wait(timeout=0.5)

    started = time.perf_counter()
    engine.stop()
    elapsed = time.perf_counter() - started

    assert elapsed < 0.2
    assert not engine.is_running()
    assert done_calls == []


def test_stop_interrupts_color_check_poll_without_callback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import win32

    entered_poll = threading.Event()
    done_calls: list[tuple[str, bool, str]] = []
    monkeypatch.setattr(win32, "ratio_to_pixel", lambda _x, _y: (0, 0))

    def _get_pixel_color(_x: int, _y: int) -> tuple[int, int, int]:
        entered_poll.set()
        return (0, 0, 0)

    monkeypatch.setattr(win32, "get_pixel_color", _get_pixel_color)
    flow = MacroFlow(
        version="1.0",
        name="interrupt color poll",
        created_at="2026-07-13T00:00:00",
        start_node_id="color_000",
        nodes={
            "color_000": ColorCheckNode(
                id="color_000",
                label="color",
                x_ratio=0.0,
                y_ratio=0.0,
                target_color="#FFFFFF",
                timeout_ms=5_000,
                check_interval_ms=500,
                on_timeout="end_error",
            ),
            "end_error": EndNode(id="end_error", label="error", status="error"),
        },
    )
    engine = FlowEngine(
        str(tmp_path / "sequence.macroflow"),
        on_node_done=lambda *args: done_calls.append(args),
    )
    engine.start(flow)
    assert entered_poll.wait(timeout=0.5)

    started = time.perf_counter()
    engine.stop()
    elapsed = time.perf_counter() - started

    assert elapsed < 0.2
    assert not engine.is_running()
    assert done_calls == []


def test_duplicate_start_is_rejected_while_worker_is_alive(tmp_path: Path) -> None:
    entered = threading.Event()
    release = threading.Event()
    flow = MacroFlow(
        version="1.0",
        name="duplicate start",
        created_at="2026-07-23T00:00:00",
        start_node_id="end_success",
        nodes={"end_success": EndNode(id="end_success", label="done")},
    )
    engine = FlowEngine(str(tmp_path / "sequence.macroflow"))

    def blocking_run(_flow: MacroFlow) -> None:
        entered.set()
        release.wait(timeout=1.0)

    engine._run = blocking_run  # type: ignore[method-assign]
    engine.start(flow)
    assert entered.wait(timeout=0.5)
    first_thread = engine._thread

    try:
        with pytest.raises(RuntimeError, match="already running"):
            engine.start(flow)
        assert engine._thread is first_thread
    finally:
        release.set()
        engine.stop()


def test_stop_timeout_keeps_worker_handle_and_blocks_restart(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import player

    class TimedOutThread:
        def __init__(self) -> None:
            self.alive = True
            self.join_timeouts: list[float | None] = []

        def is_alive(self) -> bool:
            return self.alive

        def join(self, timeout: float | None = None) -> None:
            self.join_timeouts.append(timeout)

    flow = MacroFlow(
        version="1.0",
        name="stop timeout",
        created_at="2026-07-23T00:00:00",
        start_node_id="end_success",
        nodes={"end_success": EndNode(id="end_success", label="done")},
    )
    engine = FlowEngine(str(tmp_path / "sequence.macroflow"))
    worker = TimedOutThread()
    engine._thread = worker  # type: ignore[assignment]
    monkeypatch.setattr(player, "stop", lambda: None)

    engine.stop()

    assert engine._thread is worker
    assert worker.join_timeouts == [5.0]
    assert engine.is_running()
    with pytest.raises(RuntimeError, match="already running"):
        engine.start(flow)
    assert engine._thread is worker

    worker.alive = False
    engine.start(flow)
    restarted_worker = engine._thread
    assert restarted_worker is not None
    assert restarted_worker is not worker
    restarted_worker.join(timeout=0.5)
    assert not restarted_worker.is_alive()


def test_restart_is_rejected_until_concurrent_stop_returns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import player

    flow = MacroFlow(
        version="1.0",
        name="concurrent stop",
        created_at="2026-07-23T00:00:00",
        start_node_id="end_success",
        nodes={"end_success": EndNode(id="end_success", label="done")},
    )
    engine = FlowEngine(str(tmp_path / "sequence.macroflow"))
    engine.start(flow)
    assert engine._thread is not None
    engine._thread.join(timeout=0.5)
    assert not engine._thread.is_alive()

    stop_entered = threading.Event()
    release_stop = threading.Event()

    def blocking_stop() -> None:
        stop_entered.set()
        release_stop.wait(timeout=1.0)

    monkeypatch.setattr(player, "stop", blocking_stop)
    stopper = threading.Thread(target=engine.stop)
    stopper.start()
    assert stop_entered.wait(timeout=0.5)

    with pytest.raises(RuntimeError, match="already running"):
        engine.start(flow)

    release_stop.set()
    stopper.join(timeout=0.5)
    assert not stopper.is_alive()

    engine.start(flow)
    assert engine._thread is not None
    engine._thread.join(timeout=0.5)
    assert not engine._thread.is_alive()
