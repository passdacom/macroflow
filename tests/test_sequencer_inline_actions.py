"""Headless contracts for heterogeneous sequencer steps."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap


def _run_qt(script: str) -> None:
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    completed = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        env=env,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_mixed_steps_save_load_duplicate_paths_and_preflight() -> None:
    _run_qt(
        """
        import tempfile
        from pathlib import Path

        from PyQt6.QtWidgets import QApplication

        from macroflow.macro_file import save as save_macro
        from macroflow.script_engine import load_flow
        from macroflow.sequence_model import InlineActionItem, MacroFileItem, WaitItem
        from macroflow.types import MacroData, MacroMeta, MacroSettings, TextInputEvent
        from macroflow.ui.sequencer import MacroSequencerWidget

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event = TextInputEvent(id="a", type="text_input", timestamp_ns=0, text="A")
            macro = MacroData(
                meta=MacroMeta(
                    version="1.0", app_version="1.3.1",
                    created_at="2026-07-24T00:00:00",
                    screen_width=1920, screen_height=1080, dpi_scale=1.0,
                ),
                settings=MacroSettings(), raw_events=[event], events=[event],
            )
            macro_path = root / "same.json"
            save_macro(macro, str(macro_path))

            widget = MacroSequencerWidget()
            widget.add_macro_file(macro_path)
            widget.add_text_action("HELLO")
            widget.add_click_action(0.25, 0.75, button="right", is_double=True)
            widget.add_color_wait_action(0.4, 0.6, "#AABBCC", timeout_ms=5000)
            widget.add_wait_action(750)
            widget.add_macro_file(macro_path)

            assert widget.item_count() == 6
            assert isinstance(widget._items[0], MacroFileItem)
            assert isinstance(widget._items[1], InlineActionItem)
            assert isinstance(widget._items[4], WaitItem)
            assert isinstance(widget._items[5], MacroFileItem)
            assert widget.preflight_errors() == []
            assert not widget._act_merge.isEnabled()
            assert "혼합" in widget._act_merge.toolTip()

            flow_path = root / "mixed.macroflow"
            assert widget._do_save_flow(flow_path)
            flow = load_flow(str(flow_path), strict=True)
            assert flow.version == "1.1"

            loaded = MacroSequencerWidget()
            assert loaded._load_flow_from_path(flow_path)
            assert loaded.item_count() == 6
            assert [item.step_id for item in loaded._items] == [
                item.step_id for item in widget._items
            ]
            loaded.close()

            macro_path.unlink()
            errors = widget.preflight_errors()
            assert len(errors) == 2
            assert all("파일" in error for error in errors)
            widget.close()
        app.processEvents()
        """
    )


def test_step_reorder_uses_step_id_not_duplicate_path() -> None:
    _run_qt(
        """
        import tempfile
        from pathlib import Path

        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QApplication

        from macroflow.ui.sequencer import MacroSequencerWidget

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "same.json"
            path.write_text("{}", encoding="utf-8")
            widget = MacroSequencerWidget()
            widget.add_macro_file(path)
            widget.add_macro_file(path)
            first_id, second_id = [item.step_id for item in widget._items]

            first_row = widget._list.takeItem(0)
            assert first_row is not None
            widget._list.insertItem(1, first_row)
            widget._sync_items_from_list()

            assert [item.step_id for item in widget._items] == [second_id, first_id]
            assert all(
                widget._list.item(index).data(Qt.ItemDataRole.UserRole)
                == widget._items[index].step_id
                for index in range(widget._list.count())
            )
            widget.close()
        app.processEvents()
        """
    )


def test_f6_capture_creates_actions_and_duplicate_gets_new_identity() -> None:
    _run_qt(
        """
        from PyQt6.QtWidgets import QApplication

        from macroflow.sequence_model import InlineActionItem
        from macroflow.types import ColorTriggerEvent, MouseButtonEvent
        from macroflow.ui.sequencer import MacroSequencerWidget

        app = QApplication.instance() or QApplication([])
        widget = MacroSequencerWidget()
        started = []
        ended = []
        widget.f6_capture_started.connect(lambda: started.append(True))
        widget.f6_capture_ended.connect(lambda: ended.append(True))

        widget.start_click_capture(button="left", is_double=False)
        assert widget.is_f6_capture_active()
        assert widget.consume_f6_capture(0.2, 0.3, "#112233")
        assert not widget.is_f6_capture_active()
        assert len(widget._items) == 1
        click = widget._items[0]
        assert isinstance(click, InlineActionItem)
        assert all(isinstance(event, MouseButtonEvent) for event in click.events)
        assert click.events[0].timestamp_ns == 0
        click.playback_settings.default_playback_speed = 2.0
        click_id = click.step_id
        widget.add_click_action(0.6, 0.7, _replace_row=0)
        replaced = widget._items[0]
        assert isinstance(replaced, InlineActionItem)
        assert replaced.step_id == click_id
        assert replaced.playback_settings.default_playback_speed == 2.0

        widget.start_color_wait_capture(timeout_ms=2500)
        assert widget.consume_f6_capture(0.4, 0.5, "#AABBCC")
        color = widget._items[1]
        assert isinstance(color, InlineActionItem)
        assert isinstance(color.events[0], ColorTriggerEvent)
        assert color.events[0].on_timeout == "error"

        widget._engine = object()
        widget.start_click_capture(button="left", is_double=False)
        assert widget.consume_f6_capture(0.9, 0.9, "#FFFFFF")
        assert len(widget._items) == 2
        widget._engine = None

        widget._list.setCurrentRow(1)
        original_id = color.step_id
        widget._duplicate_selected()
        assert len(widget._items) == 3
        assert widget._items[2].step_id != original_id
        assert widget._items[2].events == color.events
        assert started == [True, True, True]
        assert ended == [True, True, True]
        assert widget._act_add.text() == "➕ 매크로"
        widget.close()
        app.processEvents()
        """
    )


def test_main_window_routes_f6_to_sequencer_capture_owner() -> None:
    from pathlib import Path

    source = Path("src/macroflow/ui/main_window.py").read_text(encoding="utf-8")

    assert "self._sequencer.is_f6_capture_active()" in source
    assert "self._sequencer.consume_f6_capture" in source
    assert 'action_id == "runtime.record_or_capture"' in source
    assert "self._handle_f6()" in source
    native_start = source.index("def nativeEvent")
    native_end = source.index("# ── 탭 관리", native_start)
    assert "self._hotkey_runtime.dispatch_native(registration_id)" in source[native_start:native_end]
    handle_start = source.index("def _handle_f6")
    handle_end = source.index("def nativeEvent", handle_start)
    handle_source = source[handle_start:handle_end]
    assert handle_source.index('self._state in {"recording", "stopping"}') < handle_source.index(
        "is_f6_capture_active()"
    )


def test_preflight_failure_and_running_edit_locks_are_truthful() -> None:
    _run_qt(
        """
        from pathlib import Path

        from PyQt6.QtWidgets import QApplication, QMessageBox

        from macroflow.sequence_model import MacroFileItem, WaitItem
        from macroflow.types import MacroData, MacroMeta, MacroSettings
        from macroflow.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        QMessageBox.warning = lambda *args, **kwargs: QMessageBox.StandardButton.Ok
        window = MainWindow()
        sequence = window._sequencer
        sequence._items = [
            MacroFileItem(step_id="missing", path=Path("/definitely/missing.json"))
        ]
        sequence._refresh_all()
        window._tabs.setCurrentWidget(sequence)
        window._toggle_sequencer()
        assert not sequence.is_running()
        assert "실행 중" not in window._sb_state.text()

        sequence._items = [WaitItem(step_id="wait", duration_ms=100)]
        sequence._refresh_all()
        sequence._engine = object()
        sequence._edit_inline_item(0)
        assert sequence._items[0].duration_ms == 100

        window._macro = MacroData(
            meta=MacroMeta(
                version="1.0", app_version="1.4.0",
                created_at="2026-07-24T00:00:00",
                screen_width=1920, screen_height=1080, dpi_scale=1.0,
            ),
            settings=MacroSettings(), raw_events=[], events=[],
        )
        window._update_toolbar()
        assert not window._act_open.isEnabled()
        assert not window._act_save.isEnabled()
        assert not window._act_save_as.isEnabled()
        sequence._engine = None
        window.close()
        app.processEvents()
        """
    )


def test_modal_reentry_cannot_commit_sequence_or_file_mutations() -> None:
    _run_qt(
        """
        from pathlib import Path
        from unittest.mock import patch

        from PyQt6.QtWidgets import QApplication, QFileDialog, QInputDialog, QMessageBox

        from macroflow.sequence_model import WaitItem
        from macroflow.types import MacroData, MacroMeta, MacroSettings
        from macroflow.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        window = MainWindow()
        sequence = window._sequencer
        sequence._items = [WaitItem(step_id="wait", duration_ms=100)]
        sequence._refresh_all()

        def start_during_edit(*args, **kwargs):
            sequence._engine = object()
            return 250, True

        with patch.object(QInputDialog, "getInt", side_effect=start_during_edit):
            sequence._engine = None
            sequence._edit_inline_item(0)
        assert sequence._items[0].duration_ms == 100

        target = Path("/tmp/modal-race.macroflow")
        sequence._current_flow_path = target

        def start_during_save(*args, **kwargs):
            sequence._engine = object()
            return QMessageBox.StandardButton.Yes

        with (
            patch.object(QMessageBox, "question", side_effect=start_during_save),
            patch("macroflow.ui.sequencer.save_flow") as save_mock,
        ):
            sequence._engine = None
            assert sequence._save_flow() is False
            save_mock.assert_not_called()

        sequence._engine = None
        with patch.object(
            sequence,
            "confirm_discard_changes",
            side_effect=lambda: setattr(sequence, "_engine", object()) or True,
        ), patch("macroflow.ui.sequencer.load_flow") as load_mock:
            assert sequence._load_flow_from_path(target) is False
            load_mock.assert_not_called()

        window._macro = MacroData(
            meta=MacroMeta(
                version="1.0", app_version="1.4.0",
                created_at="2026-07-24T00:00:00",
                screen_width=1920, screen_height=1080, dpi_scale=1.0,
            ),
            settings=MacroSettings(), raw_events=[], events=[],
        )
        initial_title = window.windowTitle()

        def start_during_save_as(*args, **kwargs):
            sequence._engine = object()
            return "/tmp/modal-race.json", "Macro JSON (*.json)"

        sequence._engine = None
        with patch.object(QFileDialog, "getSaveFileName", side_effect=start_during_save_as):
            window._save_file_as()
        assert window._current_file is None
        assert window.windowTitle() == initial_title

        sequence._engine = None
        window.close()
        app.processEvents()
        """
    )
