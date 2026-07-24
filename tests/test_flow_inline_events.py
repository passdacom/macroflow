"""Inline event flow-node codec and compatibility contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from macroflow.macro_file import save as save_macro
from macroflow.script_engine import (
    EndNode,
    FlowEngine,
    InlineEventsNode,
    MacroFlow,
    MacroNode,
    load_flow,
    save_flow,
)
from macroflow.types import (
    KeyEvent,
    MacroData,
    MacroMeta,
    MacroSettings,
    MouseButtonEvent,
    TextInputEvent,
)


def _inline_flow() -> MacroFlow:
    return MacroFlow(
        version="1.1",
        name="mixed sequence",
        created_at="2026-07-24T00:00:00",
        start_node_id="inline_000",
        nodes={
            "inline_000": InlineEventsNode(
                id="inline_000",
                label="좌클릭",
                events=[
                    MouseButtonEvent(
                        id="down0001",
                        type="mouse_down",
                        timestamp_ns=0,
                        x_ratio=0.25,
                        y_ratio=0.75,
                        button="left",
                    ),
                    MouseButtonEvent(
                        id="up000001",
                        type="mouse_up",
                        timestamp_ns=100_000_000,
                        x_ratio=0.25,
                        y_ratio=0.75,
                        button="left",
                    ),
                ],
                playback_settings=MacroSettings(
                    click_dist_threshold_px=12,
                    color_trigger_check_interval_ms=75,
                ),
                next_on_success="end_success",
                next_on_failure="end_error",
            ),
            "end_success": EndNode(id="end_success", label="완료"),
            "end_error": EndNode(
                id="end_error",
                label="오류",
                status="error",
            ),
        },
    )


def test_inline_events_node_v11_strict_roundtrip(tmp_path: Path) -> None:
    target = tmp_path / "mixed.macroflow"
    flow = _inline_flow()

    save_flow(flow, str(target))

    assert load_flow(str(target), strict=True) == flow
    raw = json.loads(target.read_text(encoding="utf-8"))
    inline = raw["nodes"]["inline_000"]
    assert inline["type"] == "inline_events"
    assert inline["events"][0]["button"] == "left"
    assert inline["playback_settings"]["click_dist_threshold_px"] == 12


def test_strict_inline_load_rejects_boolean_timestamp(tmp_path: Path) -> None:
    target = tmp_path / "bool-timestamp.macroflow"
    save_flow(_inline_flow(), str(target))
    raw = json.loads(target.read_text(encoding="utf-8"))
    raw["nodes"]["inline_000"]["events"][0]["timestamp_ns"] = True
    target.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="정규 형식"):
        load_flow(str(target), strict=True)


@pytest.mark.parametrize("ratio", [float("inf"), float("-inf"), float("nan")])
def test_strict_inline_load_rejects_non_finite_coordinates(
    tmp_path: Path,
    ratio: float,
) -> None:
    target = tmp_path / "bad-ratio.macroflow"
    save_flow(_inline_flow(), str(target))
    raw = json.loads(target.read_text(encoding="utf-8"))
    raw["nodes"]["inline_000"]["events"][1]["x_ratio"] = ratio
    target.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="정규 형식"):
        load_flow(str(target), strict=True)


def test_strict_load_rejects_unsupported_flow_version(tmp_path: Path) -> None:
    target = tmp_path / "future.macroflow"
    save_flow(_inline_flow(), str(target))
    raw = json.loads(target.read_text(encoding="utf-8"))
    raw["meta"]["version"] = "9.9"
    target.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="지원하지 않는 플로우 버전"):
        load_flow(str(target), strict=True)


def test_v10_strict_codec_keeps_existing_graph_compatibility(tmp_path: Path) -> None:
    target = tmp_path / "legacy-graph.macroflow"
    flow = MacroFlow(
        version="1.0",
        name="legacy graph",
        created_at="2025-01-01T00:00:00",
        start_node_id="end_success",
        nodes={
            "end_success": EndNode(id="end_success", label="완료", status="success"),
            "unused_error": EndNode(id="unused_error", label="예비 오류", status="error"),
        },
    )

    save_flow(flow, str(target))

    assert load_flow(str(target), strict=True) == flow


def test_v10_rejects_inline_node_and_v11_rejects_non_mvp_event(tmp_path: Path) -> None:
    target = tmp_path / "invalid-inline.macroflow"
    flow = _inline_flow()
    flow.version = "1.0"
    save_flow(flow, str(target))
    with pytest.raises(ValueError, match="v1.0.*inline_events"):
        load_flow(str(target), strict=True)

    flow.version = "1.1"
    inline = flow.nodes["inline_000"]
    assert isinstance(inline, InlineEventsNode)
    inline.events = [
        KeyEvent(
            id="key00001",
            type="key_down",
            timestamp_ns=0,
            key="enter",
            vk_code=13,
        )
    ]
    save_flow(flow, str(target))
    with pytest.raises(ValueError, match="정규 형식"):
        load_flow(str(target), strict=True)


def test_strict_rejects_invalid_terminal_and_inline_semantics(tmp_path: Path) -> None:
    target = tmp_path / "invalid-semantics.macroflow"
    save_flow(_inline_flow(), str(target))
    raw = json.loads(target.read_text(encoding="utf-8"))
    raw["nodes"]["end_success"]["status"] = "unknown"
    target.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="정규 형식"):
        load_flow(str(target), strict=True)

    save_flow(_inline_flow(), str(target))
    raw = json.loads(target.read_text(encoding="utf-8"))
    raw["nodes"]["inline_000"]["events"][1]["timestamp_ns"] = 0
    target.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError, match="정규 형식"):
        load_flow(str(target), strict=True)


def test_flow_save_rejects_non_finite_json_numbers(tmp_path: Path) -> None:
    flow = _inline_flow()
    inline = flow.nodes["inline_000"]
    assert isinstance(inline, InlineEventsNode)
    mouse = inline.events[1]
    assert isinstance(mouse, MouseButtonEvent)
    mouse.x_ratio = float("inf")

    with pytest.raises(ValueError, match="Out of range float"):
        save_flow(flow, str(tmp_path / "non-finite.macroflow"))


def test_legacy_macro_json_loader_keeps_permissive_settings_defaults(tmp_path: Path) -> None:
    from macroflow.macro_file import load as load_macro

    target = tmp_path / "legacy.json"
    target.write_text(
        json.dumps(
            {
                "meta": {
                    "version": "1.0",
                    "app_version": "0.9",
                    "created_at": "2024-01-01T00:00:00",
                    "screen_width": 1920,
                    "screen_height": 1080,
                    "dpi_scale": 1.0,
                },
                "settings": {"click_dist_threshold_px": 9},
                "raw_events": [],
                "events": [],
                "is_edited": False,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    macro = load_macro(str(target))

    assert macro.settings.click_dist_threshold_px == 9
    assert macro.settings.color_trigger_default_timeout_ms == 10_000


def _text_macro(text: str) -> MacroData:
    event = TextInputEvent(
        id=f"text-{text}",
        type="text_input",
        timestamp_ns=0,
        text=text,
    )
    return MacroData(
        meta=MacroMeta(
            version="1.0",
            app_version="1.3.1",
            created_at="2026-07-24T00:00:00",
            screen_width=1920,
            screen_height=1080,
            dpi_scale=1.0,
        ),
        settings=MacroSettings(),
        raw_events=[event],
        events=[event],
    )


def test_flow_executes_macro_inline_macro_through_same_player_adapter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import player

    save_macro(_text_macro("A"), str(tmp_path / "a.json"))
    save_macro(_text_macro("B"), str(tmp_path / "b.json"))
    inline_settings = MacroSettings(click_dist_threshold_px=19)
    flow = MacroFlow(
        version="1.1",
        name="ordered",
        created_at="2026-07-24T00:00:00",
        start_node_id="macro_000",
        nodes={
            "macro_000": MacroNode(
                id="macro_000",
                label="A",
                macro_path="a.json",
                next_on_success="inline_001",
                next_on_failure="end_error",
            ),
            "inline_001": InlineEventsNode(
                id="inline_001",
                label="INLINE",
                events=[
                    TextInputEvent(
                        id="inline-text",
                        type="text_input",
                        timestamp_ns=0,
                        text="INLINE",
                    )
                ],
                playback_settings=inline_settings,
                next_on_success="macro_002",
                next_on_failure="end_error",
            ),
            "macro_002": MacroNode(
                id="macro_002",
                label="B",
                macro_path="b.json",
                next_on_success="end_success",
                next_on_failure="end_error",
            ),
            "end_success": EndNode(id="end_success", label="done"),
            "end_error": EndNode(id="end_error", label="error", status="error"),
        },
    )
    played: list[tuple[str, MacroSettings]] = []
    completed: list[str] = []

    def fake_play(
        macro: MacroData,
        *,
        speed: float,
        on_complete: object,
        on_error: object,
    ) -> None:
        del speed, on_error
        event = macro.events[0]
        assert isinstance(event, TextInputEvent)
        played.append((event.text, macro.settings))
        assert callable(on_complete)
        on_complete()

    monkeypatch.setattr(player, "play", fake_play)
    engine = FlowEngine(
        str(tmp_path / "ordered.macroflow"),
        on_complete=completed.append,
    )

    engine._run(flow)

    assert [text for text, _settings in played] == ["A", "INLINE", "B"]
    assert played[1][1] == inline_settings
    assert completed == ["success"]


def test_inline_player_failure_without_failure_edge_is_terminal_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from macroflow import player

    node = InlineEventsNode(
        id="inline",
        label="fail",
        events=[
            TextInputEvent(
                id="text",
                type="text_input",
                timestamp_ns=0,
                text="FAIL",
            )
        ],
        playback_settings=MacroSettings(),
        next_on_success="end_success",
        next_on_failure=None,
    )
    flow = MacroFlow(
        version="1.1",
        name="failure",
        created_at="2026-07-24T00:00:00",
        start_node_id="inline",
        nodes={
            "inline": node,
            "end_success": EndNode(id="end_success", label="done"),
        },
    )
    node_done: list[tuple[str, bool, str]] = []
    completed: list[str] = []
    errors: list[str] = []

    def fail_play(
        _macro: MacroData,
        *,
        speed: float,
        on_complete: object,
        on_error: object,
    ) -> None:
        del speed, on_complete
        assert callable(on_error)
        on_error(RuntimeError("input failed"))

    monkeypatch.setattr(player, "play", fail_play)
    engine = FlowEngine(
        str(tmp_path / "failure.macroflow"),
        on_node_done=lambda *args: node_done.append(args),
        on_complete=completed.append,
        on_error=errors.append,
    )

    engine._run(flow)

    assert node_done == [("inline", False, "input failed")]
    assert completed == []
    assert errors == ["input failed"]
