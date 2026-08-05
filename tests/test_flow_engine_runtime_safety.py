"""FlowEngine lifecycle and terminal-callback regression tests."""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import pytest

from macroflow.script_engine import (
    ColorCheckNode,
    EndNode,
    FlowEngine,
    InlineEventsNode,
    MacroFlow,
    MacroNode,
    WaitFixedNode,
    load_flow,
    save_flow,
)
from macroflow.types import MacroSettings, TextInputEvent


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


def test_error_end_reports_failure_without_success_completion(tmp_path: Path) -> None:
    completed: list[str] = []
    errors: list[str] = []
    done_calls: list[tuple[str, bool, str]] = []
    flow = MacroFlow(
        version="1.0",
        name="error end",
        created_at="2026-07-24T00:00:00",
        start_node_id="end_error",
        nodes={
            "end_error": EndNode(
                id="end_error",
                label="error",
                status="error",
            )
        },
    )
    engine = FlowEngine(
        str(tmp_path / "sequence.macroflow"),
        on_node_done=lambda *args: done_calls.append(args),
        on_complete=completed.append,
        on_error=errors.append,
    )

    engine._run(flow)

    assert done_calls == [("end_error", False, "error")]
    assert completed == []
    assert errors == ["플로우가 오류 상태로 종료되었습니다: error"]


def test_host_callback_exceptions_do_not_corrupt_terminal_state(tmp_path: Path) -> None:
    completed: list[str] = []
    flow = MacroFlow(
        version="1.0",
        name="callback safety",
        created_at="2026-07-24T00:00:00",
        start_node_id="end",
        nodes={"end": EndNode(id="end", label="완료", status="success")},
    )
    engine = FlowEngine(
        str(tmp_path / "callback.macroflow"),
        on_node_start=lambda *_args: (_ for _ in ()).throw(RuntimeError("start UI")),
        on_node_done=lambda *_args: (_ for _ in ()).throw(RuntimeError("done UI")),
        on_complete=completed.append,
    )

    engine._run(flow)

    assert completed == ["success"]


def test_stop_interrupts_fixed_wait_without_stopping_unowned_player(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import player

    player_stop_calls: list[object] = []
    monkeypatch.setattr(player, "stop", lambda *args: player_stop_calls.append(args))
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
    assert player_stop_calls == []


def test_color_timeout_without_failure_edge_is_terminal_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import win32

    monkeypatch.setattr(win32, "ratio_to_pixel", lambda _x, _y: (0, 0))
    monkeypatch.setattr(win32, "get_pixel_color", lambda _x, _y: (0, 0, 0))
    done_calls: list[tuple[str, bool, str]] = []
    completed: list[str] = []
    errors: list[str] = []
    flow = MacroFlow(
        version="1.0",
        name="color timeout",
        created_at="2026-07-24T00:00:00",
        start_node_id="color",
        nodes={
            "color": ColorCheckNode(
                id="color",
                label="color",
                x_ratio=0.0,
                y_ratio=0.0,
                target_color="#FFFFFF",
                timeout_ms=1,
                check_interval_ms=1,
                on_timeout=None,
            )
        },
    )
    engine = FlowEngine(
        str(tmp_path / "color.macroflow"),
        on_node_done=lambda *args: done_calls.append(args),
        on_complete=completed.append,
        on_error=errors.append,
    )

    engine._run(flow)

    assert done_calls == [("color", False, "색 감지 타임아웃")]
    assert completed == []
    assert errors == ["색 감지 타임아웃"]


def test_strict_flow_rejects_invalid_color_domain_values(tmp_path: Path) -> None:
    flow = MacroFlow(
        version="1.0",
        name="invalid color",
        created_at="2026-08-05T00:00:00",
        start_node_id="color",
        nodes={
            "color": ColorCheckNode(
                id="color",
                label="color",
                x_ratio=0.5,
                y_ratio=0.5,
                target_color="BAD",
                tolerance=-1,
                timeout_ms=-1,
                check_interval_ms=0,
            )
        },
    )
    path = tmp_path / "invalid-color.macroflow"
    path.write_text(json.dumps({
        "meta": {
            "version": flow.version,
            "name": flow.name,
            "created_at": flow.created_at,
        },
        "start_node_id": flow.start_node_id,
        "nodes": {
            "color": {
                "id": "color",
                "type": "color_check",
                "label": "color",
                "position": {},
                "x_ratio": 0.5,
                "y_ratio": 0.5,
                "target_color": "BAD",
                "tolerance": -1,
                "timeout_ms": -1,
                "check_interval_ms": 0,
                "on_match": None,
                "on_timeout": None,
            }
        },
    }), encoding="utf-8")

    with pytest.raises(ValueError, match="정규 형식"):
        load_flow(str(path), strict=True)


def test_save_flow_rejects_strict_invalid_flow_without_replacing_last_good(
    tmp_path: Path,
) -> None:
    path = tmp_path / "last-good.macroflow"
    good = MacroFlow(
        version="1.0",
        name="good",
        created_at="now",
        start_node_id="wait",
        nodes={
            "wait": WaitFixedNode(
                id="wait", label="wait", duration_ms=1, next=None
            )
        },
    )
    save_flow(good, str(path))
    original = path.read_bytes()
    invalid = MacroFlow(
        version="1.0",
        name="invalid",
        created_at="now",
        start_node_id="color",
        nodes={
            "color": ColorCheckNode(
                id="color",
                label="color",
                x_ratio=0.5,
                y_ratio=0.5,
                target_color="BAD",
                tolerance=-1,
                timeout_ms=-1,
                check_interval_ms=0,
            )
        },
    )

    with pytest.raises(ValueError, match="정규 형식"):
        save_flow(invalid, str(path))

    assert path.read_bytes() == original
    assert load_flow(str(path), strict=True) == good


def test_unexpected_node_error_reports_failed_node_done_once(tmp_path: Path) -> None:
    flow = MacroFlow(
        version="1.0",
        name="runtime invalid color",
        created_at="2026-08-05T00:00:00",
        start_node_id="color",
        nodes={
            "color": ColorCheckNode(
                id="color",
                label="color",
                x_ratio=0.5,
                y_ratio=0.5,
                target_color="BAD",
                timeout_ms=1,
                check_interval_ms=1,
            )
        },
    )
    done_calls: list[tuple[str, bool, str]] = []
    errors: list[str] = []
    engine = FlowEngine(
        str(tmp_path / "runtime-invalid.macroflow"),
        on_node_done=lambda *args: done_calls.append(args),
        on_error=errors.append,
    )

    engine._run(flow)

    assert len(done_calls) == 1
    assert done_calls[0][0:2] == ("color", False)
    assert len(errors) == 1


def test_synchronous_player_start_failure_reports_node_done_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import player

    monkeypatch.setattr(
        player,
        "play",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("start boom")),
    )
    flow = MacroFlow(
        version="1.1",
        name="start failure",
        created_at="2026-07-24T00:00:00",
        start_node_id="inline",
        nodes={
            "inline": InlineEventsNode(
                id="inline",
                label="text",
                events=[
                    TextInputEvent(
                        id="text",
                        type="text_input",
                        timestamp_ns=0,
                        text="A",
                    )
                ],
                playback_settings=MacroSettings(),
                next_on_failure=None,
            )
        },
    )
    done_calls: list[tuple[str, bool, str]] = []
    completed: list[str] = []
    errors: list[str] = []
    engine = FlowEngine(
        str(tmp_path / "failure.macroflow"),
        on_node_done=lambda *args: done_calls.append(args),
        on_complete=completed.append,
        on_error=errors.append,
    )

    engine._run(flow)

    assert done_calls == [("inline", False, "start boom")]
    assert completed == []
    assert errors == ["start boom"]


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
    engine._player_session = player.PlaybackSession()

    stop_entered = threading.Event()
    release_stop = threading.Event()

    def blocking_stop(_session: player.PlaybackSession) -> bool:
        stop_entered.set()
        release_stop.wait(timeout=1.0)
        return True

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
