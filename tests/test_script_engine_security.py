"""Expression sandbox resource-safety regression tests."""

from __future__ import annotations

import threading
import time

import pytest

from macroflow.script_engine import _validate_expression, execute_condition
from macroflow.types import ConditionEvent, WaitEvent


def _condition(expression: str) -> ConditionEvent:
    return ConditionEvent(
        id="condition",
        type="condition",
        timestamp_ns=0,
        expression=expression,
        if_true=[
            WaitEvent(
                id="true-branch",
                type="wait",
                timestamp_ns=0,
                duration_ms=0,
            )
        ],
        if_false=[],
    )


def test_expression_rejects_sequence_multiplication_amplification() -> None:
    with pytest.raises(ValueError, match="sequence 반복"):
        _validate_expression("[0] * 1_000_000_000")


def test_expression_keeps_numeric_multiplication_available() -> None:
    _validate_expression("random() * 100 > 50")


def test_expression_rejects_literal_wait_over_budget() -> None:
    with pytest.raises(ValueError, match="wait 시간 초과"):
        _validate_expression("wait(60_001)")


def test_condition_wait_is_interrupted_by_stop_signal() -> None:
    stop_flag = threading.Event()
    executed: list[str] = []
    worker = threading.Thread(
        target=execute_condition,
        args=(
            _condition("wait(500) or True"),
            stop_flag,
            lambda event: executed.append(event.id),
        ),
        daemon=True,
    )
    worker.start()
    time.sleep(0.05)

    started = time.perf_counter()
    stop_flag.set()
    worker.join(timeout=0.2)
    elapsed = time.perf_counter() - started

    assert not worker.is_alive()
    assert elapsed < 0.2
    assert executed == []


def test_condition_enforces_cumulative_wait_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import script_engine

    monkeypatch.setattr(script_engine, "_MAX_EXPRESSION_WAIT_MS", 5.0)
    false_branch = WaitEvent(
        id="false-branch",
        type="wait",
        timestamp_ns=0,
        duration_ms=0,
    )
    event = ConditionEvent(
        id="condition",
        type="condition",
        timestamp_ns=0,
        expression="wait(3) or wait(3) or True",
        if_true=[],
        if_false=[false_branch],
    )
    executed: list[str] = []

    execute_condition(
        event,
        threading.Event(),
        lambda sub_event: executed.append(sub_event.id),
    )

    assert executed == ["false-branch"]
