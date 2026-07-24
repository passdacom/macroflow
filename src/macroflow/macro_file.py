"""MacroFlow JSON 직렬화·역직렬화 및 편집 유틸리티.

저장 시 .bak 파일 자동 생성.
로드 시 스키마 버전 마이그레이션 수행.
raw_events는 항상 불변으로 보존된다.

json-format-spec.md 기반.
"""

from __future__ import annotations

import copy
import dataclasses
import json
import logging
import math
import re
import shutil
from itertools import pairwise
from pathlib import Path
from typing import Any, Literal

from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    ConditionEvent,
    KeyEvent,
    LoopEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    TextInputEvent,
    WaitEvent,
    WindowTriggerEvent,
)

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = "1.0"


# ── 마이그레이션 ──────────────────────────────────────────────────────────────
# 버전별 마이그레이션 함수. key = "이전버전→현재버전"
_MIGRATIONS: dict[str, Any] = {
    # 예: "0.9→1.0": lambda d: d  (현재는 없음)
}


def _migrate(data: dict[str, Any]) -> dict[str, Any]:
    """필요 시 스키마 버전을 현재 버전으로 마이그레이션한다."""
    version = data.get("meta", {}).get("version", CURRENT_SCHEMA_VERSION)
    if version == CURRENT_SCHEMA_VERSION:
        return data
    key = f"{version}→{CURRENT_SCHEMA_VERSION}"
    if key in _MIGRATIONS:
        logger.info(f"Migrating macro schema: {key}")
        return _MIGRATIONS[key](data)  # type: ignore[no-any-return]
    logger.warning(f"No migration path for schema {version}; loading as-is")
    return data


# ── 역직렬화 ──────────────────────────────────────────────────────────────────


def _bounded_int(value: Any, *, minimum: int, maximum: int, default: int) -> int:
    """외부 JSON 숫자를 안전한 runtime 범위로 정규화한다."""
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return min(maximum, max(minimum, parsed))


def _dict_to_settings(d: dict[str, Any]) -> MacroSettings:
    """저장된 settings 딕셔너리를 MacroSettings로 변환한다.

    기존 파일에는 클릭 색 체크 timeout이 `color_check_click_timeout_ms` 하나뿐이었다.
    새 action별 timeout 필드가 누락된 경우 legacy 값을 세 필드에 복사해 사용자가
    저장해 둔 단일 timeout 의미를 보존한다.
    """
    data = dict(d)
    legacy_timeout = data.get("color_check_click_timeout_ms", 10000)
    data.setdefault("color_check_click_wait_timeout_ms", legacy_timeout)
    data.setdefault("color_check_click_skip_timeout_ms", legacy_timeout)
    data.setdefault("color_check_click_stop_timeout_ms", legacy_timeout)
    timeout_defaults = {
        "color_check_click_timeout_ms": 10000,
        "color_check_click_wait_timeout_ms": 10000,
        "color_check_click_skip_timeout_ms": 10000,
        "color_check_click_stop_timeout_ms": 10000,
        "color_trigger_default_timeout_ms": 0,
    }
    interval_defaults = {
        "color_check_click_interval_ms": 50,
        "color_trigger_check_interval_ms": 50,
    }
    for key, default in timeout_defaults.items():
        if key in data:
            data[key] = _bounded_int(
                data[key], minimum=0, maximum=600000, default=default
            )
    for key, default in interval_defaults.items():
        if key in data:
            data[key] = _bounded_int(
                data[key], minimum=1, maximum=10000, default=default
            )
    return MacroSettings(**data)


def _dict_to_event(d: dict[str, Any]) -> AnyEvent:
    """딕셔너리를 AnyEvent 서브클래스 인스턴스로 변환한다.

    Args:
        d: JSON에서 파싱된 이벤트 딕셔너리.

    Returns:
        적절한 MacroEvent 서브클래스 인스턴스.

    Raises:
        ValueError: 알 수 없는 type 필드.
    """
    common: dict[str, Any] = {
        "id":               d["id"],
        "type":             d["type"],
        "timestamp_ns":     d["timestamp_ns"],
        "delay_override_ms": d.get("delay_override_ms"),
        "source_file":      d.get("source_file", ""),
        "remark":           d.get("remark", ""),
    }

    match d["type"]:
        case "mouse_down" | "mouse_up":
            raw_action = d.get("color_check_on_mismatch", "skip")
            on_mismatch: Literal["skip", "stop", "wait"] = (
                "stop" if raw_action == "stop"
                else "wait" if raw_action == "wait"
                else "skip"
            )
            return MouseButtonEvent(
                **common,
                x_ratio=d["x_ratio"],
                y_ratio=d["y_ratio"],
                button=d.get("button", "left"),
                recorded_color=d.get("recorded_color"),
                color_check_enabled=d.get("color_check_enabled", False),
                color_check_on_mismatch=on_mismatch,
            )
        case "mouse_move":
            return MouseMoveEvent(
                **common,
                x_ratio=d["x_ratio"],
                y_ratio=d["y_ratio"],
            )
        case "mouse_wheel":
            return MouseWheelEvent(
                **common,
                delta=d["delta"],
                axis=d.get("axis", "vertical"),
                x_ratio=d["x_ratio"],
                y_ratio=d["y_ratio"],
            )
        case "key_down" | "key_up":
            return KeyEvent(
                **common,
                key=d["key"],
                vk_code=d["vk_code"],
            )
        case "wait":
            return WaitEvent(**common, duration_ms=d["duration_ms"])
        case "color_trigger":
            return ColorTriggerEvent(
                **common,
                x_ratio=d["x_ratio"],
                y_ratio=d["y_ratio"],
                target_color=d["target_color"],
                tolerance=d.get("tolerance", 10),
                timeout_ms=_bounded_int(
                    d.get("timeout_ms", 0),
                    minimum=0,
                    maximum=600000,
                    default=0,
                ),
                check_interval_ms=_bounded_int(
                    d.get("check_interval_ms", 50),
                    minimum=1,
                    maximum=10000,
                    default=50,
                ),
                on_timeout=d.get("on_timeout", "error"),
            )
        case "window_trigger":
            return WindowTriggerEvent(
                **common,
                window_title_contains=d["window_title_contains"],
                timeout_ms=d.get("timeout_ms", 10000),
                on_timeout=d.get("on_timeout", "error"),
            )
        case "text_input":
            return TextInputEvent(
                **common,
                text=d.get("text", ""),
            )
        case "condition":
            return ConditionEvent(
                **common,
                expression=d["expression"],
                if_true=[_dict_to_event(e) for e in d.get("if_true", [])],
                if_false=[_dict_to_event(e) for e in d.get("if_false", [])],
            )
        case "loop":
            return LoopEvent(
                **common,
                count=d["count"],
                events=[_dict_to_event(e) for e in d.get("events", [])],
            )
        case _:
            raise ValueError(f"Unknown event type: {d['type']!r}")


def _event_to_dict(event: AnyEvent) -> dict[str, Any]:
    """MacroEvent 인스턴스를 JSON 직렬화 가능한 딕셔너리로 변환한다."""
    return dataclasses.asdict(event)


def event_from_dict(data: dict[str, Any]) -> AnyEvent:
    """Public canonical decoder shared by macro JSON and flow documents."""
    return _dict_to_event(data)


def event_to_dict(event: AnyEvent) -> dict[str, Any]:
    """Public canonical encoder shared by macro JSON and flow documents."""
    return _event_to_dict(event)


def settings_from_dict(data: dict[str, Any]) -> MacroSettings:
    """Decode a settings snapshot with the same legacy defaults as macro files."""
    return _dict_to_settings(data)


def settings_to_dict(settings: MacroSettings) -> dict[str, Any]:
    """Encode a complete playback-settings snapshot."""
    return dataclasses.asdict(settings)


def _valid_color(value: object) -> bool:
    return value is None or (
        type(value) is str and re.fullmatch(r"#[0-9A-Fa-f]{6}", value) is not None
    )


def _valid_required_color(value: object) -> bool:
    return type(value) is str and re.fullmatch(r"#[0-9A-Fa-f]{6}", value) is not None


def event_types_valid(event: AnyEvent, *, _depth: int = 0) -> bool:
    """Return whether an event has strict JSON-safe runtime field types."""
    if _depth > 16 or (
        type(event.id) is not str
        or type(event.type) is not str
        or type(event.timestamp_ns) is not int
        or not (event.delay_override_ms is None or type(event.delay_override_ms) is int)
        or type(event.source_file) is not str
        or type(event.remark) is not str
    ):
        return False

    def finite_ratio(value: object) -> bool:
        return type(value) is float and math.isfinite(value)

    if isinstance(event, MouseButtonEvent):
        return (
            finite_ratio(event.x_ratio)
            and finite_ratio(event.y_ratio)
            and event.button in {"left", "right", "middle"}
            and _valid_color(event.recorded_color)
            and type(event.color_check_enabled) is bool
            and event.color_check_on_mismatch in {"skip", "stop", "wait"}
        )
    if isinstance(event, MouseMoveEvent):
        return finite_ratio(event.x_ratio) and finite_ratio(event.y_ratio)
    if isinstance(event, MouseWheelEvent):
        return (
            type(event.delta) is int
            and event.axis in {"vertical", "horizontal"}
            and finite_ratio(event.x_ratio)
            and finite_ratio(event.y_ratio)
        )
    if isinstance(event, KeyEvent):
        return type(event.key) is str and type(event.vk_code) is int
    if isinstance(event, WaitEvent):
        return type(event.duration_ms) is int
    if isinstance(event, ColorTriggerEvent):
        return (
            finite_ratio(event.x_ratio)
            and finite_ratio(event.y_ratio)
            and _valid_color(event.target_color)
            and type(event.tolerance) is int
            and type(event.timeout_ms) is int
            and type(event.check_interval_ms) is int
            and event.on_timeout in {"error", "skip", "retry"}
        )
    if isinstance(event, WindowTriggerEvent):
        return (
            type(event.window_title_contains) is str
            and type(event.timeout_ms) is int
            and event.on_timeout in {"error", "skip", "retry"}
        )
    if isinstance(event, TextInputEvent):
        return type(event.text) is str
    if isinstance(event, ConditionEvent):
        return (
            type(event.expression) is str
            and type(event.if_true) is list
            and type(event.if_false) is list
            and all(event_types_valid(item, _depth=_depth + 1) for item in event.if_true)
            and all(event_types_valid(item, _depth=_depth + 1) for item in event.if_false)
        )
    if isinstance(event, LoopEvent):
        return (
            type(event.count) is int
            and type(event.events) is list
            and all(event_types_valid(item, _depth=_depth + 1) for item in event.events)
        )
    return False


def settings_types_valid(settings: MacroSettings) -> bool:
    """Return whether a settings snapshot preserves exact numeric JSON types."""
    for field in dataclasses.fields(settings):
        value = getattr(settings, field.name)
        if field.name == "default_playback_speed":
            if type(value) is not float or not math.isfinite(value):
                return False
        elif type(value) is not int:
            return False
    return True


def inline_event_block_valid(events: list[AnyEvent]) -> bool:
    """Validate one semantic sequencer action without widening macro-file behavior."""
    if not events or not all(event_types_valid(event) for event in events):
        return False
    if len(events) == 1:
        event = events[0]
        if event.timestamp_ns != 0:
            return False
        return (
            isinstance(event, TextInputEvent)
            and bool(event.text)
        ) or (
            isinstance(event, ColorTriggerEvent)
            and _valid_required_color(event.target_color)
            and event.tolerance >= 0
            and event.timeout_ms >= 0
            and event.check_interval_ms > 0
            and event.on_timeout == "error"
        )
    if len(events) not in {2, 4} or not all(
        isinstance(event, MouseButtonEvent) for event in events
    ):
        return False
    click_events = [event for event in events if isinstance(event, MouseButtonEvent)]
    expected_types = (
        ["mouse_down", "mouse_up"]
        if len(click_events) == 2
        else ["mouse_down", "mouse_up", "mouse_down", "mouse_up"]
    )
    first = click_events[0]
    return (
        [event.type for event in click_events] == expected_types
        and first.timestamp_ns == 0
        and all(
            event.button == first.button
            and event.x_ratio == first.x_ratio
            and event.y_ratio == first.y_ratio
            for event in click_events
        )
        and all(
            previous.timestamp_ns < current.timestamp_ns
            for previous, current in pairwise(click_events)
        )
    )


# ── 공개 I/O ─────────────────────────────────────────────────────────────────

def load(path: str) -> MacroData:
    """JSON 파일에서 MacroData를 로드한다.

    마이그레이션이 필요한 경우 자동으로 수행한다.

    Args:
        path: .json 파일 경로.

    Returns:
        로드된 MacroData.

    Raises:
        FileNotFoundError: 파일이 없는 경우.
        ValueError: JSON 파싱 오류 또는 필수 필드 누락.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Macro file not found: {path}")

    try:
        with p.open(encoding="utf-8") as f:
            raw: dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파싱 오류 ({path}): {e}") from e
    except OSError as e:
        raise ValueError(f"파일 읽기 오류 ({path}): {e}") from e

    try:
        raw = _migrate(raw)
        meta = MacroMeta(**raw["meta"])
        settings = _dict_to_settings(raw.get("settings", {}))
        raw_events: list[AnyEvent] = [_dict_to_event(e) for e in raw["raw_events"]]
        events: list[AnyEvent] = [_dict_to_event(e) for e in raw["events"]]
        is_edited: bool = raw.get("is_edited", False)
    except (KeyError, TypeError) as e:
        raise ValueError(f"매크로 파일 구조 오류 ({path}): {e}") from e

    return MacroData(
        meta=meta,
        settings=settings,
        raw_events=raw_events,
        events=events,
        is_edited=is_edited,
    )


def save(macro: MacroData, path: str) -> None:
    """MacroData를 JSON 파일로 저장한다.

    기존 파일이 있으면 .bak으로 백업 후 덮어쓴다.

    Args:
        macro: 저장할 MacroData.
        path: 저장 경로.
    """
    p = Path(path)

    try:
        # 기존 파일 백업
        if p.exists():
            shutil.copy2(p, p.with_suffix(".bak"))
            logger.debug(f"Backed up: {p.with_suffix('.bak')}")

        p.parent.mkdir(parents=True, exist_ok=True)

        data: dict[str, Any] = {
            "meta":       dataclasses.asdict(macro.meta),
            "settings":   dataclasses.asdict(macro.settings),
            "raw_events": [_event_to_dict(e) for e in macro.raw_events],
            "events":     [_event_to_dict(e) for e in macro.events],
            "is_edited":  macro.is_edited,
        }

        with p.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        raise OSError(f"매크로 저장 실패 ({path}): {e}") from e

    logger.debug(f"Saved macro to {path}")


# ── 편집 유틸리티 ─────────────────────────────────────────────────────────────

def delete_mouse_moves(macro: MacroData) -> MacroData:
    """events에서 mouse_move 이벤트를 모두 제거한다. raw_events는 유지.

    Args:
        macro: 원본 MacroData.

    Returns:
        mouse_move가 제거된 새 MacroData (is_edited=True).
    """
    filtered = [e for e in macro.events if e.type != "mouse_move"]
    return MacroData(
        meta=macro.meta,
        settings=macro.settings,
        raw_events=macro.raw_events,
        events=filtered,
        is_edited=True,
    )


def set_delay_all(
    macro: MacroData,
    delay_ms: int | None,
    *,
    event_ids: set[str] | None = None,
) -> MacroData:
    """대상 events의 재생 대기를 동일 값 또는 녹화 타이밍(None)으로 설정한다.

    Args:
        macro: 원본 MacroData.
        delay_ms: 실행 전 대기(ms). None이면 녹화 타이밍을 사용한다.
        event_ids: 설정할 이벤트 ID 집합. None이면 모든 events에 적용한다.

    Returns:
        재생 대기가 일괄 설정된 새 MacroData (is_edited=True).
    """
    updated = copy.deepcopy(macro.events)
    for event in updated:
        if event_ids is None or event.id in event_ids:
            event.delay_override_ms = delay_ms
    return MacroData(
        meta=macro.meta,
        settings=macro.settings,
        raw_events=macro.raw_events,
        events=updated,
        is_edited=True,
    )


def set_delay_single(macro: MacroData, event_id: str, delay_ms: int | None) -> MacroData:
    """events에서 특정 id의 delay_override_ms만 수정한다.

    Args:
        macro: 원본 MacroData.
        event_id: 수정할 이벤트 id (8자리 hex).
        delay_ms: 설정할 딜레이. None이면 원래 타이밍 복원.

    Returns:
        해당 이벤트의 딜레이가 수정된 새 MacroData (is_edited=True).

    Raises:
        KeyError: 해당 id를 가진 이벤트가 없는 경우.
    """
    updated = copy.deepcopy(macro.events)
    for event in updated:
        if event.id == event_id:
            event.delay_override_ms = delay_ms
            return MacroData(
                meta=macro.meta,
                settings=macro.settings,
                raw_events=macro.raw_events,
                events=updated,
                is_edited=True,
            )
    raise KeyError(f"Event id not found: {event_id!r}")


def reset_to_raw(macro: MacroData) -> MacroData:
    """events를 raw_events 전체 복사본으로 되돌린다 (is_edited=False).

    Args:
        macro: 원본 MacroData.

    Returns:
        원본으로 되돌린 새 MacroData.
    """
    return MacroData(
        meta=macro.meta,
        settings=macro.settings,
        raw_events=macro.raw_events,
        events=copy.deepcopy(macro.raw_events),
        is_edited=False,
    )


def edit_key_value(
    macro: MacroData, event_id: str, new_key: str, new_vk_code: int
) -> MacroData:
    """events에서 특정 id의 KeyEvent key·vk_code를 수정한다.

    Args:
        macro: 원본 MacroData.
        event_id: 수정할 이벤트 id (8자리 hex).
        new_key: 새 키 이름 문자열 (예: "a", "enter").
        new_vk_code: 새 Windows Virtual Key Code.

    Returns:
        해당 이벤트가 수정된 새 MacroData (is_edited=True).

    Raises:
        KeyError: 해당 id를 가진 이벤트가 없는 경우.
        TypeError: 해당 이벤트가 KeyEvent가 아닌 경우.
    """
    updated = copy.deepcopy(macro.events)
    for event in updated:
        if event.id == event_id:
            if not isinstance(event, KeyEvent):
                raise TypeError(f"Event {event_id!r} is not a KeyEvent")
            event.key = new_key
            event.vk_code = new_vk_code
            return MacroData(
                meta=macro.meta,
                settings=macro.settings,
                raw_events=macro.raw_events,
                events=updated,
                is_edited=True,
            )
    raise KeyError(f"Event id not found: {event_id!r}")


def edit_wheel_delta(
    macro: MacroData, event_id: str, new_delta: int
) -> MacroData:
    """events에서 특정 id의 MouseWheelEvent delta를 수정한다.

    Args:
        macro: 원본 MacroData.
        event_id: 수정할 이벤트 id (8자리 hex).
        new_delta: 새 스크롤 양 (양수=위/우, 음수=아래/좌).

    Returns:
        해당 이벤트가 수정된 새 MacroData (is_edited=True).

    Raises:
        KeyError: 해당 id를 가진 이벤트가 없는 경우.
        TypeError: 해당 이벤트가 MouseWheelEvent가 아닌 경우.
    """
    updated = copy.deepcopy(macro.events)
    for event in updated:
        if event.id == event_id:
            if not isinstance(event, MouseWheelEvent):
                raise TypeError(f"Event {event_id!r} is not a MouseWheelEvent")
            event.delta = new_delta
            return MacroData(
                meta=macro.meta,
                settings=macro.settings,
                raw_events=macro.raw_events,
                events=updated,
                is_edited=True,
            )
    raise KeyError(f"Event id not found: {event_id!r}")


def merge_macros(macros: list[tuple[MacroData, str]], gap_ms: int = 500) -> MacroData:
    """여러 MacroData를 타임스탬프 오프셋을 적용하여 하나로 병합한다.

    각 매크로 사이에 gap_ms 간격을 두고, source_file 필드에 원본 파일명을
    기록하여 에디터의 '출처' 열에 표시할 수 있게 한다.

    Args:
        macros: (MacroData, 파일명) 튜플 목록. 순서대로 연결된다.
        gap_ms: 매크로 사이 삽입 간격 (밀리초). 기본값 500ms.

    Returns:
        병합된 새 MacroData (is_edited=True).

    Raises:
        ValueError: macros 목록이 비어 있는 경우.
    """
    if not macros:
        raise ValueError("병합할 매크로가 없습니다")

    _GAP_NS = max(0, gap_ms) * 1_000_000  # 매크로 간 간격

    merged_events: list[AnyEvent] = []
    previous_end_ns: int | None = None

    for macro_data, fname in macros:
        evs = copy.deepcopy(macro_data.events)
        if not evs:
            continue

        if previous_end_ns is None:
            offset_ns = 0
        else:
            offset_ns = previous_end_ns + _GAP_NS - evs[0].timestamp_ns

        for ev in evs:
            ev.timestamp_ns += offset_ns
            ev.source_file = fname
        merged_events.extend(evs)
        previous_end_ns = max(ev.timestamp_ns for ev in evs)

    # 첫 번째 매크로의 메타·설정을 기반으로 생성
    base_meta = macros[0][0].meta
    base_settings = macros[0][0].settings

    return MacroData(
        meta=base_meta,
        settings=base_settings,
        raw_events=copy.deepcopy(merged_events),
        events=merged_events,
        is_edited=True,
    )


def edit_position(
    macro: MacroData, event_id: str, new_x_ratio: float, new_y_ratio: float
) -> MacroData:
    """events에서 특정 id의 마우스 이벤트 좌표를 수정한다.

    Args:
        macro: 원본 MacroData.
        event_id: 수정할 이벤트 id (8자리 hex).
        new_x_ratio: 새 X 좌표 비율 (0.0~1.0).
        new_y_ratio: 새 Y 좌표 비율 (0.0~1.0).

    Returns:
        해당 이벤트가 수정된 새 MacroData (is_edited=True).

    Raises:
        KeyError: 해당 id를 가진 이벤트가 없는 경우.
        TypeError: 해당 이벤트가 마우스 이벤트가 아닌 경우.
    """
    updated = copy.deepcopy(macro.events)
    for event in updated:
        if event.id == event_id:
            if not isinstance(event, (MouseButtonEvent, MouseMoveEvent)):
                raise TypeError(f"Event {event_id!r} is not a mouse event")
            event.x_ratio = new_x_ratio
            event.y_ratio = new_y_ratio
            return MacroData(
                meta=macro.meta,
                settings=macro.settings,
                raw_events=macro.raw_events,
                events=updated,
                is_edited=True,
            )
    raise KeyError(f"Event id not found: {event_id!r}")


def toggle_color_check(macro: MacroData, event_id: str) -> MacroData:
    """events에서 특정 id의 mouse_down 이벤트의 color_check_enabled를 토글한다.

    Args:
        macro: 원본 MacroData.
        event_id: 수정할 mouse_down 이벤트 id (8자리 hex).

    Returns:
        color_check_enabled가 반전된 새 MacroData (is_edited=True).

    Raises:
        KeyError: 해당 id를 가진 이벤트가 없는 경우.
        TypeError: 해당 이벤트가 MouseButtonEvent가 아닌 경우.
    """
    updated = copy.deepcopy(macro.events)
    for event in updated:
        if event.id == event_id:
            if not isinstance(event, MouseButtonEvent):
                raise TypeError(f"Event {event_id!r} is not a MouseButtonEvent")
            event.color_check_enabled = not event.color_check_enabled
            return MacroData(
                meta=macro.meta,
                settings=macro.settings,
                raw_events=macro.raw_events,
                events=updated,
                is_edited=True,
            )
    raise KeyError(f"Event id not found: {event_id!r}")


def set_color_check_on_mismatch(
    macro: MacroData, event_id: str, action: Literal["skip", "stop", "wait"]
) -> MacroData:
    """events에서 특정 mouse_down 이벤트의 color_check_on_mismatch를 변경한다.

    Args:
        macro: 원본 MacroData.
        event_id: 수정할 mouse_down 이벤트 id.
        action: "skip" — 불일치 시 해당 클릭만 스킵 후 계속 실행.
                "stop" — 불일치 시 재생 전체 즉시 중단.
                "wait" — 최대 10초 동안 색 일치를 기다린 뒤 클릭 진행.

    Returns:
        color_check_on_mismatch가 변경된 새 MacroData (is_edited=True).

    Raises:
        KeyError: 해당 id를 가진 이벤트가 없는 경우.
        TypeError: 해당 이벤트가 MouseButtonEvent가 아닌 경우.
    """
    updated = copy.deepcopy(macro.events)
    for event in updated:
        if event.id == event_id:
            if not isinstance(event, MouseButtonEvent):
                raise TypeError(f"Event {event_id!r} is not a MouseButtonEvent")
            event.color_check_on_mismatch = action
            return MacroData(
                meta=macro.meta,
                settings=macro.settings,
                raw_events=macro.raw_events,
                events=updated,
                is_edited=True,
            )
    raise KeyError(f"Event id not found: {event_id!r}")
