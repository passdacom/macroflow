"""Event editor display row construction.

This module intentionally stays free of Qt widget dependencies so display semantics
can be tested without loading PyQt on headless CI.
"""

from __future__ import annotations

import dataclasses

from macroflow.types import (
    AnyEvent,
    ColorTriggerEvent,
    ConditionEvent,
    KeyEvent,
    LoopEvent,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    TextInputEvent,
    WaitEvent,
    WindowTriggerEvent,
)

# ── 표시 행 정책 ─────────────────────────────────────────────────────────────

KIND_CLICK = "click"
KIND_RIGHT_CLICK = "right_click"
KIND_DRAG = "drag"
KIND_RIGHT_DRAG = "right_drag"
KIND_COLOR_CHECK_CLICK = "color_check_click"
KIND_COLOR_CHECK_RIGHT_CLICK = "color_check_right_click"
KIND_COLOR_CHECK_CLICK_STOP = "color_check_click_stop"
KIND_COLOR_CHECK_RIGHT_CLICK_STOP = "color_check_right_click_stop"
KIND_COLOR_CHECK_CLICK_WAIT = "color_check_click_wait"
KIND_COLOR_CHECK_RIGHT_CLICK_WAIT = "color_check_right_click_wait"
KIND_TEXT_INPUT = "text_input"
KIND_KEY_PRESS = "key_press"
KIND_MOUSE_MOVE = "mouse_move"
KIND_MOUSE_WHEEL = "mouse_wheel"
KIND_WAIT = "wait"
KIND_COLOR_TRIGGER = "color_trigger"
KIND_WINDOW_TRIGGER = "window_trigger"
KIND_CONDITION = "condition"
KIND_LOOP = "loop"
KIND_ORPHAN = "orphan"

COLOR_CHECK_CLICK_KINDS = (
    KIND_CLICK,
    KIND_RIGHT_CLICK,
    KIND_DRAG,
    KIND_RIGHT_DRAG,
    KIND_COLOR_CHECK_CLICK,
    KIND_COLOR_CHECK_RIGHT_CLICK,
    KIND_COLOR_CHECK_CLICK_STOP,
    KIND_COLOR_CHECK_RIGHT_CLICK_STOP,
    KIND_COLOR_CHECK_CLICK_WAIT,
    KIND_COLOR_CHECK_RIGHT_CLICK_WAIT,
)

POSITION_EDIT_KINDS = COLOR_CHECK_CLICK_KINDS + (KIND_ORPHAN, KIND_MOUSE_MOVE)

DISPLAY_ROW_KINDS = (
    *POSITION_EDIT_KINDS,
    KIND_TEXT_INPUT,
    KIND_KEY_PRESS,
    KIND_MOUSE_WHEEL,
    KIND_WAIT,
    KIND_COLOR_TRIGGER,
    KIND_WINDOW_TRIGGER,
    KIND_CONDITION,
    KIND_LOOP,
)


# ── 표시 행 데이터 ─────────────────────────────────────────────────────────────

@dataclasses.dataclass
class _DisplayRow:
    """에디터 테이블의 한 행을 나타낸다."""

    kind: str                 # 색상/편집 동작 결정
    label: str                # 타입 열 텍스트
    detail: str               # 내용 열 텍스트
    time_ms: float            # 시간(ms) 열 값
    delay_str: str            # 딜레이(ms) 열 텍스트
    event_indices: list[int]  # 이 행이 나타내는 이벤트 인덱스들
    primary_idx: int          # 딜레이/편집 기준 이벤트 인덱스
    source_file: str = ""     # 출처 파일명 (병합 매크로에서 설정)
    color_check_enabled: bool = False         # 색 체크 활성 여부
    color_check_on_mismatch: str = "skip"     # "skip" | "stop" | "wait"
    time_ms_rel: float = 0.0                  # 이전 이벤트 대비 delta(ms). 상대 시간 표시용.
    color_hex: str | None = None              # 내용 열 옆 색상 박스에 표시할 #RRGGBB 값.
    remark: str = ""                          # 비고 열에 표시할 사용자 메모.


def _delay_str(event: AnyEvent) -> str:
    return str(event.delay_override_ms) if event.delay_override_ms is not None else ""


def _time_ms(event: AnyEvent) -> float:
    return event.timestamp_ns / 1_000_000


def _button_label(button: str) -> str:
    return "왼쪽" if button == "left" else "오른쪽"


def _position_detail(x_ratio: float, y_ratio: float) -> str:
    return f"({x_ratio * 100:.1f}%, {y_ratio * 100:.1f}%)"


def _color_check_kind(button: str, mismatch: str) -> str:
    if button == "left":
        if mismatch == "stop":
            return KIND_COLOR_CHECK_CLICK_STOP
        if mismatch == "wait":
            return KIND_COLOR_CHECK_CLICK_WAIT
        return KIND_COLOR_CHECK_CLICK
    if mismatch == "stop":
        return KIND_COLOR_CHECK_RIGHT_CLICK_STOP
    if mismatch == "wait":
        return KIND_COLOR_CHECK_RIGHT_CLICK_WAIT
    return KIND_COLOR_CHECK_RIGHT_CLICK


def _color_check_emoji(mismatch: str) -> str:
    if mismatch == "stop":
        return "🛑"
    if mismatch == "wait":
        return "⏳"
    return "🎨"


def _build_mouse_down_row(
    events: list[AnyEvent],
    index: int,
    consumed: set[int],
) -> _DisplayRow:
    event = events[index]
    assert isinstance(event, MouseButtonEvent)

    move_indices: list[int] = []
    up_idx: int | None = None

    for j in range(index + 1, len(events)):
        if j in consumed:
            continue
        e2 = events[j]
        if isinstance(e2, MouseMoveEvent):
            move_indices.append(j)
        elif (
            isinstance(e2, MouseButtonEvent)
            and e2.type == "mouse_up"
            and e2.button == event.button
        ):
            up_idx = j
            break

    btn_ko = _button_label(event.button)
    base_detail = _position_detail(event.x_ratio, event.y_ratio)
    is_color_check = event.color_check_enabled and event.recorded_color is not None

    if up_idx is None:
        consumed.add(index)
        return _DisplayRow(
            KIND_ORPHAN, f"눌림({btn_ko})", base_detail,
            _time_ms(event), _delay_str(event), [index], index,
        )

    all_indices = [index] + move_indices + [up_idx]
    consumed.update(all_indices)

    if len(move_indices) > 3:
        kind = KIND_DRAG if event.button == "left" else KIND_RIGHT_DRAG
        label = f"드래그({btn_ko})"
        emoji = _color_check_emoji(event.color_check_on_mismatch) if is_color_check else "🎨"
    elif is_color_check:
        emoji = _color_check_emoji(event.color_check_on_mismatch)
        kind = _color_check_kind(event.button, event.color_check_on_mismatch)
        label = f"클릭({btn_ko}) {emoji}"
    else:
        emoji = "🎨"
        kind = KIND_CLICK if event.button == "left" else KIND_RIGHT_CLICK
        label = f"클릭({btn_ko})"

    # 색 정보 표시: 체크 활성=색 강조, 비활성=회색 괄호
    if event.recorded_color:
        if is_color_check:
            color_tag = f" {emoji}{event.recorded_color}"
        else:
            color_tag = f" [{event.recorded_color}]"
        detail = f"{base_detail}{color_tag}"
    else:
        detail = base_detail

    return _DisplayRow(
        kind, label, detail,
        _time_ms(event), _delay_str(event), all_indices, index,
        color_check_enabled=is_color_check,
        color_check_on_mismatch=event.color_check_on_mismatch,
        color_hex=event.recorded_color,
    )


def _build_mouse_up_row(event: MouseButtonEvent, index: int) -> _DisplayRow:
    btn_ko = _button_label(event.button)
    return _DisplayRow(
        KIND_ORPHAN, f"뗌({btn_ko})", _position_detail(event.x_ratio, event.y_ratio),
        _time_ms(event), _delay_str(event), [index], index,
    )


def _build_mouse_move_row(event: MouseMoveEvent, index: int) -> _DisplayRow:
    return _DisplayRow(
        KIND_MOUSE_MOVE, "마우스 이동", _position_detail(event.x_ratio, event.y_ratio),
        _time_ms(event), _delay_str(event), [index], index,
    )


def _build_key_down_row(events: list[AnyEvent], index: int, consumed: set[int]) -> _DisplayRow:
    event = events[index]
    assert isinstance(event, KeyEvent)

    up_idx = None
    for j in range(index + 1, len(events)):
        if j in consumed:
            continue
        e2 = events[j]
        if isinstance(e2, KeyEvent) and e2.type == "key_up" and e2.vk_code == event.vk_code:
            up_idx = j
            break

    consumed.add(index)
    if up_idx is not None:
        consumed.add(up_idx)
        return _DisplayRow(
            KIND_KEY_PRESS, "키 입력", event.key,
            _time_ms(event), _delay_str(event), [index, up_idx], index,
        )
    return _DisplayRow(
        KIND_KEY_PRESS, "키 누름", event.key,
        _time_ms(event), _delay_str(event), [index], index,
    )


def _build_key_up_row(event: KeyEvent, index: int) -> _DisplayRow:
    return _DisplayRow(
        KIND_KEY_PRESS, "키 뗌", event.key,
        _time_ms(event), _delay_str(event), [index], index,
    )


def _build_text_input_row(event: TextInputEvent, index: int) -> _DisplayRow:
    preview = event.text if len(event.text) <= 30 else event.text[:27] + "..."
    return _DisplayRow(
        KIND_TEXT_INPUT, "텍스트 입력", f'"{preview}"',
        _time_ms(event), _delay_str(event), [index], index,
    )


def _build_wait_row(event: WaitEvent, index: int) -> _DisplayRow:
    return _DisplayRow(
        KIND_WAIT, "대기", f"{event.duration_ms}ms",
        _time_ms(event), _delay_str(event), [index], index,
    )


def _build_mouse_wheel_row(events: list[AnyEvent], index: int, consumed: set[int]) -> _DisplayRow:
    event = events[index]
    assert isinstance(event, MouseWheelEvent)

    # 연속된 같은 축(axis) 휠 이벤트를 하나의 행으로 그룹핑한다.
    # 다른 이벤트 타입이 사이에 끼면 그룹을 끊는다.
    group_indices: list[int] = [index]
    total_delta: int = event.delta
    for j in range(index + 1, len(events)):
        if j in consumed:
            break
        e2 = events[j]
        if isinstance(e2, MouseWheelEvent) and e2.axis == event.axis:
            group_indices.append(j)
            total_delta += e2.delta
        else:
            break
    consumed.update(group_indices)

    # 방향 아이콘 결정
    if event.axis == "vertical":
        icon = "↑" if total_delta > 0 else "↓"
        label = f"↕ 휠 {'위' if total_delta > 0 else '아래'}"
    else:
        icon = "→" if total_delta > 0 else "←"
        label = f"↔ 휠 {'우' if total_delta > 0 else '좌'}"

    notches = abs(total_delta) // 120 or 1  # 0 방지
    count_str = f" ×{len(group_indices)}" if len(group_indices) > 1 else ""
    detail = (
        f"{icon} {notches}노치  Δ{total_delta:+d}{count_str}"
        f"  @ {_position_detail(event.x_ratio, event.y_ratio)}"
    )
    return _DisplayRow(
        KIND_MOUSE_WHEEL, label, detail,
        _time_ms(event), _delay_str(event), group_indices, index,
    )


def _build_color_trigger_row(event: ColorTriggerEvent, index: int) -> _DisplayRow:
    return _DisplayRow(
        KIND_COLOR_TRIGGER, "색 트리거",
        f"{_position_detail(event.x_ratio, event.y_ratio)} {event.target_color}",
        _time_ms(event), _delay_str(event), [index], index,
        color_hex=event.target_color,
    )


def _build_window_trigger_row(event: WindowTriggerEvent, index: int) -> _DisplayRow:
    return _DisplayRow(
        KIND_WINDOW_TRIGGER, "창 트리거", event.window_title_contains,
        _time_ms(event), _delay_str(event), [index], index,
    )


def _build_condition_row(event: ConditionEvent, index: int) -> _DisplayRow:
    return _DisplayRow(
        KIND_CONDITION, "조건 분기", event.expression[:30],
        _time_ms(event), _delay_str(event), [index], index,
    )


def _build_loop_row(event: LoopEvent, index: int) -> _DisplayRow:
    return _DisplayRow(
        KIND_LOOP, "반복", f"×{event.count}",
        _time_ms(event), _delay_str(event), [index], index,
    )


def _apply_row_metadata(rows: list[_DisplayRow], events: list[AnyEvent]) -> None:
    # primary 이벤트 기준으로 비고를 표시한다. 그룹 내부 secondary 이벤트의 비고는 저장/로드로 보존하되 UI 행에는 직접 표시하지 않는다.
    for row in rows:
        row.remark = events[row.primary_idx].remark

    # 상대 시간 계산: 각 행의 primary 이벤트 기준
    for i, row in enumerate(rows):
        ev = events[row.primary_idx]
        if ev.delay_override_ms is not None:
            row.time_ms_rel = float(ev.delay_override_ms)
        elif i == 0:
            row.time_ms_rel = row.time_ms  # 첫 행은 절대값 그대로
        else:
            prev_ev = events[rows[i - 1].primary_idx]
            row.time_ms_rel = (ev.timestamp_ns - prev_ev.timestamp_ns) / 1_000_000


def _build_rows(events: list[AnyEvent], show_moves: bool) -> list[_DisplayRow]:
    """events 리스트를 표시용 _DisplayRow 리스트로 변환한다.

    연속된 mouse_down+up → 클릭/드래그 한 행으로 그룹화.
    연속된 key_down+up → 키 입력 한 행으로 그룹화.
    show_moves=False 이면 mouse_move는 행 목록에서 제외.
    """
    rows: list[_DisplayRow] = []
    consumed: set[int] = set()

    for i, event in enumerate(events):
        if i in consumed:
            continue

        if isinstance(event, MouseButtonEvent) and event.type == "mouse_down":
            rows.append(_build_mouse_down_row(events, i, consumed))
        elif isinstance(event, MouseButtonEvent) and event.type == "mouse_up":
            consumed.add(i)
            rows.append(_build_mouse_up_row(event, i))
        elif isinstance(event, MouseMoveEvent):
            consumed.add(i)
            if show_moves:
                rows.append(_build_mouse_move_row(event, i))
        elif isinstance(event, KeyEvent) and event.type == "key_down":
            rows.append(_build_key_down_row(events, i, consumed))
        elif isinstance(event, KeyEvent) and event.type == "key_up":
            consumed.add(i)
            rows.append(_build_key_up_row(event, i))
        elif isinstance(event, TextInputEvent):
            consumed.add(i)
            rows.append(_build_text_input_row(event, i))
        elif isinstance(event, WaitEvent):
            consumed.add(i)
            rows.append(_build_wait_row(event, i))
        elif isinstance(event, MouseWheelEvent):
            rows.append(_build_mouse_wheel_row(events, i, consumed))
        elif isinstance(event, ColorTriggerEvent):
            consumed.add(i)
            rows.append(_build_color_trigger_row(event, i))
        elif isinstance(event, WindowTriggerEvent):
            consumed.add(i)
            rows.append(_build_window_trigger_row(event, i))
        elif isinstance(event, ConditionEvent):
            consumed.add(i)
            rows.append(_build_condition_row(event, i))
        elif isinstance(event, LoopEvent):
            consumed.add(i)
            rows.append(_build_loop_row(event, i))

    _apply_row_metadata(rows, events)
    return rows
