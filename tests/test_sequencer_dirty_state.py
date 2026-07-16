"""시퀀서 미저장 변경 보호 회귀 테스트.

기존 일부 테스트가 collection 시점에 PyQt 모듈을 대체하므로 실제 Qt 검증은
독립 subprocess에서 실행해 테스트 순서와 전역 module state의 영향을 차단한다.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap


def _run_offscreen(script: str) -> None:
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(script)],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_dirty_transitions_for_mutations_and_noops() -> None:
    _run_offscreen(
        """
        import tempfile
        from pathlib import Path

        from PyQt6.QtWidgets import QApplication
        from macroflow.ui.sequencer import MacroSequencerWidget

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.json"
            second = root / "second.json"
            first.write_text("{}", encoding="utf-8")
            second.write_text("{}", encoding="utf-8")

            widget = MacroSequencerWidget()
            assert not widget.is_dirty()

            widget.add_macro_file(first)
            assert widget.is_dirty()
            widget._set_dirty(False)
            widget.add_macro_file(first)
            assert not widget.is_dirty(), "duplicate add must be a no-op"

            widget._list.setCurrentRow(0)
            widget._remove_selected()
            assert widget.is_dirty()
            widget._set_dirty(False)
            widget._remove_selected()
            assert not widget.is_dirty(), "remove without selection must be a no-op"

            widget.add_macro_file(first)
            widget.add_macro_file(second)
            widget._set_dirty(False)
            widget._gap_spin.setValue(widget._gap_spin.value() + 1)
            assert widget.is_dirty()

            widget._set_dirty(False)
            first_row = widget._list.takeItem(0)
            assert first_row is not None
            widget._list.insertItem(1, first_row)
            widget._sync_items_from_list()
            assert widget.is_dirty()
            assert [item.path for item in widget._items] == [second, first]
            widget.close()

            left = root / "left" / "same.json"
            right = root / "right" / "same.json"
            left.parent.mkdir()
            right.parent.mkdir()
            left.write_text("{}", encoding="utf-8")
            right.write_text("{}", encoding="utf-8")
            same_name_widget = MacroSequencerWidget()
            same_name_widget.add_macro_file(left)
            same_name_widget.add_macro_file(right)
            same_name_widget._set_dirty(False)
            left_row = same_name_widget._list.takeItem(0)
            assert left_row is not None
            same_name_widget._list.insertItem(1, left_row)
            same_name_widget._sync_items_from_list()
            assert same_name_widget.is_dirty()
            assert [item.path for item in same_name_widget._items] == [right, left]
            same_name_widget.close()
        app.processEvents()
        """
    )


def test_save_load_and_save_as_failure_are_transactional() -> None:
    _run_offscreen(
        """
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
        from macroflow.ui.sequencer import MacroSequencerWidget

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            macro = root / "one.json"
            flow_path = root / "sequence.macroflow"
            macro.write_text("{}", encoding="utf-8")

            widget = MacroSequencerWidget()
            widget.add_macro_file(macro)
            assert widget._do_save_flow(flow_path)
            assert not widget.is_dirty()
            assert widget._current_flow_path == flow_path

            widget._gap_spin.setValue(widget._gap_spin.value() + 1)
            assert widget.is_dirty()
            with patch.object(widget, "confirm_discard_changes", return_value=True):
                assert widget._load_flow_from_path(flow_path)
            assert not widget.is_dirty()
            assert widget._current_flow_path == flow_path

            previous_path = root / "previous.macroflow"
            requested_path = root / "requested.macroflow"
            widget._current_flow_path = previous_path
            widget._set_dirty(True)
            with (
                patch.object(
                    QFileDialog,
                    "getSaveFileName",
                    return_value=(str(requested_path), "MacroFlow (*.macroflow)"),
                ),
                patch("macroflow.ui.sequencer.save_flow", side_effect=OSError("disk full")),
                patch.object(QMessageBox, "critical"),
            ):
                assert not widget._save_flow_as()
            assert widget.is_dirty()
            assert widget._current_flow_path == previous_path
            widget.close()
        app.processEvents()
        """
    )


def test_unsaved_prompt_and_failed_open_preserve_state() -> None:
    _run_offscreen(
        """
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock, patch

        from PyQt6.QtWidgets import QApplication, QMessageBox
        from macroflow.ui.sequencer import MacroSequencerWidget

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.json"
            second = root / "second.json"
            target = root / "target.macroflow"
            first.write_text("{}", encoding="utf-8")
            second.write_text("{}", encoding="utf-8")

            widget = MacroSequencerWidget()
            widget.add_macro_file(first)
            with patch.object(
                QMessageBox,
                "question",
                return_value=QMessageBox.StandardButton.Cancel,
            ):
                assert not widget.confirm_discard_changes()
            assert widget.is_dirty()

            with patch.object(
                QMessageBox,
                "question",
                return_value=QMessageBox.StandardButton.Discard,
            ):
                assert widget.confirm_discard_changes()
            assert widget.is_dirty(), "discard applies only when the operation proceeds"

            widget._current_flow_path = target
            with patch.object(
                QMessageBox,
                "question",
                return_value=QMessageBox.StandardButton.Save,
            ):
                assert widget.confirm_discard_changes()
            assert target.exists()
            assert not widget.is_dirty()

            widget._gap_spin.setValue(widget._gap_spin.value() + 1)
            with (
                patch.object(
                    QMessageBox,
                    "question",
                    return_value=QMessageBox.StandardButton.Save,
                ),
                patch("macroflow.ui.sequencer.save_flow", side_effect=OSError("disk full")),
                patch.object(QMessageBox, "critical"),
            ):
                assert not widget.confirm_discard_changes()
            assert widget.is_dirty()

            load_mock = Mock()
            with (
                patch.object(widget, "confirm_discard_changes", return_value=False),
                patch("macroflow.ui.sequencer.load_flow", load_mock),
            ):
                assert not widget._load_flow_from_path(target)
            assert [item.path for item in widget._items] == [first]
            load_mock.assert_not_called()

            widget.add_macro_file(second)
            with (
                patch.object(widget, "confirm_discard_changes", return_value=True),
                patch(
                    "macroflow.ui.sequencer._project_linear_flow",
                    side_effect=ValueError("unsupported flow"),
                ),
                patch.object(QMessageBox, "critical"),
            ):
                assert not widget._load_flow_from_path(target)
            assert [item.path for item in widget._items] == [first, second]
            assert widget.is_dirty()
            widget.close()
        app.processEvents()
        """
    )


def test_lossy_flow_projection_is_rejected() -> None:
    _run_offscreen(
        """
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        from PyQt6.QtWidgets import QApplication, QMessageBox
        from macroflow.script_engine import (
            ColorCheckNode,
            EndNode,
            MacroFlow,
            MacroNode,
            WaitFixedNode,
            save_flow,
        )
        from macroflow.ui.sequencer import MacroSequencerWidget

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.json"
            second = root / "second.json"
            third = root / "third.json"
            for macro in (first, second, third):
                macro.write_text("{}", encoding="utf-8")

            end_success = EndNode(id="end_success", label="done", status="success")
            end_error = EndNode(id="end_error", label="error", status="error")
            branch_flow = MacroFlow(
                version="1.0",
                name="branch",
                created_at="2026-07-16T00:00:00",
                start_node_id="macro_000",
                nodes={
                    "macro_000": MacroNode(
                        id="macro_000",
                        label="first",
                        macro_path=first.name,
                        next_on_success="color_000",
                        next_on_failure="end_error",
                    ),
                    "color_000": ColorCheckNode(
                        id="color_000",
                        label="branch",
                        x_ratio=0.5,
                        y_ratio=0.5,
                        target_color="#FFFFFF",
                        on_match="macro_001",
                        on_timeout="end_error",
                    ),
                    "macro_001": MacroNode(
                        id="macro_001",
                        label="second",
                        macro_path=second.name,
                        next_on_success="end_success",
                        next_on_failure="end_error",
                    ),
                    "end_success": end_success,
                    "end_error": end_error,
                },
            )
            branch_path = root / "branch.macroflow"
            save_flow(branch_flow, str(branch_path))

            uneven_flow = MacroFlow(
                version="1.0",
                name="uneven",
                created_at="2026-07-16T00:00:00",
                start_node_id="macro_000",
                nodes={
                    "macro_000": MacroNode(
                        id="macro_000",
                        label="first",
                        macro_path=first.name,
                        next_on_success="wait_000",
                        next_on_failure="end_error",
                    ),
                    "wait_000": WaitFixedNode(
                        id="wait_000",
                        label="100ms",
                        duration_ms=100,
                        next="macro_001",
                    ),
                    "macro_001": MacroNode(
                        id="macro_001",
                        label="second",
                        macro_path=second.name,
                        next_on_success="wait_001",
                        next_on_failure="end_error",
                    ),
                    "wait_001": WaitFixedNode(
                        id="wait_001",
                        label="200ms",
                        duration_ms=200,
                        next="macro_002",
                    ),
                    "macro_002": MacroNode(
                        id="macro_002",
                        label="third",
                        macro_path=third.name,
                        next_on_success="end_success",
                        next_on_failure="end_error",
                    ),
                    "end_success": end_success,
                    "end_error": end_error,
                },
            )
            uneven_path = root / "uneven.macroflow"
            save_flow(uneven_flow, str(uneven_path))

            oversized_gap_flow = MacroFlow(
                version="1.0",
                name="oversized-gap",
                created_at="2026-07-16T00:00:00",
                start_node_id="macro_000",
                nodes={
                    "macro_000": MacroNode(
                        id="macro_000",
                        label="first",
                        macro_path=first.name,
                        next_on_success="wait_000",
                        next_on_failure="end_error",
                    ),
                    "wait_000": WaitFixedNode(
                        id="wait_000",
                        label="45000ms",
                        duration_ms=45_000,
                        next="macro_001",
                    ),
                    "macro_001": MacroNode(
                        id="macro_001",
                        label="second",
                        macro_path=second.name,
                        next_on_success="end_success",
                        next_on_failure="end_error",
                    ),
                    "end_success": end_success,
                    "end_error": end_error,
                },
            )
            oversized_gap_path = root / "oversized-gap.macroflow"
            save_flow(oversized_gap_flow, str(oversized_gap_path))

            widget = MacroSequencerWidget()
            widget.add_macro_file(first)
            original_paths = [item.path for item in widget._items]
            original_gap = widget._gap_spin.value()
            with (
                patch.object(widget, "confirm_discard_changes", return_value=True),
                patch.object(QMessageBox, "critical"),
            ):
                assert not widget._load_flow_from_path(branch_path)
                assert not widget._load_flow_from_path(uneven_path)
                assert not widget._load_flow_from_path(oversized_gap_path)
            assert [item.path for item in widget._items] == original_paths
            assert widget._gap_spin.value() == original_gap
            assert widget.is_dirty()
            widget.close()
        app.processEvents()
        """
    )


def test_main_window_dirty_tab_and_close_cancel() -> None:
    _run_offscreen(
        """
        import tempfile
        from pathlib import Path
        from unittest.mock import Mock, patch

        from PyQt6.QtGui import QCloseEvent
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from macroflow import player
        from macroflow.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            macro = Path(directory) / "one.json"
            macro.write_text("{}", encoding="utf-8")
            with patch.object(MainWindow, "_restore_settings", lambda self: None):
                window = MainWindow()
            sequencer_index = window._tabs.indexOf(window._sequencer)
            assert window._tabs.tabText(sequencer_index) == "시퀀서"

            window._sequencer.add_macro_file(macro)
            assert window._tabs.tabText(sequencer_index) == "시퀀서 *"
            window._sequencer._set_dirty(False)
            assert window._tabs.tabText(sequencer_index) == "시퀀서"
            window._sequencer._set_dirty(True)

            event = QCloseEvent()
            order = []
            window._state = "playing"
            with (
                patch.object(
                    player,
                    "stop",
                    side_effect=lambda: order.append("stop_playback"),
                ),
                patch("macroflow.win32.stop_emergency_hook"),
                patch.object(window._sequencer, "is_running", return_value=True),
                patch.object(
                    window._sequencer,
                    "stop_sequence",
                    side_effect=lambda: order.append("stop_sequence") or True,
                ),
                patch.object(
                    window._overlay,
                    "stop",
                    side_effect=lambda: order.append("overlay_stop"),
                ),
                patch.object(
                    window._sequencer,
                    "confirm_discard_changes",
                    side_effect=lambda: order.append("confirm") or False,
                ),
            ):
                window.closeEvent(event)
            assert order == [
                "stop_playback",
                "overlay_stop",
                "stop_sequence",
                "overlay_stop",
                "confirm",
            ]
            assert window._state == "idle"
            assert not event.isAccepted()

            blocked_event = QCloseEvent()
            confirm_mock = Mock(return_value=True)
            overlay_stop_mock = Mock()
            window._state = "idle"
            with (
                patch.object(window._sequencer, "is_running", return_value=True),
                patch.object(window._sequencer, "stop_sequence", return_value=False),
                patch.object(window._overlay, "stop", overlay_stop_mock),
                patch.object(
                    window._sequencer,
                    "confirm_discard_changes",
                    confirm_mock,
                ),
                patch.object(QMessageBox, "warning"),
            ):
                window.closeEvent(blocked_event)
            assert not blocked_event.isAccepted()
            overlay_stop_mock.assert_called_once_with()
            confirm_mock.assert_not_called()

            recording_event = QCloseEvent()
            recording_order = []

            class FinishedRecordingThread:
                def join(self, timeout=None):
                    recording_order.append("join_recording")
                    window._state = "idle"

                def is_alive(self):
                    return False

            window._state = "stopping"
            window._recording_stop_thread = FinishedRecordingThread()
            with (
                patch.object(window._sequencer, "is_running", return_value=False),
                patch.object(
                    window._sequencer,
                    "confirm_discard_changes",
                    side_effect=lambda: recording_order.append("confirm") or False,
                ),
            ):
                window.closeEvent(recording_event)
            assert recording_order == ["join_recording", "confirm"]
            assert not recording_event.isAccepted()

            timeout_event = QCloseEvent()
            timeout_order = []

            class AliveRecordingThread:
                def join(self, timeout=None):
                    timeout_order.append("join_recording")

                def is_alive(self):
                    return True

            timeout_confirm = Mock(return_value=False)
            window._state = "stopping"
            window._recording_stop_thread = AliveRecordingThread()
            with (
                patch.object(window._sequencer, "is_running", return_value=False),
                patch.object(
                    window._sequencer,
                    "confirm_discard_changes",
                    timeout_confirm,
                ),
                patch.object(QMessageBox, "warning"),
            ):
                window.closeEvent(timeout_event)
            assert timeout_order == ["join_recording"]
            assert not timeout_event.isAccepted()
            timeout_confirm.assert_not_called()

            playback_event = QCloseEvent()
            playback_confirm = Mock(return_value=False)
            window._state = "playing"
            with (
                patch.object(player, "stop"),
                patch.object(player, "is_playing", return_value=True),
                patch.object(window._sequencer, "is_running", return_value=False),
                patch.object(
                    window._sequencer,
                    "confirm_discard_changes",
                    playback_confirm,
                ),
                patch.object(QMessageBox, "warning"),
            ):
                window.closeEvent(playback_event)
            assert window._state == "playing"
            assert not playback_event.isAccepted()
            playback_confirm.assert_not_called()

            window._state = "idle"
            window._sequencer._set_dirty(False)
            window._overlay.close()
            window.close()
        app.processEvents()
        """
    )
