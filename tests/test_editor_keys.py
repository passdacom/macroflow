"""Editor key-name to VK-code mapping tests."""

from __future__ import annotations

import subprocess
import sys

from macroflow.ui.editor_keys import key_name_to_vk


def test_editor_keys_import_does_not_eagerly_import_pyqt_widgets() -> None:
    """키 매핑 helper는 Qt 런타임 없이 독립 import 가능해야 한다."""
    code = "import sys; from macroflow.ui.editor_keys import key_name_to_vk; print(key_name_to_vk('enter', 0)); print('PyQt6' in sys.modules)"
    result = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    assert result.stdout.splitlines() == ["13", "False"]


def test_key_name_to_vk_maps_standard_names_and_aliases() -> None:
    assert key_name_to_vk("enter", 0) == 0x0D
    assert key_name_to_vk("return", 0) == 0x0D
    assert key_name_to_vk("A", 0) == 0x41
    assert key_name_to_vk("f12", 0) == 0x7B
    assert key_name_to_vk("period", 0) == 0xBE
    assert key_name_to_vk("numpad9", 0) == 0x69


def test_key_name_to_vk_returns_fallback_for_unknown_name() -> None:
    assert key_name_to_vk("unknown-custom-key", 0x99) == 0x99
