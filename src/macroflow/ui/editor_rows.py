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


def _delay_str(event: AnyEvent) -> str:
    return str(event.delay_override_ms) if event.delay_override_ms is not None else ""


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

        # ── 마우스 버튼 down ──────────────────────────────────────────────────
        if isinstance(event, MouseButtonEvent) and event.type == "mouse_down":
            move_indices: list[int] = []
            up_idx: int | None = None

            for j in range(i + 1, len(events)):
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

            btn_ko = "왼쪽" if event.button == "left" else "오른쪽"
            x_s = f"{event.x_ratio * 100:.1f}%"
            y_s = f"{event.y_ratio * 100:.1f}%"
            is_color_check = event.color_check_enabled and event.recorded_color is not None

            if up_idx is not None:
                all_indices = [i] + move_indices + [up_idx]
                consumed.update(all_indices)
                if len(move_indices) > 3:
                    kind = "drag" if event.button == "left" else "right_drag"
                    label = f"드래그({btn_ko})"
                elif is_color_check:
                    mismatch = event.color_check_on_mismatch
                    is_stop = mismatch == "stop"
                    is_wait = mismatch == "wait"
                    emoji = "🛑" if is_stop else ("⏳" if is_wait else "🎨")
                    if event.button == "left":
                        if is_stop:
                            kind = "color_check_click_stop"
                        elif is_wait:
                            kind = "color_check_click_wait"
                        else:
                            kind = "color_check_click"
                    else:
                        if is_stop:
                            kind = "color_check_right_click_stop"
                        elif is_wait:
                            kind = "color_check_right_click_wait"
                        else:
                            kind = "color_check_right_click"
                    label = f"클릭({btn_ko}) {emoji}"
                else:
                    is_stop = False
                    emoji = "🎨"
                    kind = "click" if event.button == "left" else "right_click"
                    label = f"클릭({btn_ko})"
                # 색 정보 표시: 체크 활성=색 강조, 비활성=회색 괄호
                if event.recorded_color:
                    if is_color_check:
                        color_tag = f" {emoji}{event.recorded_color}"
                    else:
                        color_tag = f" [{event.recorded_color}]"
                    detail = f"({x_s}, {y_s}){color_tag}"
                else:
                    detail = f"({x_s}, {y_s})"
                rows.append(_DisplayRow(
                    kind, label, detail,
                    event.timestamp_ns / 1_000_000,
                    _delay_str(event), all_indices, i,
                    color_check_enabled=is_color_check,
                    color_check_on_mismatch=event.color_check_on_mismatch,
                    color_hex=event.recorded_color,
                ))
            else:
                consumed.add(i)
                rows.append(_DisplayRow(
                    "orphan", f"눌림({btn_ko})", f"({x_s}, {y_s})",
                    event.timestamp_ns / 1_000_000,
                    _delay_str(event), [i], i,
                ))

        # ── 마우스 버튼 up (미소비) ───────────────────────────────────────────
        elif isinstance(event, MouseButtonEvent) and event.type == "mouse_up":
            consumed.add(i)
            btn_ko = "왼쪽" if event.button == "left" else "오른쪽"
            x_s = f"{event.x_ratio * 100:.1f}%"
            y_s = f"{event.y_ratio * 100:.1f}%"
            rows.append(_DisplayRow(
                "orphan", f"뗌({btn_ko})", f"({x_s}, {y_s})",
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 마우스 이동 ───────────────────────────────────────────────────────
        elif isinstance(event, MouseMoveEvent):
            consumed.add(i)
            if show_moves:
                x_s = f"{event.x_ratio * 100:.1f}%"
                y_s = f"{event.y_ratio * 100:.1f}%"
                rows.append(_DisplayRow(
                    "mouse_move", "마우스 이동", f"({x_s}, {y_s})",
                    event.timestamp_ns / 1_000_000,
                    _delay_str(event), [i], i,
                ))

        # ── 키 누름 ───────────────────────────────────────────────────────────
        elif isinstance(event, KeyEvent) and event.type == "key_down":
            up_idx = None
            for j in range(i + 1, len(events)):
                if j in consumed:
                    continue
                e2 = events[j]
                if (
                    isinstance(e2, KeyEvent)
                    and e2.type == "key_up"
                    and e2.vk_code == event.vk_code
                ):
                    up_idx = j
                    break

            if up_idx is not None:
                consumed.add(i)
                consumed.add(up_idx)
                rows.append(_DisplayRow(
                    "key_press", "키 입력", event.key,
                    event.timestamp_ns / 1_000_000,
                    _delay_str(event), [i, up_idx], i,
                ))
            else:
                consumed.add(i)
                rows.append(_DisplayRow(
                    "key_press", "키 누름", event.key,
                    event.timestamp_ns / 1_000_000,
                    _delay_str(event), [i], i,
                ))

        # ── 키 뗌 (미소비) ────────────────────────────────────────────────────
        elif isinstance(event, KeyEvent) and event.type == "key_up":
            consumed.add(i)
            rows.append(_DisplayRow(
                "key_press", "키 뗌", event.key,
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 텍스트 입력 ──────────────────────────────────────────────────────────────────────
        elif isinstance(event, TextInputEvent):
            consumed.add(i)
            preview = event.text if len(event.text) <= 30 else event.text[:27] + "..."
            rows.append(_DisplayRow(
                "text_input", "텍스트 입력", f'"{preview}"',
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 대기 ─────────────────────────────────────────────────────────────
        elif isinstance(event, WaitEvent):
            consumed.add(i)
            rows.append(_DisplayRow(
                "wait", "대기", f"{event.duration_ms}ms",
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 마우스 휠 ────────────────────────────────────────────────────────
        elif isinstance(event, MouseWheelEvent):
            # 연속된 같은 축(axis) 휠 이벤트를 하나의 행으로 그룹핑한다.
            # 다른 이벤트 타입이 사이에 끼면 그룹을 끊는다.
            group_indices: list[int] = [i]
            total_delta: int = event.delta
            for j in range(i + 1, len(events)):
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
            x_s = f"{event.x_ratio * 100:.1f}%"
            y_s = f"{event.y_ratio * 100:.1f}%"
            detail = (
                f"{icon} {notches}노치  Δ{total_delta:+d}{count_str}"
                f"  @ ({x_s}, {y_s})"
            )
            rows.append(_DisplayRow(
                "mouse_wheel", label, detail,
                event.timestamp_ns / 1_000_000,
                _delay_str(event), group_indices, i,
            ))

        # ── 색 트리거 ─────────────────────────────────────────────────────────
        elif isinstance(event, ColorTriggerEvent):
            consumed.add(i)
            x_s = f"{event.x_ratio * 100:.1f}%"
            y_s = f"{event.y_ratio * 100:.1f}%"
            rows.append(_DisplayRow(
                "color_trigger", "색 트리거",
                f"({x_s}, {y_s}) {event.target_color}",
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
                color_hex=event.target_color,
            ))

        # ── 창 트리거 ─────────────────────────────────────────────────────────
        elif isinstance(event, WindowTriggerEvent):
            consumed.add(i)
            rows.append(_DisplayRow(
                "window_trigger", "창 트리거",
                event.window_title_contains,
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 조건 분기 ─────────────────────────────────────────────────────────
        elif isinstance(event, ConditionEvent):
            consumed.add(i)
            rows.append(_DisplayRow(
                "condition", "조건 분기",
                event.expression[:30],
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

        # ── 반복 ─────────────────────────────────────────────────────────────
        elif isinstance(event, LoopEvent):
            consumed.add(i)
            rows.append(_DisplayRow(
                "loop", "반복", f"×{event.count}",
                event.timestamp_ns / 1_000_000,
                _delay_str(event), [i], i,
            ))

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

    return rows
