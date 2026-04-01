"""macro_file.py 직렬화·역직렬화 및 편집 함수 테스트."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from macroflow.macro_file import (
    delete_mouse_moves,
    edit_wheel_delta,
    load,
    reset_to_raw,
    save,
    set_delay_all,
    set_delay_single,
)
from macroflow.types import (
    ColorTriggerEvent,
    KeyEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    MouseMoveEvent,
    MouseWheelEvent,
    WaitEvent,
)

# ── 픽스처 ────────────────────────────────────────────────────────────────────

def _make_macro() -> MacroData:
    """테스트용 최소 MacroData를 생성한다."""
    events = [
        MouseButtonEvent(
            id="a1b2c3d4", type="mouse_down", timestamp_ns=1_000_000_000,
            x_ratio=0.5, y_ratio=0.5, button="left",
        ),
        MouseMoveEvent(
            id="b2c3d4e5", type="mouse_move", timestamp_ns=1_020_000_000,
            x_ratio=0.501, y_ratio=0.500,
        ),
        MouseButtonEvent(
            id="c3d4e5f6", type="mouse_up", timestamp_ns=1_087_000_000,
            x_ratio=0.502, y_ratio=0.501, button="left",
        ),
        KeyEvent(
            id="d4e5f6a7", type="key_down", timestamp_ns=2_000_000_000,
            key="enter", vk_code=0x0D,
        ),
        KeyEvent(
            id="e5f6a7b8", type="key_up", timestamp_ns=2_050_000_000,
            key="enter", vk_code=0x0D,
        ),
    ]
    return MacroData(
        meta=MacroMeta(
            version="1.0", app_version="0.1.0",
            created_at="2025-01-15T14:30:00",
            screen_width=1920, screen_height=1080, dpi_scale=1.0,
            author="test", description="test macro",
        ),
        settings=MacroSettings(),
        raw_events=copy.deepcopy(events),
        events=events,
    )


# ── 직렬화·역직렬화 ──────────────────────────────────────────────────────────

def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    """저장 후 로드하면 동일한 MacroData가 반환되어야 한다."""
    macro = _make_macro()
    path = str(tmp_path / "test.json")

    save(macro, path)
    loaded = load(path)

    assert loaded.meta.version == macro.meta.version
    assert loaded.meta.author == "test"
    assert len(loaded.events) == len(macro.events)
    assert len(loaded.raw_events) == len(macro.raw_events)
    assert loaded.is_edited == macro.is_edited


def test_save_creates_bak(tmp_path: Path) -> None:
    """기존 파일이 있을 때 저장하면 .bak 파일이 생성되어야 한다."""
    macro = _make_macro()
    path = tmp_path / "test.json"
    bak_path = path.with_suffix(".bak")

    save(macro, str(path))
    assert not bak_path.exists()

    save(macro, str(path))
    assert bak_path.exists()


def test_load_missing_file(tmp_path: Path) -> None:
    """존재하지 않는 파일을 로드하면 FileNotFoundError가 발생해야 한다."""
    with pytest.raises(FileNotFoundError):
        load(str(tmp_path / "nonexistent.json"))


def test_event_types_roundtrip(tmp_path: Path) -> None:
    """모든 이벤트 타입이 저장 후 동일 타입으로 복원되어야 한다."""
    events = [
        MouseButtonEvent(id="00000001", type="mouse_down", timestamp_ns=100,
                         x_ratio=0.1, y_ratio=0.2, button="right"),
        MouseMoveEvent(id="00000002", type="mouse_move", timestamp_ns=200,
                       x_ratio=0.11, y_ratio=0.21),
        MouseButtonEvent(id="00000003", type="mouse_up", timestamp_ns=300,
                         x_ratio=0.12, y_ratio=0.22, button="right"),
        KeyEvent(id="00000004", type="key_down", timestamp_ns=400,
                 key="a", vk_code=0x41),
        KeyEvent(id="00000005", type="key_up", timestamp_ns=450,
                 key="a", vk_code=0x41),
        WaitEvent(id="00000006", type="wait", timestamp_ns=500,
                  duration_ms=200),
        ColorTriggerEvent(
            id="00000007", type="color_trigger", timestamp_ns=600,
            x_ratio=0.5, y_ratio=0.9, target_color="#FFFFFF",
            tolerance=10, timeout_ms=5000, check_interval_ms=50,
            on_timeout="skip",
        ),
    ]
    macro = MacroData(
        meta=MacroMeta(version="1.0", app_version="0.1.0",
                       created_at="2025-01-15T00:00:00",
                       screen_width=1920, screen_height=1080, dpi_scale=1.0),
        settings=MacroSettings(),
        raw_events=copy.deepcopy(events),
        events=events,
    )

    path = str(tmp_path / "types.json")
    save(macro, path)
    loaded = load(path)

    type_names = [e.type for e in loaded.events]
    assert type_names == ["mouse_down", "mouse_move", "mouse_up",
                          "key_down", "key_up", "wait", "color_trigger"]


def test_wheel_event_roundtrip(tmp_path: Path) -> None:
    """MouseWheelEvent가 저장 후 동일 값으로 복원되어야 한다."""
    wheel = MouseWheelEvent(
        id="00000010", type="mouse_wheel", timestamp_ns=1000,
        delta=-240, axis="vertical", x_ratio=0.5, y_ratio=0.5,
    )
    macro = MacroData(
        meta=MacroMeta(version="1.0", app_version="0.1.0",
                       created_at="2025-01-15T00:00:00",
                       screen_width=1920, screen_height=1080, dpi_scale=1.0),
        settings=MacroSettings(),
        raw_events=[wheel],
        events=[wheel],
    )
    path = str(tmp_path / "wheel.json")
    save(macro, path)
    loaded = load(path)

    assert len(loaded.events) == 1
    ev = loaded.events[0]
    assert isinstance(ev, MouseWheelEvent)
    assert ev.delta == -240
    assert ev.axis == "vertical"
    assert ev.x_ratio == pytest.approx(0.5)


def test_edit_wheel_delta() -> None:
    """edit_wheel_delta는 지정 이벤트의 delta만 변경하고 나머지는 유지한다."""
    wheel = MouseWheelEvent(
        id="00000011", type="mouse_wheel", timestamp_ns=500,
        delta=120, axis="vertical", x_ratio=0.3, y_ratio=0.4,
    )
    macro = MacroData(
        meta=MacroMeta(version="1.0", app_version="0.1.0",
                       created_at="2025-01-15T00:00:00",
                       screen_width=1920, screen_height=1080, dpi_scale=1.0),
        settings=MacroSettings(),
        raw_events=[wheel],
        events=[wheel],
    )

    result = edit_wheel_delta(macro, "00000011", -360)

    assert result.events[0].delta == -360  # type: ignore[union-attr]
    assert result.is_edited is True
    # raw_events 불변
    assert macro.raw_events[0].delta == 120  # type: ignore[union-attr]


# ── 편집 함수 ─────────────────────────────────────────────────────────────────

def test_delete_mouse_moves() -> None:
    """delete_mouse_moves는 events에서 mouse_move만 제거하고 raw_events는 유지한다."""
    macro = _make_macro()
    result = delete_mouse_moves(macro)

    assert all(e.type != "mouse_move" for e in result.events)
    assert any(e.type == "mouse_move" for e in result.raw_events)
    assert result.is_edited is True
    assert len(result.events) == len(macro.events) - 1


def test_set_delay_all() -> None:
    """set_delay_all은 events 전체의 delay_override_ms를 동일값으로 설정한다."""
    macro = _make_macro()
    result = set_delay_all(macro, 100)

    assert all(e.delay_override_ms == 100 for e in result.events)
    assert result.is_edited is True
    # raw_events는 변경 없음
    assert all(e.delay_override_ms is None for e in result.raw_events)


def test_set_delay_single() -> None:
    """set_delay_single은 특정 id의 delay_override_ms만 수정한다."""
    macro = _make_macro()
    target_id = macro.events[0].id

    result = set_delay_single(macro, target_id, 200)

    assert result.events[0].delay_override_ms == 200
    assert all(e.delay_override_ms is None for e in result.events[1:])
    assert result.is_edited is True


def test_set_delay_single_to_none() -> None:
    """delay_override_ms를 None으로 설정하면 원래 타이밍 기준으로 복원된다."""
    macro = set_delay_all(_make_macro(), 100)
    target_id = macro.events[0].id

    result = set_delay_single(macro, target_id, None)
    assert result.events[0].delay_override_ms is None


def test_set_delay_single_invalid_id() -> None:
    """없는 id를 사용하면 KeyError가 발생해야 한다."""
    macro = _make_macro()
    with pytest.raises(KeyError):
        set_delay_single(macro, "ffffffff", 100)


def test_reset_to_raw() -> None:
    """reset_to_raw는 events를 raw_events 복사본으로 되돌리고 is_edited=False로 설정한다."""
    macro = delete_mouse_moves(_make_macro())
    assert macro.is_edited is True

    restored = reset_to_raw(macro)

    assert restored.is_edited is False
    assert len(restored.events) == len(restored.raw_events)
    # raw_events와 events는 동일한 내용이지만 독립적인 객체여야 한다
    assert restored.events is not restored.raw_events
