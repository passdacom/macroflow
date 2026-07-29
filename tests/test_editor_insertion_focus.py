"""Real-Qt regressions for focusing newly inserted editor actions."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap


def _run_offscreen(script: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["PYTHONUTF8"] = "1"
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_inserted_editor_row_becomes_selection_focus_and_next_anchor() -> None:
    result = _run_offscreen(
        """
        from PyQt6.QtWidgets import QApplication

        from macroflow.event_insertions import _insert_text_input_event
        from macroflow.types import MacroData, MacroMeta, MacroSettings, WaitEvent
        from macroflow.ui.editor import EventEditorWidget

        app = QApplication.instance() or QApplication([])
        events = [
            WaitEvent(id=f"wait-{index}", type="wait", timestamp_ns=(index + 1) * 1_000_000_000, duration_ms=10)
            for index in range(3)
        ]
        macro = MacroData(
            meta=MacroMeta(
                version="1.0", app_version="test", created_at="2026-07-28T00:00:00",
                screen_width=1920, screen_height=1080, dpi_scale=1.0,
            ),
            settings=MacroSettings(), raw_events=[], events=events,
        )
        widget = EventEditorWidget()
        widget.load_macro(macro)
        widget.show()
        widget._table.selectRow(1)
        app.processEvents()

        first = _insert_text_input_event(
            macro.events,
            insert_after_event_idx=widget._selected_insert_after_event_idx(),
            text="first",
            delay_ms=0,
            id_factory=lambda: "insert-first",
        )
        widget._apply_inserted_events(first, previous_event_ids={event.id for event in macro.events})
        app.processEvents()
        assert widget._table.currentRow() == 2
        assert [index.row() for index in widget._table.selectionModel().selectedRows()] == [2]
        assert widget._table.hasFocus()
        assert widget._selected_insert_after_event_idx() == 2

        previous = widget.current_macro()
        assert previous is not None
        second = _insert_text_input_event(
            previous.events,
            insert_after_event_idx=widget._selected_insert_after_event_idx(),
            text="second",
            delay_ms=0,
            id_factory=lambda: "insert-second",
        )
        widget._apply_inserted_events(
            second,
            previous_event_ids={event.id for event in previous.events},
        )
        app.processEvents()
        assert widget._table.currentRow() == 3
        assert widget._rows[3].primary_event_id == "insert-second"
        widget.close()
        """
    )

    assert result.returncode == 0, result.stderr


def test_async_color_insert_aborts_if_editor_model_changed_during_capture() -> None:
    result = _run_offscreen(
        """
        from unittest.mock import patch

        from PyQt6.QtWidgets import QApplication

        from macroflow.types import MacroData, MacroMeta, MacroSettings, WaitEvent
        from macroflow.ui.editor import EventEditorWidget

        app = QApplication.instance() or QApplication([])
        macro = MacroData(
            meta=MacroMeta(
                version="1.0", app_version="test", created_at="2026-07-28T00:00:00",
                screen_width=1920, screen_height=1080, dpi_scale=1.0,
            ),
            settings=MacroSettings(), raw_events=[],
            events=[WaitEvent(id="anchor", type="wait", timestamp_ns=1_000_000_000, duration_ms=10)],
        )
        widget = EventEditorWidget()
        widget.load_macro(macro)
        widget._table.selectRow(0)
        callbacks = []
        widget._start_f6_capture = lambda callback, **_kwargs: callbacks.append(callback)
        widget._start_color_trigger_insert()
        assert len(callbacks) == 1

        widget._apply_events([
            WaitEvent(id="replacement", type="wait", timestamp_ns=2_000_000_000, duration_ms=20)
        ])
        with patch("macroflow.ui.editor.QMessageBox.warning") as warning:
            callbacks[0](0.25, 0.75, "#112233")

        current = widget.current_macro()
        assert current is not None
        assert [event.id for event in current.events] == ["replacement"]
        warning.assert_called_once()
        assert "캡처 중 매크로가 변경" in warning.call_args.args[2]
        widget.close()
        """
    )

    assert result.returncode == 0, result.stderr
