"""Real-Qt contracts for interactive editor column redistribution."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap


def test_all_editor_columns_resize_without_horizontal_scrolling() -> None:
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            textwrap.dedent(
                """
                from PyQt6.QtCore import Qt
                from PyQt6.QtWidgets import QApplication, QHeaderView
                from macroflow.types import MacroData, MacroMeta, MacroSettings, TextInputEvent
                from macroflow.ui.editor import EventEditorWidget

                app = QApplication.instance() or QApplication([])
                editor = EventEditorWidget()
                editor.resize(900, 500)
                editor.load_macro(MacroData(
                    meta=MacroMeta(
                        version="1.0", app_version="test", created_at="2026-07-29T00:00:00",
                        screen_width=1920, screen_height=1080, dpi_scale=1.0,
                    ),
                    settings=MacroSettings(),
                    raw_events=[],
                    events=[TextInputEvent(
                        id="text", type="text_input", timestamp_ns=0,
                        text="a sufficiently long content value", remark="remark",
                        source_file="source.json",
                    )],
                ))
                editor.show()
                app.processEvents()

                table = editor._table
                header = table.horizontalHeader()
                assert all(
                    header.sectionResizeMode(column) == QHeaderView.ResizeMode.Interactive
                    for column in range(table.columnCount())
                )
                before = [table.columnWidth(column) for column in range(table.columnCount())]
                header.resizeSection(3, before[3] + 80)
                app.processEvents()
                after = [table.columnWidth(column) for column in range(table.columnCount())]

                assert after[3] > before[3], (before, after)
                assert any(
                    after[column] < before[column]
                    for column in range(table.columnCount())
                    if column != 3
                ), (before, after)
                assert sum(after) <= table.viewport().width(), (after, table.viewport().width())
                assert table.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff

                editor._on_relative_time_toggled(True)
                app.processEvents()
                assert [table.columnWidth(column) for column in range(table.columnCount())] == after

                for width in (1100, 760):
                    editor.resize(width, 500)
                    app.processEvents()
                    current = [table.columnWidth(column) for column in range(table.columnCount())]
                    assert sum(current) <= table.viewport().width(), (current, table.viewport().width())
                    assert table.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
                editor.close()
                """
            ),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    assert result.returncode == 0, result.stderr
