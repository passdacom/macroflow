"""MacroFlow 저장의 원자성 회귀 테스트."""

import json
from pathlib import Path
from typing import Any, TextIO

import pytest

import macroflow.script_engine as script_engine
from macroflow.script_engine import EndNode, MacroFlow, load_flow, save_flow


def _flow() -> MacroFlow:
    return MacroFlow(
        version="1.0",
        name="atomic",
        created_at="2026-07-16T00:00:00",
        start_node_id="end_success",
        nodes={
            "end_success": EndNode(
                id="end_success",
                label="done",
                status="success",
            )
        },
    )


def test_partial_serialization_failure_preserves_existing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "sequence.macroflow"
    target.write_text("ORIGINAL", encoding="utf-8")

    def partial_dump(
        _data: dict[str, Any],
        file: TextIO,
        **_kwargs: Any,
    ) -> None:
        file.write("PARTIAL")
        file.flush()
        raise OSError("simulated disk failure")

    monkeypatch.setattr(script_engine.json, "dump", partial_dump)

    with pytest.raises(OSError, match="simulated disk failure"):
        save_flow(_flow(), str(target))

    assert target.read_text(encoding="utf-8") == "ORIGINAL"
    assert not list(tmp_path.glob(f".{target.name}.*.tmp"))


def test_replace_failure_preserves_existing_file_and_cleans_temp(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "sequence.macroflow"
    target.write_text("ORIGINAL", encoding="utf-8")

    def fail_replace(_source: Path, _target: Path) -> None:
        raise PermissionError("target is locked")

    monkeypatch.setattr(script_engine.os, "replace", fail_replace)

    with pytest.raises(PermissionError, match="target is locked"):
        save_flow(_flow(), str(target))

    assert target.read_text(encoding="utf-8") == "ORIGINAL"
    assert not list(tmp_path.glob(f".{target.name}.*.tmp"))


def test_successful_save_replaces_target_and_leaves_no_temp_file(tmp_path: Path) -> None:
    target = tmp_path / "sequence.macroflow"
    target.write_text("OLD", encoding="utf-8")

    save_flow(_flow(), str(target))

    assert load_flow(str(target)) == _flow()
    assert not list(tmp_path.glob(f".{target.name}.*.tmp"))


@pytest.mark.parametrize(
    "variant",
    ["unknown_top_level", "unknown_meta", "unknown_node_field", "embedded_id_mismatch"],
)
def test_strict_load_rejects_document_fields_that_would_be_lost(
    tmp_path: Path,
    variant: str,
) -> None:
    target = tmp_path / "sequence.macroflow"
    save_flow(_flow(), str(target))
    raw = json.loads(target.read_text(encoding="utf-8"))

    if variant == "unknown_top_level":
        raw["document_metadata"] = {"owner": "operator"}
    elif variant == "unknown_meta":
        raw["meta"]["owner"] = "operator"
    elif variant == "unknown_node_field":
        raw["nodes"]["end_success"]["operator_note"] = "keep me"
    else:
        raw["nodes"]["end_success"]["id"] = "embedded-custom-id"
    target.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(ValueError, match="정규 형식"):
        load_flow(str(target), strict=True)
