"""Sequencer save/load/merge smoke for Windows RDP or local offscreen runs.

This is a small integration harness, not a pytest test. It exercises the real
MacroSequencerWidget flow persistence and merge path using a hidden QApplication,
then writes a structured JSON report.
"""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from macroflow.macro_file import save
from macroflow.types import KeyEvent, MacroData, MacroMeta, MacroSettings, MouseMoveEvent
from macroflow.ui.sequencer import MacroSequencerWidget


def _meta() -> MacroMeta:
    return MacroMeta(
        version="1.0",
        app_version="sequencer-smoke",
        created_at="2026-06-22T00:00:00",
        screen_width=1920,
        screen_height=1080,
        dpi_scale=1.0,
        description="sequencer save/load/merge smoke",
    )


def _macro(*events: KeyEvent | MouseMoveEvent) -> MacroData:
    return MacroData(
        meta=_meta(),
        settings=MacroSettings(),
        raw_events=list(events),
        events=list(events),
        is_edited=False,
    )


def _key(event_id: str, timestamp_ns: int, key: str, vk_code: int) -> KeyEvent:
    return KeyEvent(
        id=event_id,
        type="key_down",
        timestamp_ns=timestamp_ns,
        key=key,
        vk_code=vk_code,
    )


def _move(event_id: str, timestamp_ns: int, x_ratio: float, y_ratio: float) -> MouseMoveEvent:
    return MouseMoveEvent(
        id=event_id,
        type="mouse_move",
        timestamp_ns=timestamp_ns,
        x_ratio=x_ratio,
        y_ratio=y_ratio,
    )


def _rewrite_flow_with_dot_segments(flow_path: Path) -> dict[str, object]:
    payload = json.loads(flow_path.read_text(encoding="utf-8"))
    touched: list[dict[str, str]] = []
    for node in payload.get("nodes", {}).values():
        if node.get("type") != "macro":
            continue
        macro_path = node.get("macro_path", "")
        if macro_path == "macros/first.json":
            node["macro_path"] = "./macros/../macros/first.json"
        elif macro_path == "macros/second.json":
            node["macro_path"] = "macros/../macros/second.json"
        touched.append({"label": node.get("label", ""), "macro_path": node.get("macro_path", "")})
    flow_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"nodes": touched, "path": str(flow_path)}


def run_smoke(*, report_path: Path | None = None) -> dict[str, object]:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    with tempfile.TemporaryDirectory(prefix="macroflow-sequencer-smoke-") as td:
        base = Path(td)
        macros_dir = base / "macros"
        macros_dir.mkdir()

        first_path = macros_dir / "first.json"
        second_path = macros_dir / "second.json"
        flow_path = base / "sequence.macroflow"

        save(_macro(_key("old", 100_000_000, "a", 0x41), _move("move", 400_000_000, 0.25, 0.50)), str(first_path))
        save(_macro(_key("new", 50_000_000, "b", 0x42)), str(second_path))

        widget = MacroSequencerWidget()
        widget._gap_spin.setValue(250)
        merged_payload: dict[str, object] = {}

        def _capture_merged(macro: MacroData) -> None:
            merged_payload["event_ids"] = [event.id for event in macro.events]
            merged_payload["source_files"] = [event.source_file for event in macro.events]
            merged_payload["timestamps"] = [event.timestamp_ns for event in macro.events]
            merged_payload["event_types"] = [event.type for event in macro.events]

        widget.merge_to_editor.connect(_capture_merged)
        widget.add_macro_file(first_path)
        widget.add_macro_file(second_path)
        widget._current_flow_path = flow_path
        widget._do_save_flow(flow_path)

        initial_item_paths = [str(item.path) for item in widget._items]
        rewritten = _rewrite_flow_with_dot_segments(flow_path)
        widget._load_flow_from_path(flow_path)
        loaded_item_paths = [str(item.path) for item in widget._items]
        resolved_loaded_paths = [str(item.path.resolve(strict=False)) for item in widget._items]
        widget._merge_to_editor()

        flow_payload: dict[str, object] = json.loads(flow_path.read_text(encoding="utf-8"))
        nodes_payload = flow_payload["nodes"]
        assert isinstance(nodes_payload, dict)
        node_types = {
            node_id: node.get("type")
            for node_id, node in nodes_payload.items()
            if isinstance(node, dict)
        }

        result: dict[str, object] = {
            "ok": True,
            "platform": os.name,
            "work_dir": str(base),
            "macro_paths": [str(first_path), str(second_path)],
            "initial_item_paths": initial_item_paths,
            "rewritten_flow": rewritten,
            "loaded_item_paths": loaded_item_paths,
            "resolved_loaded_paths": resolved_loaded_paths,
            "expected_loaded_paths": [
                str(first_path.resolve(strict=False)),
                str(second_path.resolve(strict=False)),
            ],
            "flow_path": str(flow_path),
            "flow_node_types": node_types,
            "gap_ms": widget._gap_spin.value(),
            "merged": merged_payload,
            "assertions": {
                "two_items_loaded": len(widget._items) == 2,
                "normalized_paths": resolved_loaded_paths
                == [str(first_path.resolve(strict=False)), str(second_path.resolve(strict=False))],
                "wait_node_present": any(node_type == "wait_fixed" for node_type in node_types.values()),
                "merge_emitted": merged_payload.get("event_ids") == ["old", "move", "new"],
                "merge_source_files": merged_payload.get("source_files") == ["first.json", "first.json", "second.json"],
                "merge_gap_applied": merged_payload.get("timestamps") == [100_000_000, 400_000_000, 650_000_000],
                "gap_restored": widget._gap_spin.value() == 250,
            },
        }
        result["ok"] = all(result["assertions"].values())

        if report_path is not None:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

        widget.deleteLater()
        app.processEvents()
        return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run MacroFlow sequencer save/load/merge smoke")
    parser.add_argument("--report", type=Path, help="Optional JSON report output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_smoke(report_path=args.report)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
