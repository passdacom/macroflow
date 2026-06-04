"""MainWindow 이어서 녹화 확인창 계약 테스트."""

from __future__ import annotations

import ast
from pathlib import Path


def _question_calls_in_start_append_recording() -> list[ast.Call]:
    source = Path("src/macroflow/ui/main_window.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == "MainWindow":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "_start_append_recording":
                    return [
                        call
                        for call in ast.walk(item)
                        if isinstance(call, ast.Call)
                        and ast.unparse(call.func) == "QMessageBox.question"
                    ]
    raise AssertionError("MainWindow._start_append_recording not found")


def test_append_recording_confirmation_defaults_to_yes_for_spacebar() -> None:
    """이어서 녹화 확인창은 Space만 눌러도 진행되도록 Yes를 기본 버튼으로 둔다."""
    calls = _question_calls_in_start_append_recording()

    assert len(calls) == 1
    question_call = calls[0]
    assert len(question_call.args) >= 5
    assert ast.unparse(question_call.args[4]) == "QMessageBox.StandardButton.Yes"
