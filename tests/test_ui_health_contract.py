"""UI 문구/확인창 계약 테스트."""

from __future__ import annotations

import ast
from pathlib import Path

from macroflow.hotkey_config import DEFAULT_HOTKEY_CONFIG
from macroflow.win32.hotkeys import MOD_NOREPEAT, native_hotkeys

_SOURCE = Path("src/macroflow/ui/main_window.py").read_text(encoding="utf-8")
_EDITOR_SOURCE = Path("src/macroflow/ui/editor.py").read_text(encoding="utf-8")


def test_play_toolbar_uses_stop_copy_while_playing() -> None:
    """일반 매크로 재생 중 F7 버튼은 실제 동작에 맞게 stop 의미를 보여야 한다."""
    start = _SOURCE.index("def _update_toolbar")
    end = _SOURCE.index("def _update_range_spinboxes", start)
    method_src = _SOURCE[start:end]

    assert 'f"⏹ 중지 ({play_key})" if is_play else f"▶ 재생 ({play_key})"' in method_src
    assert 'f"▶ 계속 ({pause_key})"' in method_src
    assert 'f"⏸ 일시중지 ({pause_key})"' in method_src


def test_main_window_registers_f8_pause_hotkey_and_routes_it() -> None:
    assert DEFAULT_HOTKEY_CONFIG.binding_for("runtime.pause_or_resume") == "F8"
    native = next(
        item
        for item in native_hotkeys(DEFAULT_HOTKEY_CONFIG)
        if item.action_id == "runtime.pause_or_resume"
    )
    assert native.registration_id == 3
    assert native.vk == 0x77
    assert native.modifiers == MOD_NOREPEAT
    assert 'action_id == "runtime.pause_or_resume"' in _SOURCE
    assert "self._toggle_pause()" in _SOURCE


def test_main_window_registers_f9_quick_text_hotkey_and_routes_it() -> None:
    assert DEFAULT_HOTKEY_CONFIG.binding_for("recording.quick_text") == "F9"
    native = next(
        item
        for item in native_hotkeys(DEFAULT_HOTKEY_CONFIG)
        if item.action_id == "recording.quick_text"
    )
    assert native.registration_id == 4
    assert native.vk == 0x78
    assert native.modifiers == MOD_NOREPEAT
    assert 'action_id == "recording.quick_text"' in _SOURCE
    assert "self._capture_quick_text()" in _SOURCE


def test_settings_menu_exposes_f9_text_playback_delay_default() -> None:
    assert 'QAction("F9 텍스트 재생 대기...", self)' in _SOURCE
    assert "self._act_quick_text_delay.triggered.connect(self._show_quick_text_delay_settings)" in _SOURCE
    assert "def _show_quick_text_delay_settings" in _SOURCE


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
