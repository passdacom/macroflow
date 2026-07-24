"""Side-effect-free runtime smokes used by packaged Windows artifacts."""

from __future__ import annotations

import tempfile
from pathlib import Path

from macroflow.script_engine import load_flow, save_flow
from macroflow.sequence_model import (
    InlineActionItem,
    SequenceItem,
    WaitItem,
    build_sequence_flow,
    project_sequence_flow,
)
from macroflow.types import (
    ColorTriggerEvent,
    MacroSettings,
    MouseButtonEvent,
    TextInputEvent,
)


def run_inline_sequence_smoke() -> None:
    """Exercise packaged mixed-sequence imports and codecs without sending input."""
    settings = MacroSettings()
    items: list[SequenceItem] = [
        InlineActionItem(
            step_id="smoke-text",
            label="문구 입력: SMOKE",
            events=[
                TextInputEvent(
                    id="text",
                    type="text_input",
                    timestamp_ns=0,
                    text="SMOKE",
                )
            ],
            playback_settings=settings,
        ),
        InlineActionItem(
            step_id="smoke-click",
            label="좌클릭",
            events=[
                MouseButtonEvent(
                    id="down",
                    type="mouse_down",
                    timestamp_ns=0,
                    x_ratio=0.25,
                    y_ratio=0.75,
                    button="left",
                ),
                MouseButtonEvent(
                    id="up",
                    type="mouse_up",
                    timestamp_ns=100_000_000,
                    x_ratio=0.25,
                    y_ratio=0.75,
                    button="left",
                ),
            ],
            playback_settings=settings,
        ),
        InlineActionItem(
            step_id="smoke-color",
            label="색상 대기",
            events=[
                ColorTriggerEvent(
                    id="color",
                    type="color_trigger",
                    timestamp_ns=0,
                    x_ratio=0.5,
                    y_ratio=0.5,
                    target_color="#AABBCC",
                    timeout_ms=1_000,
                    check_interval_ms=50,
                    on_timeout="error",
                )
            ],
            playback_settings=settings,
        ),
        WaitItem(step_id="smoke-wait", duration_ms=10),
    ]

    with tempfile.TemporaryDirectory(prefix="macroflow-smoke-") as directory:
        flow_path = Path(directory) / "inline-smoke.macroflow"
        flow = build_sequence_flow(
            items,
            flow_path,
            created_at="2026-07-24T00:00:00",
        )
        save_flow(flow, str(flow_path))
        loaded = load_flow(str(flow_path), strict=True)
        projected = project_sequence_flow(loaded, flow_path)
        if projected != items:
            raise RuntimeError("Packaged inline sequence smoke round-trip mismatch")
