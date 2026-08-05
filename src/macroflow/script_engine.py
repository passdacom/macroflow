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

import dataclasses
import json
import logging
import math
import os
import random as _random_module
import re
import tempfile
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import macroflow.expression_sandbox as _expression_sandbox
from macroflow.expression_sandbox import (
    MAX_EXPRESSION_WAIT_MS as _DEFAULT_EXPRESSION_WAIT_MS,
)
from macroflow.expression_sandbox import (
    validate_expression as _validate_expression_rules,
)
from macroflow.expression_sandbox import validate_wait_ms as _validated_wait_ms
from macroflow.macro_file import (
    event_from_dict,
    inline_event_block_valid,
    settings_from_dict,
    settings_types_valid,
)
from macroflow.types import (
    AnyEvent,
    ConditionEvent,
    LoopEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
)

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from macroflow.player import PlaybackSession


def _safe_callback(callback: Callable[..., None] | None, *args: object) -> None:
    """Notify UI/host code without letting callback failures corrupt flow state."""
    if callback is None:
        return
    try:
        callback(*args)
    except Exception:
        logger.exception("Flow callback failed: %r", callback)


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
class InlineEventsNode:
    """Execute a node-local block of existing macro events."""

    id: str
    label: str
    events: list[AnyEvent]
    playback_settings: MacroSettings
    next_on_success: str | None = None
    next_on_failure: str | None = None
    position: dict[str, int] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class EndNode:
    """플로우 종료 노드."""

    id: str
    label: str
    status: str = "success"    # "success" | "error"
    position: dict[str, int] = dataclasses.field(default_factory=dict)


AnyFlowNode = (
    MacroNode
    | ColorCheckNode
    | CounterNode
    | WaitFixedNode
    | InlineEventsNode
    | EndNode
)


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
            normalized = raw_path.resolve(strict=False) if raw_path.is_absolute() else (base / raw_path).resolve(strict=False)
            paths.append(normalized)
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

    def __init__(self, message: str, *, node_done_reported: bool = False) -> None:
        super().__init__(message)
        self.node_done_reported = node_done_reported


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
        case "inline_events":
            return InlineEventsNode(
                id=nid,
                label=label,
                events=[event_from_dict(event) for event in d.get("events", [])],
                playback_settings=settings_from_dict(d.get("playback_settings", {})),
                next_on_success=d.get("next_on_success"),
                next_on_failure=d.get("next_on_failure"),
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
    elif isinstance(node, InlineEventsNode):
        d["type"] = "inline_events"
    elif isinstance(node, EndNode):
        d["type"] = "end"
    return d


def _flow_to_dict(flow: MacroFlow) -> dict[str, Any]:
    """MacroFlow를 정규 JSON 문서 구조로 변환한다."""
    return {
        "meta": {
            "version": flow.version,
            "name": flow.name,
            "created_at": flow.created_at,
        },
        "start_node_id": flow.start_node_id,
        "nodes": {nid: _node_to_dict(node) for nid, node in flow.nodes.items()},
    }


def _json_values_equal(left: Any, right: Any) -> bool:
    """JSON 값을 Python의 bool/int 동등성에 기대지 않고 타입까지 비교한다."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _json_values_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _json_values_equal(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return bool(left == right)


def _strict_flow_types_valid(flow: MacroFlow) -> bool:
    """역직렬화가 허용한 bool/int 혼동 등 JSON schema 타입 손실을 차단한다."""
    if any(
        type(value) is not str
        for value in (flow.version, flow.name, flow.created_at, flow.start_node_id)
    ):
        return False

    def nullable_string(value: Any) -> bool:
        return value is None or type(value) is str

    for node_id, node in flow.nodes.items():
        if type(node_id) is not str or type(node.id) is not str or type(node.label) is not str:
            return False
        if type(node.position) is not dict or any(
            type(key) is not str or type(value) is not int
            for key, value in node.position.items()
        ):
            return False
        if isinstance(node, MacroNode):
            if type(node.macro_path) is not str or not all(
                nullable_string(value)
                for value in (node.next_on_success, node.next_on_failure)
            ):
                return False
        elif isinstance(node, ColorCheckNode):
            if (
                type(node.x_ratio) is not float
                or type(node.y_ratio) is not float
                or not math.isfinite(node.x_ratio)
                or not math.isfinite(node.y_ratio)
            ):
                return False
            if any(
                type(value) is not int
                for value in (node.tolerance, node.timeout_ms, node.check_interval_ms)
            ) or not all(nullable_string(value) for value in (node.on_match, node.on_timeout)):
                return False
            if (
                type(node.target_color) is not str
                or re.fullmatch(r"#[0-9A-Fa-f]{6}", node.target_color) is None
                or not 0 <= node.tolerance <= 255
                or node.timeout_ms < 0
                or node.check_interval_ms <= 0
            ):
                return False
        elif isinstance(node, CounterNode):
            if type(node.name) is not str or any(
                type(value) is not int for value in (node.initial, node.increment, node.max)
            ) or not all(
                nullable_string(value) for value in (node.on_continue, node.on_max_reached)
            ):
                return False
        elif isinstance(node, WaitFixedNode):
            if (
                type(node.duration_ms) is not int
                or node.duration_ms < 0
                or not nullable_string(node.next)
            ):
                return False
        elif isinstance(node, InlineEventsNode):
            if (
                type(node.events) is not list
                or not node.events
                or not inline_event_block_valid(node.events)
                or not settings_types_valid(node.playback_settings)
                or not all(
                    nullable_string(value)
                    for value in (node.next_on_success, node.next_on_failure)
                )
            ):
                return False
        elif isinstance(node, EndNode):
            if node.status not in {"success", "error"}:
                return False
    return True


def _strict_flow_graph_valid(flow: MacroFlow) -> bool:
    """Reject dangling and hidden nodes while preserving intentional graph cycles."""
    if flow.start_node_id not in flow.nodes:
        return False

    def outgoing(node: AnyFlowNode) -> tuple[str | None, ...]:
        if isinstance(node, (MacroNode, InlineEventsNode)):
            return (node.next_on_success, node.next_on_failure)
        if isinstance(node, ColorCheckNode):
            return (node.on_match, node.on_timeout)
        if isinstance(node, CounterNode):
            return (node.on_continue, node.on_max_reached)
        if isinstance(node, WaitFixedNode):
            return (node.next,)
        return ()

    visited: set[str] = set()
    pending = [flow.start_node_id]
    while pending:
        node_id = pending.pop()
        if node_id in visited:
            continue
        node = flow.nodes.get(node_id)
        if node is None:
            return False
        visited.add(node_id)
        for target in outgoing(node):
            if target is not None:
                if target not in flow.nodes:
                    return False
                pending.append(target)
    return visited == set(flow.nodes)


def load_flow(path: str, *, strict: bool = False) -> MacroFlow:
    """JSON .macroflow 파일을 MacroFlow로 로드한다.

    Args:
        path: .macroflow 파일 경로.
        strict: 정규 형식으로 다시 저장할 때 손실되는 필드가 있으면 거부한다.

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

    flow = MacroFlow(
        version=meta.get("version", "1.0"),
        name=meta.get("name", "unnamed"),
        created_at=meta.get("created_at", ""),
        start_node_id=raw["start_node_id"],
        nodes=nodes,
    )
    if strict:
        if flow.version not in {"1.0", "1.1"}:
            raise ValueError(
                f"지원하지 않는 플로우 버전: {flow.version!r} (정규 형식 아님)"
            )
        if flow.version == "1.0" and any(
            isinstance(node, InlineEventsNode) for node in flow.nodes.values()
        ):
            raise ValueError("v1.0 정규 플로우에는 inline_events 노드를 사용할 수 없습니다.")
        if (
            not _strict_flow_types_valid(flow)
            or (flow.version == "1.1" and not _strict_flow_graph_valid(flow))
            or not _json_values_equal(raw, _flow_to_dict(flow))
        ):
            raise ValueError(
                "정규 형식이 아닌 필드가 있어 손실 방지를 위해 로드를 거부했습니다."
            )
    return flow


def save_flow(flow: MacroFlow, path: str) -> None:
    """MacroFlow를 JSON .macroflow 파일로 저장한다.

    Args:
        flow: 저장할 MacroFlow.
        path: 저장 경로.
    """
    if (
        flow.version not in {"1.0", "1.1"}
        or not _strict_flow_types_valid(flow)
        or (flow.version == "1.1" and not _strict_flow_graph_valid(flow))
    ):
        raise ValueError(
            "정규 형식이 아닌 필드가 있어 손실 방지를 위해 저장을 거부했습니다."
        )

    data = _flow_to_dict(flow)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f".{p.name}.",
            suffix=".tmp",
            dir=p.parent,
            delete=False,
        ) as temp_file:
            temp_path = Path(temp_file.name)
            json.dump(data, temp_file, ensure_ascii=False, indent=2, allow_nan=False)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        os.replace(temp_path, p)
    except Exception:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)
        raise

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
        self._lifecycle_lock = threading.Lock()
        self._stopping = False
        self._stop_calls_in_progress = 0
        self._player_session: PlaybackSession | None = None
        self._player_session_lock = threading.Lock()

    def start(self, flow: MacroFlow) -> None:
        """플로우를 별도 스레드에서 실행 시작한다."""
        with self._lifecycle_lock:
            worker_alive = self._thread is not None and self._thread.is_alive()
            if self._stopping and not worker_alive and not self._stop_calls_in_progress:
                self._stopping = False
            if self._stop_calls_in_progress or self._stopping or worker_alive:
                raise RuntimeError("FlowEngine is already running")
            self._stop_flag.clear()
            worker = threading.Thread(
                target=self._run, args=(flow,), daemon=True, name="FlowEngine"
            )
            self._thread = worker
            try:
                worker.start()
            except Exception:
                self._thread = None
                raise

    def stop(self) -> None:
        """실행을 중단한다."""
        with self._lifecycle_lock:
            self._stop_flag.set()
            self._stopping = True
            self._stop_calls_in_progress += 1
            worker = self._thread
        try:
            from macroflow import player

            with self._player_session_lock:
                player_session = self._player_session
            if player_session is not None:
                player.stop(player_session)
            if worker is not None:
                worker.join(timeout=5.0)
        finally:
            with self._lifecycle_lock:
                self._stop_calls_in_progress -= 1
                if not self._stop_calls_in_progress and worker is self._thread and (
                    worker is None or not worker.is_alive()
                ):
                    self._stopping = False

    def is_running(self) -> bool:
        with self._lifecycle_lock:
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
                _safe_callback(self._on_error, msg)
                return

            node = flow.nodes[current_id]
            label = getattr(node, "label", current_id)

            _safe_callback(self._on_node_start, current_id, label)

            try:
                current_id = self._execute_node(node)
                if isinstance(node, EndNode) and node.status != "success":
                    _safe_callback(
                        self._on_error,
                        f"플로우가 오류 상태로 종료되었습니다: {node.status}",
                    )
                    return
            except FlowError as e:
                logger.error(f"FlowError: {e}")
                if not e.node_done_reported:
                    _safe_callback(self._on_node_done, current_id or "", False, str(e))
                _safe_callback(self._on_error, str(e))
                return
            except Exception as e:
                logger.exception(f"예상치 못한 오류: {e}")
                _safe_callback(self._on_node_done, current_id, False, str(e))
                _safe_callback(self._on_error, str(e))
                return

        if not self._stop_flag.is_set():
            _safe_callback(self._on_complete, "success")

    def _execute_node(self, node: AnyFlowNode) -> str | None:
        """노드를 실행하고 다음 노드 ID를 반환한다.

        Returns:
            다음 노드 ID. None이면 플로우 종료.
        """
        if isinstance(node, MacroNode):
            return self._run_macro_node(node)

        elif isinstance(node, InlineEventsNode):
            return self._run_inline_events_node(node)

        elif isinstance(node, ColorCheckNode):
            return self._run_color_check_node(node)

        elif isinstance(node, CounterNode):
            return self._run_counter_node(node)

        elif isinstance(node, WaitFixedNode):
            if self._stop_flag.wait(node.duration_ms / 1000.0):
                return None
            _safe_callback(
                self._on_node_done,
                node.id,
                True,
                f"{node.duration_ms}ms 대기 완료",
            )
            return node.next

        elif isinstance(node, EndNode):
            _safe_callback(
                self._on_node_done,
                node.id,
                node.status == "success",
                node.status,
            )
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
                    raise FlowError(msg)
            except ValueError as e:
                msg = f"보안: 경로 검증 실패 ({node.macro_path!r})"
                logger.error(msg)
                raise FlowError(msg) from e

        # 절대·상대 경로 공통: .json 파일만 허용 (실행 파일·스크립트 로드 차단)
        if macro_path.suffix.lower() != ".json":
            msg = f"보안: .json 파일만 허용 ({node.macro_path!r})"
            logger.error(msg)
            raise FlowError(msg)
        if not macro_path.exists():
            msg = f"매크로 파일 없음: {macro_path}"
            raise FlowError(msg)

        from macroflow import macro_file

        try:
            macro = macro_file.load(str(macro_path))
        except Exception as e:
            msg = f"매크로 로드 실패: {e}"
            raise FlowError(msg) from e

        return self._run_macro_data(
            node.id,
            macro,
            next_on_success=node.next_on_success,
            next_on_failure=node.next_on_failure,
        )

    def _run_inline_events_node(self, node: InlineEventsNode) -> str | None:
        """Execute an inline action block through the normal macro player."""
        macro = MacroData(
            meta=MacroMeta(
                version="1.0",
                app_version="",
                created_at="",
                screen_width=0,
                screen_height=0,
                dpi_scale=1.0,
            ),
            settings=node.playback_settings,
            raw_events=list(node.events),
            events=list(node.events),
            is_edited=False,
        )
        return self._run_macro_data(
            node.id,
            macro,
            next_on_success=node.next_on_success,
            next_on_failure=node.next_on_failure,
        )

    def _run_macro_data(
        self,
        node_id: str,
        macro: MacroData,
        *,
        next_on_success: str | None,
        next_on_failure: str | None,
    ) -> str | None:
        """Run MacroData synchronously and map its result to flow edges."""
        from macroflow import player

        done_event = threading.Event()
        callback_lock = threading.Lock()
        callback_state: dict[str, Any] = {
            "accepting": True,
            "ok": True,
            "msg": "",
        }

        def _finish(ok: bool, message: str) -> None:
            with callback_lock:
                if not callback_state["accepting"] or done_event.is_set():
                    return
                callback_state["ok"] = ok
                callback_state["msg"] = message
                done_event.set()

        def _on_complete() -> None:
            _finish(True, "")

        def _on_error(exc: Exception) -> None:
            _finish(False, str(exc))

        try:
            player_session = player.play(
                macro,
                speed=self._speed,
                on_complete=_on_complete,
                on_error=_on_error,
            )
        except Exception as exc:
            message = str(exc)
            _safe_callback(self._on_node_done, node_id, False, message)
            if next_on_failure is None:
                raise FlowError(message, node_done_reported=True) from exc
            return next_on_failure

        with self._player_session_lock:
            self._player_session = player_session

        # 재생 완료 또는 중단 신호까지 대기
        while not done_event.is_set() and not self._stop_flag.is_set():
            self._stop_flag.wait(0.05)

        with callback_lock:
            callback_state["accepting"] = False
        if self._stop_flag.is_set():
            player.stop(player_session)
            with self._player_session_lock:
                if self._player_session == player_session:
                    self._player_session = None
            return None

        with self._player_session_lock:
            if self._player_session == player_session:
                self._player_session = None

        ok = bool(callback_state["ok"])
        message = str(callback_state["msg"])
        _safe_callback(self._on_node_done, node_id, ok, message)

        if not ok and next_on_failure is None:
            raise FlowError(
                message or f"노드 실행 실패: {node_id}",
                node_done_reported=True,
            )

        return next_on_success if ok else next_on_failure

    def _run_color_check_node(self, node: ColorCheckNode) -> str | None:
        """GetPixel 폴링으로 색 감지 대기 후 다음 노드 ID를 반환한다."""
        from macroflow.win32 import get_pixel_color, ratio_to_pixel

        x, y = ratio_to_pixel(node.x_ratio, node.y_ratio)
        target = _hex_to_rgb(node.target_color)
        timeout_ms = max(0, int(node.timeout_ms))
        interval_s = max(1, int(node.check_interval_ms)) / 1000.0
        deadline_ns = (
            None
            if timeout_ms == 0
            else time.perf_counter_ns() + timeout_ms * 1_000_000
        )

        matched = False
        while True:
            if self._stop_flag.is_set():
                return None
            now_ns = time.perf_counter_ns()
            if deadline_ns is not None and now_ns >= deadline_ns:
                break
            actual = get_pixel_color(x, y)
            checked_ns = time.perf_counter_ns()
            if self._stop_flag.is_set():
                return None
            if deadline_ns is not None and checked_ns >= deadline_ns:
                break
            if _color_matches(actual, target, node.tolerance):
                matched = True
                break
            wait_s = interval_s
            if deadline_ns is not None:
                remaining_s = (deadline_ns - checked_ns) / 1_000_000_000
                if remaining_s <= 0:
                    break
                wait_s = min(wait_s, remaining_s)
            if self._stop_flag.wait(wait_s):
                return None

        msg = f"색 감지 {'성공' if matched else '타임아웃'}"
        _safe_callback(self._on_node_done, node.id, matched, msg)

        if not matched and node.on_timeout is None:
            raise FlowError(msg, node_done_reported=True)

        return node.on_match if matched else node.on_timeout

    def _run_counter_node(self, node: CounterNode) -> str | None:
        """카운터를 증가시키고 max 도달 여부에 따라 다음 노드 ID를 반환한다."""
        node._value += node.increment
        reached = node._value >= node.max
        msg = f"카운터 {node.name}: {node._value}/{node.max}"
        logger.debug(msg)
        _safe_callback(self._on_node_done, node.id, True, msg)
        return node.on_max_reached if reached else node.on_continue


# ── expression 안전성 검증 ─────────────────────────────────────────────────────
# 기존 private API는 호출부·회귀 테스트 호환성을 위해 유지한다. 실제 AST
# 정책은 PyQt/실행 엔진 의존성이 없는 expression_sandbox 모듈이 소유한다.
_ALLOWED_EXPR_NODES = _expression_sandbox._ALLOWED_EXPR_NODES
_ALLOWED_FUNC_NAMES = _expression_sandbox._ALLOWED_FUNC_NAMES
_MAX_EXPRESSION_LEN: int = _expression_sandbox.MAX_EXPRESSION_LEN
_MAX_EXPRESSION_WAIT_MS: float = _DEFAULT_EXPRESSION_WAIT_MS
_is_numeric_expression = _expression_sandbox._is_numeric_expression


def _validate_expression(expr: str) -> None:
    """현재 runtime wait 상한으로 expression sandbox 규칙을 검증한다."""
    _validate_expression_rules(
        expr,
        maximum_wait_ms=_MAX_EXPRESSION_WAIT_MS,
    )


# ── 인라인 ConditionEvent / LoopEvent 실행 ────────────────────────────────────

def execute_condition(
    event: ConditionEvent,
    stop_flag: threading.Event,
    execute_fn: Callable[[AnyEvent], None],
    execute_sequence_fn: Callable[[list[AnyEvent]], None] | None = None,
    wait_fn: Callable[[float], bool] | None = None,
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

    remaining_wait_ms = _MAX_EXPRESSION_WAIT_MS

    def _pixel_color(x_ratio: float, y_ratio: float) -> tuple[int, int, int]:
        x, y = ratio_to_pixel(x_ratio, y_ratio)
        return get_pixel_color(x, y)

    def _wait(ms: float) -> None:
        nonlocal remaining_wait_ms
        wait_ms = _validated_wait_ms(ms, maximum=remaining_wait_ms)
        remaining_wait_ms -= wait_ms
        if wait_fn is None:
            stop_flag.wait(wait_ms / 1000.0)
        else:
            wait_fn(wait_ms / 1000.0)

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
    if execute_sequence_fn is not None:
        if not stop_flag.is_set():
            execute_sequence_fn(branch)
        return
    for sub_event in branch:
        if stop_flag.is_set():
            return
        execute_fn(sub_event)


def execute_loop(
    event: LoopEvent,
    stop_flag: threading.Event,
    execute_fn: Callable[[AnyEvent], None],
    execute_sequence_fn: Callable[[list[AnyEvent]], None] | None = None,
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

        if execute_sequence_fn is not None:
            execute_sequence_fn(event.events)
        else:
            for sub_event in event.events:
                if stop_flag.is_set():
                    return
                execute_fn(sub_event)

        iteration += 1

    logger.debug(f"LoopEvent 완료: {iteration}회 반복")
