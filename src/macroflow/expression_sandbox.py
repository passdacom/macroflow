"""Pure validation rules for MacroFlow condition expressions.

This module owns the AST allowlist and wait-budget validation. It intentionally
has no dependencies on the execution engine, Windows APIs, or PyQt.
"""

from __future__ import annotations

import ast
import math

_ALLOWED_EXPR_NODES: frozenset[type[ast.AST]] = frozenset(
    {
        ast.Expression,
        ast.BoolOp,
        ast.And,
        ast.Or,
        ast.BinOp,
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Mod,
        ast.FloorDiv,
        ast.UnaryOp,
        ast.Not,
        ast.USub,
        ast.UAdd,
        ast.Compare,
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        ast.Call,
        ast.Constant,
        ast.Name,
        ast.Tuple,
        ast.List,
        ast.Load,
        ast.Subscript,
        ast.Slice,
        ast.IfExp,
    }
)
_ALLOWED_FUNC_NAMES: frozenset[str] = frozenset({"pixel_color", "wait", "random"})
MAX_EXPRESSION_LEN: int = 512
MAX_EXPRESSION_WAIT_MS: float = 60_000.0


def _is_numeric_expression(node: ast.AST) -> bool:
    """Return whether an AST node is statically a numeric expression."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (int, float))
    if isinstance(node, ast.UnaryOp):
        return _is_numeric_expression(node.operand)
    if isinstance(node, ast.BinOp):
        return _is_numeric_expression(node.left) and _is_numeric_expression(node.right)
    if isinstance(node, ast.IfExp):
        return _is_numeric_expression(node.body) and _is_numeric_expression(node.orelse)
    if isinstance(node, ast.Call):
        return isinstance(node.func, ast.Name) and node.func.id == "random"
    if isinstance(node, ast.Subscript):
        return (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "pixel_color"
            and not isinstance(node.slice, ast.Slice)
        )
    return False


def validate_wait_ms(value: object, *, maximum: float) -> float:
    """Validate a sandbox wait value and return milliseconds as a float."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("wait 시간은 유한한 숫자여야 합니다")
    wait_ms = float(value)
    if not math.isfinite(wait_ms) or wait_ms < 0 or wait_ms > maximum:
        raise ValueError(f"wait 시간 초과 또는 잘못된 값 ({wait_ms}ms, 최대 {maximum}ms)")
    return wait_ms


def validate_expression(
    expr: str,
    *,
    maximum_wait_ms: float = MAX_EXPRESSION_WAIT_MS,
) -> None:
    """Validate that an expression contains only the permitted AST surface."""
    if len(expr) > MAX_EXPRESSION_LEN:
        raise ValueError(f"expression 길이 초과 ({len(expr)} > {MAX_EXPRESSION_LEN})")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"표현식 구문 오류: {exc}") from exc

    for node in ast.walk(tree):
        if type(node) not in _ALLOWED_EXPR_NODES:
            raise ValueError(f"허용되지 않은 표현식 요소: {type(node).__name__!r}")
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in _ALLOWED_FUNC_NAMES:
                raise ValueError(f"허용되지 않은 함수: {ast.unparse(node.func)!r}")
            if node.func.id == "wait":
                if len(node.args) != 1 or node.keywords:
                    raise ValueError("wait()는 위치 인자 1개만 허용합니다")
                if isinstance(node.args[0], ast.Constant):
                    validate_wait_ms(
                        node.args[0].value,
                        maximum=maximum_wait_ms,
                    )
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mult):
            if not (_is_numeric_expression(node.left) and _is_numeric_expression(node.right)):
                raise ValueError("sequence 반복을 유발하는 곱셈은 허용되지 않습니다")
