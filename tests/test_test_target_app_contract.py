"""Contract tests for the MacroFlow RDP test target app."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "test_target_app.py"


def _load_target_app():
    spec = importlib.util.spec_from_file_location("test_target_app", _SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_initial_status_contract_contains_stable_target_fields(tmp_path: Path):
    target = _load_target_app()
    status_path = tmp_path / "target_status.json"
    events_path = tmp_path / "target_events.jsonl"

    status = target.initial_status(
        scenario="basic",
        status_path=status_path,
        events_path=events_path,
        color_hex="#22aa55",
    )

    assert status["scenario"] == "basic"
    assert status["ready"] is False
    assert status["button_clicks"] == 0
    assert status["text_value"] == ""
    assert status["color_clicks"] == 0
    assert status["drag_count"] == 0
    assert status["wheel_delta"] == 0
    assert status["color_hex"] == "#22AA55"
    assert status["status_path"] == str(status_path)
    assert status["events_path"] == str(events_path)
    assert status["coords"] == {}


def test_assertions_require_click_text_color_drag_and_wheel():
    target = _load_target_app()
    status = {
        "button_clicks": 1,
        "text_value": "rdp-ok",
        "color_clicks": 1,
        "drag_count": 1,
        "wheel_delta": -120,
    }

    assertions = target.build_assertions(status, expected_text="rdp-ok")

    assert assertions == {
        "button_clicked": True,
        "text_input_ok": True,
        "color_clicked": True,
        "drag_seen": True,
        "wheel_seen": True,
    }
    assert target.is_success(assertions) is True


def test_write_status_and_event_log_are_structured_json(tmp_path: Path):
    target = _load_target_app()
    status_path = tmp_path / "target_status.json"
    events_path = tmp_path / "target_events.jsonl"
    status = target.initial_status(
        scenario="basic",
        status_path=status_path,
        events_path=events_path,
        color_hex="#22AA55",
    )

    target.write_status(status_path, status)
    target.append_event(events_path, "ready", coords={"button": [10, 20]})

    assert json.loads(status_path.read_text(encoding="utf-8"))["scenario"] == "basic"
    event = json.loads(events_path.read_text(encoding="utf-8").strip())
    assert event["kind"] == "ready"
    assert event["coords"] == {"button": [10, 20]}
