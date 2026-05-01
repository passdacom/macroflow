"""MacroFlow 스크립팅 실행 엔진.

두 가지 기능을 제공한다:
1. .macroflow 플로우차트 파일 실행 (FlowEngine)
2. 인라인 ConditionEvent / LoopEvent 실행 (execute_condition, execute_loop)

샌드박스 원칙:
- 파일시스템 접근 금지 (매크로 파일 로드만 허용)
- 네트워크 접근 금지
- eval() 사용 시 허용 함수만 바인딩된 제한된 globals 사용
- eval() / exec() 외부 직접 사용 금지

ARCHITECTURE.md: Core Layer — PyQt6 임포트 금지.
"""

from __future__ import annotations

import ast
import dataclasses
import json
import logging
import random as _random_module
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from macroflow.types import AnyEvent, ConditionEvent, LoopEvent

logger = logging.getLogger(__name__)


# ── FlowNode 데이터 타입 ──────────────────────────────────────────────────────

@dataclasses.dataclass
class MacroNode:
    """매크로 JSON 파일 실행 노드."""

    id: str
    label: str
    macro_path: str          # .macroflow 기준 상대 경로
    next_on_success: str | None = None
    next_on_failure: str | None = None
    position: dict[str, int] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class ColorCheckNode:
    """GetPixel 기반 픽셀 색 감지 대기 노드."""

    id: str
    label: str
    x_ratio: float
    y_ratio: float
    target_color: str          # "#RRGGBB"
    tolerance: int = 10
    timeout_ms: int = 10000
    check_interval_ms: int = 50
    on_match: str | None = None
    on_timeout: str | None = None
    position: dict[str, int] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class CounterNode:
    """반복 카운터 노드."""

    id: str
    label: str
    name: str
    initial: int = 0
    increment: int = 1
    max: int = 100
    on_continue: str | None = None
    on_max_reached: str | None = None
    position: dict[str, int] = dataclasses.field(default_factory=dict)

    # 런타임 상태 — 직렬화하지 않음
    _value: int = dataclasses.field(default=0, init=False, repr=False, compare=False)


@dataclasses.dataclass
class WaitFixedNode:
    """고정 대기 노드."""

    id: str
    label: str
    duration_ms: int = 1000
    next: str | None = None
    position: dict[str, int] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class EndNode:
    """플로우 종료 노드."""

    id: str
    label: str
    status: str = "success"    # "success" | "error"
    position: dict[str, int] = dataclasses.field(default_factory=dict)


AnyFlowNode = MacroNode | ColorCheckNode | CounterNode | WaitFixedNode | EndNode


@dataclasses.dataclass
class MacroFlow:
    """플로우차트 전체 데이터."""

    version: str
    name: str
    created_at: str
    start_node_id: str
    nodes: dict[str, AnyFlowNode]


def iter_linear_macro_paths(flow: MacroFlow, flow_path: str | Path) -> list[Path]:
    """선형 MacroFlow에서 매크로 경로를 실행 순서대로 추출한다.

    MacroSequencerWidget이 저장하는 단순 시퀀스는 MacroNode 사이에
    WaitFixedNode가 들어갈 수 있다. 이 함수는 해당 대기 노드를 건너뛰며
    다음 매크로 노드까지 순회한다.
    """
    base = Path(flow_path).parent
    paths: list[Path] = []
    current_id: str | None = flow.start_node_id
    visited: set[str] = set()

    while current_id and current_id in flow.nodes and current_id not in visited:
        visited.add(current_id)
        node = flow.nodes[current_id]

        if isinstance(node, MacroNode):
            raw_path = Path(node.macro_path)
            paths.append(raw_path if raw_path.is_absolute() else base / raw_path)
            current_id = node.next_on_success
        elif isinstance(node, WaitFixedNode):
            current_id = node.next
        elif isinstance(node, EndNode):
            break
        else:
            break

    return paths


# ── FlowEngine 오류 ────────────────────────────────────────────────────────────

class FlowError(Exception):
    """플로우 실행 중 복구 불가 오류."""


# ── 직렬화/역직렬화 ────────────────────────────────────────────────────────────

def _dict_to_node(d: dict[str, Any]) -> AnyFlowNode:
    """딕셔너리를 FlowNode 인스턴스로 변환한다."""
    node_type = d["type"]
    nid = d["id"]
    label = d.get("label", nid)
    pos = d.get("position", {})

    match node_type:
        case "macro":
            return MacroNode(
                id=nid, label=label,
                macro_path=d["macro_path"],
                next_on_success=d.get("next_on_success"),
                next_on_failure=d.get("next_on_failure"),
                position=pos,
            )
        case "color_check":
            return ColorCheckNode(
                id=nid, label=label,
                x_ratio=d["x_ratio"], y_ratio=d["y_ratio"],
                target_color=d["target_color"],
                tolerance=d.get("tolerance", 10),
                timeout_ms=d.get("timeout_ms", 10000),
                check_interval_ms=d.get("check_interval_ms", 50),
                on_match=d.get("on_match"),
                on_timeout=d.get("on_timeout"),
                position=pos,
            )
        case "counter":
            node = CounterNode(
                id=nid, label=label,
                name=d["name"],
                initial=d.get("initial", 0),
                increment=d.get("increment", 1),
                max=d.get("max", 100),
                on_continue=d.get("on_continue"),
                on_max_reached=d.get("on_max_reached"),
                position=pos,
            )
            node._value = node.initial
            return node
        case "wait_fixed":
            return WaitFixedNode(
                id=nid, label=label,
                duration_ms=d.get("duration_ms", 1000),
                next=d.get("next"),
                position=pos,
            )
        case "end":
            return EndNode(
                id=nid, label=label,
                status=d.get("status", "success"),
                position=pos,
            )
        case _:
            raise ValueError(f"알 수 없는 노드 타입: {node_type!r}")


def _node_to_dict(node: AnyFlowNode) -> dict[str, Any]:
    """FlowNode를 JSON 직렬화 가능한 딕셔너리로 변환한다."""
    d = dataclasses.asdict(node)
    # _value(런타임 상태) 제거
    d.pop("_value", None)
    if isinstance(node, MacroNode):
        d["type"] = "macro"
    elif isinstance(node, ColorCheckNode):
        d["type"] = "color_check"
    elif isinstance(node, CounterNode):
        d["type"] = "counter"
    elif isinstance(node, WaitFixedNode):
        d["type"] = "wait_fixed"
    elif isinstance(node, EndNode):
        d["type"] = "end"
    return d


def load_flow(path: str) -> MacroFlow:
    """JSON .macroflow 파일을 MacroFlow로 로드한다.

    Args:
        path: .macroflow 파일 경로.

    Returns:
        로드된 MacroFlow.

    Raises:
        FileNotFoundError: 파일이 없는 경우.
        ValueError: JSON 파싱 오류 또는 필수 필드 누락.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Flow file not found: {path}")

    with p.open(encoding="utf-8") as f:
        raw: dict[str, Any] = json.load(f)

    meta = raw.get("meta", raw)
    nodes: dict[str, AnyFlowNode] = {
        nid: _dict_to_node({**ndata, "id": nid})
        for nid, ndata in raw["nodes"].items()
    }

    return MacroFlow(
        version=meta.get("version", "1.0"),
        name=meta.get("name", "unnamed"),
        created_at=meta.get("created_at", ""),
        start_node_id=raw["start_node_id"],
        nodes=nodes,
    )


def save_flow(flow: MacroFlow, path: str) -> None:
    """MacroFlow를 JSON .macroflow 파일로 저장한다.

    Args:
        flow: 저장할 MacroFlow.
        path: 저장 경로.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    data: dict[str, Any] = {
        "meta": {
            "version": flow.version,
            "name": flow.name,
            "created_at": flow.created_at,
        },
        "start_node_id": flow.start_node_id,
        "nodes": {nid: _node_to_dict(node) for nid, node in flow.nodes.items()},
    }

    with p.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.debug(f"Flow saved to {path}")


# ── 색상 유틸리티 ─────────────────────────────────────────────────────────────

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """#RRGGBB 문자열을 (R, G, B) 튜플로 변환한다."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _color_matches(
    actual: tuple[int, int, int],
    target: tuple[int, int, int],
    tolerance: int,
) -> bool:
    return all(abs(a - t) <= tolerance for a, t in zip(actual, target, strict=False))


# ── FlowEngine ────────────────────────────────────────────────────────────────

class FlowEngine:
    """MacroFlow 플로우차트 실행 엔진.

    .macroflow 파일을 노드 그래프로 순회하며 실행한다.
    각 매크로 노드는 player.play()를 동기적으로 호출한다.

    Args:
        flow_path: .macroflow 파일 경로. MacroNode의 macro_path 해석 기준.
        on_node_start: 노드 실행 시작 시 콜백 (node_id, label).
        on_node_done: 노드 실행 완료 시 콜백 (node_id, success, message).
        on_complete: 플로우 완료 시 콜백 (status).
        on_error: 오류 발생 시 콜백 (message).
    """

    def __init__(
        self,
        flow_path: str,
        on_node_start: Callable[[str, str], None] | None = None,
        on_node_done: Callable[[str, bool, str], None] | None = None,
        on_complete: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        speed: float = 1.0,
    ) -> None:
        self._flow_path = Path(flow_path)
        self._base_dir = self._flow_path.parent
        self._on_node_start = on_node_start
        self._on_node_done = on_node_done
        self._on_complete = on_complete
        self._on_error = on_error
        self._speed = speed
        self._stop_flag = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self, flow: MacroFlow) -> None:
        """플로우를 별도 스레드에서 실행 시작한다."""
        self._stop_flag.clear()
        self._thread = threading.Thread(
            target=self._run, args=(flow,), daemon=True, name="FlowEngine"
        )
        self._thread.start()

    def stop(self) -> None:
        """실행을 중단한다."""
        self._stop_flag.set()
        from macroflow import player
        player.stop()
        if self._thread is not None:
            self._thread.join(timeout=5.0)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def _run(self, flow: MacroFlow) -> None:
        """플로우 실행 메인 루프."""
        # 카운터 초기화
        for node in flow.nodes.values():
            if isinstance(node, CounterNode):
                node._value = node.initial

        current_id: str | None = flow.start_node_id

        while current_id is not None and not self._stop_flag.is_set():
            if current_id not in flow.nodes:
                msg = f"노드 ID를 찾을 수 없습니다: {current_id!r}"
                logger.error(msg)
                if self._on_error:
                    self._on_error(msg)
                return

            node = flow.nodes[current_id]
            label = getattr(node, "label", current_id)

            if self._on_node_start:
                self._on_node_start(current_id, label)

            try:
                current_id = self._execute_node(node)
            except FlowError as e:
                logger.error(f"FlowError: {e}")
                if self._on_node_done:
                    self._on_node_done(current_id or "", False, str(e))
                if self._on_error:
                    self._on_error(str(e))
                return
            except Exception as e:
                logger.exception(f"예상치 못한 오류: {e}")
                if self._on_error:
                    self._on_error(str(e))
                return

        if not self._stop_flag.is_set() and self._on_complete:
            self._on_complete("success")

    def _execute_node(self, node: AnyFlowNode) -> str | None:
        """노드를 실행하고 다음 노드 ID를 반환한다.

        Returns:
            다음 노드 ID. None이면 플로우 종료.
        """
        if isinstance(node, MacroNode):
            return self._run_macro_node(node)

        elif isinstance(node, ColorCheckNode):
            return self._run_color_check_node(node)

        elif isinstance(node, CounterNode):
            return self._run_counter_node(node)

        elif isinstance(node, WaitFixedNode):
            if not self._stop_flag.is_set():
                time.sleep(node.duration_ms / 1000.0)
            if self._on_node_done:
                self._on_node_done(node.id, True, f"{node.duration_ms}ms 대기 완료")
            return node.next

        elif isinstance(node, EndNode):
            if self._on_node_done:
                self._on_node_done(node.id, node.status == "success", node.status)
            return None

        return None

    def _run_macro_node(self, node: MacroNode) -> str | None:
        """매크로 JSON 파일을 동기적으로 재생하고 다음 노드 ID를 반환한다."""
        raw = Path(node.macro_path)
        if raw.is_absolute():
            macro_path = raw.resolve()
        else:
            # 상대 경로: Path Traversal(../) 방지 검사 적용
            macro_path = (self._base_dir / raw).resolve()
            try:
                if not macro_path.is_relative_to(self._base_dir.resolve()):
                    msg = f"보안: 허용되지 않은 경로 접근 차단 ({node.macro_path!r})"
                    logger.error(msg)
                    if self._on_node_done:
                        self._on_node_done(node.id, False, msg)
                    raise FlowError(msg)
            except ValueError as e:
                msg = f"보안: 경로 검증 실패 ({node.macro_path!r})"
                logger.error(msg)
                if self._on_node_done:
                    self._on_node_done(node.id, False, msg)
                raise FlowError(msg) from e

        # 절대·상대 경로 공통: .json 파일만 허용 (실행 파일·스크립트 로드 차단)
        if macro_path.suffix.lower() != ".json":
            msg = f"보안: .json 파일만 허용 ({node.macro_path!r})"
            logger.error(msg)
            if self._on_node_done:
                self._on_node_done(node.id, False, msg)
            raise FlowError(msg)
        if not macro_path.exists():
            msg = f"매크로 파일 없음: {macro_path}"
            if self._on_node_done:
                self._on_node_done(node.id, False, msg)
            raise FlowError(msg)

        from macroflow import macro_file, player

        try:
            macro = macro_file.load(str(macro_path))
        except Exception as e:
            msg = f"매크로 로드 실패: {e}"
            if self._on_node_done:
                self._on_node_done(node.id, False, msg)
            raise FlowError(msg) from e

        done_event = threading.Event()
        result: dict[str, Any] = {"ok": True, "msg": ""}

        def _on_complete() -> None:
            result["ok"] = True
            done_event.set()

        def _on_error(exc: Exception) -> None:
            result["ok"] = False
            result["msg"] = str(exc)
            done_event.set()

        player.play(macro, speed=self._speed, on_complete=_on_complete, on_error=_on_error)

        # 재생 완료 또는 중단 신호까지 대기
        while not done_event.is_set() and not self._stop_flag.is_set():
            time.sleep(0.05)

        if self._stop_flag.is_set():
            player.stop()
            return None

        if self._on_node_done:
            self._on_node_done(node.id, result["ok"], result["msg"])

        return node.next_on_success if result["ok"] else node.next_on_failure

    def _run_color_check_node(self, node: ColorCheckNode) -> str | None:
        """GetPixel 폴링으로 색 감지 대기 후 다음 노드 ID를 반환한다."""
        from macroflow.win32 import get_pixel_color, ratio_to_pixel

        x, y = ratio_to_pixel(node.x_ratio, node.y_ratio)
        target = _hex_to_rgb(node.target_color)
        deadline_ns = time.perf_counter_ns() + node.timeout_ms * 1_000_000
        interval_s = node.check_interval_ms / 1000.0

        matched = False
        while time.perf_counter_ns() < deadline_ns:
            if self._stop_flag.is_set():
                return None
            actual = get_pixel_color(x, y)
            if _color_matches(actual, target, node.tolerance):
                matched = True
                break
            time.sleep(interval_s)

        msg = f"색 감지 {'성공' if matched else '타임아웃'}"
        if self._on_node_done:
            self._on_node_done(node.id, matched, msg)

        return node.on_match if matched else node.on_timeout

    def _run_counter_node(self, node: CounterNode) -> str | None:
        """카운터를 증가시키고 max 도달 여부에 따라 다음 노드 ID를 반환한다."""
        node._value += node.increment
        reached = node._value >= node.max
        msg = f"카운터 {node.name}: {node._value}/{node.max}"
        logger.debug(msg)
        if self._on_node_done:
            self._on_node_done(node.id, True, msg)
        return node.on_max_reached if reached else node.on_continue


# ── expression 안전성 검증 ─────────────────────────────────────────────────────
# 객체 그래프 순회(`__class__.__mro__[-1].__subclasses__()` 등)를 통한
# 샌드박스 탈출을 AST 화이트리스트로 차단한다.
# ast.Attribute 미포함 → `.` 속성 접근 전면 차단.

_ALLOWED_EXPR_NODES: frozenset[type[ast.AST]] = frozenset({
    ast.Expression,
    ast.BoolOp, ast.And, ast.Or,
    ast.BinOp, ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.FloorDiv,
    ast.UnaryOp, ast.Not, ast.USub, ast.UAdd,
    ast.Compare,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Call,
    ast.Constant,
    ast.Name,
    ast.Tuple, ast.List,
    ast.Load,
    ast.Subscript,
    ast.Slice,
    ast.IfExp,
})
_ALLOWED_FUNC_NAMES: frozenset[str] = frozenset({"pixel_color", "wait", "random"})
_MAX_EXPRESSION_LEN: int = 512


def _validate_expression(expr: str) -> None:
    """표현식이 허용된 AST 노드만 포함하는지 검증한다.

    Args:
        expr: 검증할 표현식 문자열.

    Raises:
        ValueError: 허용되지 않은 노드(속성 접근 등) 또는 길이 초과 시.
    """
    if len(expr) > _MAX_EXPRESSION_LEN:
        raise ValueError(
            f"expression 길이 초과 ({len(expr)} > {_MAX_EXPRESSION_LEN})"
        )
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"표현식 구문 오류: {e}") from e
    for node in ast.walk(tree):
        if type(node) not in _ALLOWED_EXPR_NODES:
            raise ValueError(
                f"허용되지 않은 표현식 요소: {type(node).__name__!r}"
            )
        if isinstance(node, ast.Call):
            if (
                not isinstance(node.func, ast.Name)
                or node.func.id not in _ALLOWED_FUNC_NAMES
            ):
                raise ValueError(
                    f"허용되지 않은 함수: {ast.unparse(node.func)!r}"
                )


# ── 인라인 ConditionEvent / LoopEvent 실행 ────────────────────────────────────

def execute_condition(
    event: ConditionEvent,
    stop_flag: threading.Event,
    execute_fn: Callable[[AnyEvent], None],
) -> None:
    """ConditionEvent를 샌드박스 내에서 평가하고 분기를 실행한다.

    DSL 표현식에서 허용하는 함수:
        pixel_color(x_ratio, y_ratio) → tuple[int, int, int]
        wait(ms) → None
        random() → float  (0.0~1.0)

    Args:
        event: 실행할 ConditionEvent.
        stop_flag: 중단 신호 Event.
        execute_fn: 단일 AnyEvent를 실행하는 콜백.
    """
    from macroflow.win32 import get_pixel_color, ratio_to_pixel

    def _pixel_color(x_ratio: float, y_ratio: float) -> tuple[int, int, int]:
        x, y = ratio_to_pixel(x_ratio, y_ratio)
        return get_pixel_color(x, y)

    def _wait(ms: float) -> None:
        time.sleep(ms / 1000.0)

    def _random() -> float:
        return _random_module.random()

    # 제한된 샌드박스: __builtins__ 완전 차단, 허용 함수만 노출
    # random은 모듈 전체가 아닌 random() 함수 하나만 노출 (모듈 속성 접근 차단)
    sandbox_globals: dict[str, Any] = {
        "__builtins__": {},
        "pixel_color": _pixel_color,
        "wait": _wait,
        "random": _random,
        "True": True,
        "False": False,
    }

    try:
        _validate_expression(event.expression)
        result = bool(eval(event.expression, sandbox_globals))  # noqa: S307
    except Exception as e:
        logger.error(f"ConditionEvent 표현식 오류 ({event.expression!r}): {e}")
        result = False

    branch = event.if_true if result else event.if_false
    for sub_event in branch:
        if stop_flag.is_set():
            return
        execute_fn(sub_event)


def execute_loop(
    event: LoopEvent,
    stop_flag: threading.Event,
    execute_fn: Callable[[AnyEvent], None],
) -> None:
    """LoopEvent의 events 배열을 지정 횟수만큼 반복 실행한다.

    Args:
        event: 실행할 LoopEvent. count == -1이면 stop_flag까지 무한 반복.
        stop_flag: 중단 신호 Event.
        execute_fn: 단일 AnyEvent를 실행하는 콜백.
    """
    iteration = 0
    infinite = event.count == -1

    while not stop_flag.is_set():
        if not infinite and iteration >= event.count:
            break

        for sub_event in event.events:
            if stop_flag.is_set():
                return
            execute_fn(sub_event)

        iteration += 1

    logger.debug(f"LoopEvent 완료: {iteration}회 반복")
