"""Pure expression-sandbox module boundaries and compatibility contracts."""

from __future__ import annotations

import subprocess
import sys

import pytest


def test_expression_sandbox_imports_without_script_engine_or_pyqt() -> None:
    script = """
import sys
from macroflow.expression_sandbox import validate_expression, validate_wait_ms

validate_expression("random() * 100 > 50")
assert validate_wait_ms(25, maximum=100) == 25.0
assert "macroflow.script_engine" not in sys.modules
assert not any(name == "PyQt6" or name.startswith("PyQt6.") for name in sys.modules)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr


def test_expression_sandbox_public_validator_preserves_security_rules() -> None:
    from macroflow.expression_sandbox import validate_expression

    with pytest.raises(ValueError, match="sequence 반복"):
        validate_expression("[0] * 1_000_000_000")
    with pytest.raises(ValueError, match="wait 시간 초과"):
        validate_expression("wait(60_001)")


@pytest.mark.parametrize(
    ("expression", "message"),
    [
        ("().__class__", "허용되지 않은 표현식 요소"),
        ("open('secret.txt')", "허용되지 않은 함수"),
        ("1 + " * 200, "expression 길이 초과"),
    ],
)
def test_expression_sandbox_rejects_escape_and_oversized_inputs(
    expression: str,
    message: str,
) -> None:
    from macroflow.expression_sandbox import validate_expression

    with pytest.raises(ValueError, match=message):
        validate_expression(expression)


@pytest.mark.parametrize("value", [True, -1, float("inf"), float("nan")])
def test_expression_sandbox_rejects_invalid_wait_values(value: object) -> None:
    from macroflow.expression_sandbox import validate_wait_ms

    with pytest.raises(ValueError, match="wait 시간"):
        validate_wait_ms(value, maximum=100)


def test_script_engine_validation_alias_honors_runtime_wait_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import script_engine

    monkeypatch.setattr(script_engine, "_MAX_EXPRESSION_WAIT_MS", 5.0)

    with pytest.raises(ValueError, match="wait 시간 초과"):
        script_engine._validate_expression("wait(6)")
