"""MacroFlow UI 레이어 — PyQt6 기반 사용자 인터페이스.

패키지 import 시점에는 PyQt 위젯 모듈을 eager import하지 않는다. 이렇게 해야
`macroflow.ui.editor_rows` 같은 순수 helper 모듈을 headless CI에서도 안전하게
import할 수 있다.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .main_window import MainWindow
    from .sequencer import MacroSequencerWidget

__all__ = ["MainWindow", "MacroSequencerWidget"]


def __getattr__(name: str) -> Any:
    if name == "MainWindow":
        from .main_window import MainWindow

        return MainWindow
    if name == "MacroSequencerWidget":
        from .sequencer import MacroSequencerWidget

        return MacroSequencerWidget
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
