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
import shutil
from pathlib import Path
from typing import Any

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
    }

    match d["type"]:
        case "mouse_down" | "mouse_up":
            return MouseButtonEvent(
                **common,
                x_ratio=d["x_ratio"],
                y_ratio=d["y_ratio"],
                button=d.get("button", "left"),
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
                timeout_ms=d.get("timeout_ms", 10000),
                check_interval_ms=d.get("check_interval_ms", 50),
                on_timeout=d.get("on_timeout", "error"),
            )
        case "window_trigger":
            return WindowTriggerEvent(
                **common,
                window_title_contains=d["window_title_contains"],
                timeout_ms=d.get("timeout_ms", 10000),
                on_timeout=d.get("on_timeout", "error"),
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
        settings = MacroSettings(**raw.get("settings", {}))
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


def set_delay_all(macro: MacroData, delay_ms: int) -> MacroData:
    """events 전체의 delay_override_ms를 동일 값으로 설정한다.

    Args:
        macro: 원본 MacroData.
        delay_ms: 설정할 딜레이 (밀리초).

    Returns:
        딜레이가 일괄 설정된 새 MacroData (is_edited=True).
    """
    updated = copy.deepcopy(macro.events)
    for event in updated:
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
