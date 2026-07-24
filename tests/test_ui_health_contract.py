"""UI 문구/확인창 계약 테스트."""

from __future__ import annotations

import ast
from pathlib import Path

_SOURCE = Path("src/macroflow/ui/main_window.py").read_text(encoding="utf-8")
_EDITOR_SOURCE = Path("src/macroflow/ui/editor.py").read_text(encoding="utf-8")


def test_play_toolbar_uses_stop_copy_while_playing() -> None:
    """일반 매크로 재생 중 F7 버튼은 실제 동작에 맞게 stop 의미를 보여야 한다."""
    start = _SOURCE.index("def _update_toolbar")
    end = _SOURCE.index("def _update_range_spinboxes", start)
    method_src = _SOURCE[start:end]

    assert '"⏹ 중지 (F7)" if is_play else "▶ 재생 (F7)"' in method_src
    assert '"▶ 계속 (F8)" if self._paused else "⏸ 일시중지 (F8)"' in method_src


def test_main_window_registers_f8_pause_hotkey_and_routes_it() -> None:
    assert "_HOTKEY_PAUSE = 3" in _SOURCE
    assert "_VK_F8 = 0x77" in _SOURCE
    assert "RegisterHotKey(hwnd, _HOTKEY_PAUSE, 0, _VK_F8)" in _SOURCE
    assert "UnregisterHotKey(hwnd, _HOTKEY_PAUSE)" in _SOURCE
    assert "if msg.wParam == _HOTKEY_PAUSE:" in _SOURCE
    assert "self._toggle_pause()" in _SOURCE


def test_delete_mouse_moves_requires_confirmation_dialog() -> None:
    """mouse_move 영구 삭제는 확인창을 거쳐야 한다."""
    module = ast.parse(_EDITOR_SOURCE)
    for node in module.body:
        if isinstance(node, ast.ClassDef) and node.name == "EventEditorWidget":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "_delete_mouse_moves":
                    question_calls = [
                        call
                        for call in ast.walk(item)
                        if isinstance(call, ast.Call)
                        and ast.unparse(call.func) == "QMessageBox.question"
                    ]
                    assert question_calls, "QMessageBox.question call missing"
                    question_call = question_calls[0]
                    assert any("Ctrl+Z" in ast.unparse(arg) for arg in question_call.args)
                    return
    raise AssertionError("EventEditorWidget._delete_mouse_moves not found")
