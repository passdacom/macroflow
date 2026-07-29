"""Qt QShortcut adapter used by the configurable hotkey runtime."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from functools import partial

from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QWidget


class QtFocusedHotkeyBindings:
    """Own replaceable app-focused shortcuts without leaving stale bindings."""

    def __init__(self, parent: QWidget) -> None:
        self._parent = parent
        self._shortcuts: list[QShortcut] = []

    def replace(
        self,
        bindings: Mapping[str, str],
        callback: Callable[[str], None],
    ) -> None:
        self.clear()
        for action_id, key in bindings.items():
            shortcut = QShortcut(QKeySequence(key), self._parent)
            shortcut.activated.connect(partial(callback, action_id))
            self._shortcuts.append(shortcut)

    def clear(self) -> None:
        for shortcut in self._shortcuts:
            shortcut.setEnabled(False)
            shortcut.deleteLater()
        self._shortcuts.clear()

    @property
    def count(self) -> int:
        return len(self._shortcuts)
