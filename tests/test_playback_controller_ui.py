"""Real Qt wiring tests; orchestration itself is tested without Qt."""
from tests.test_qt_runtime_safety import _run_offscreen


def test_window_delegates_options_pause_stop_and_preserves_owner():
    result = _run_offscreen('''
        from unittest.mock import Mock, patch
        from PyQt6.QtWidgets import QApplication
        from macroflow.types import MacroData, MacroMeta, MacroSettings, WaitEvent
        from macroflow.ui.main_window import MainWindow
        from macroflow.ui.playback_repeat import range_playback_options, RepeatPlaybackSession
        from macroflow.playback_controller import PlaybackOutcome

        app = QApplication.instance() or QApplication([])
        MainWindow._restore_settings = lambda self: None
        window = MainWindow()
        event = WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=1)
        macro = MacroData(meta=MacroMeta(version="1", app_version="test", created_at="now",
                         screen_width=1920, screen_height=1080, dpi_scale=1),
                         settings=MacroSettings(), raw_events=[event], events=[event])
        controller = Mock()
        controller.session = RepeatPlaybackSession(total=1)
        controller.outcome = None
        controller.stop.return_value = False
        with patch("macroflow.win32.start_emergency_hook"), \
             patch("macroflow.win32.stop_emergency_hook"), \
             patch("macroflow.ui.main_window.PlaybackController", return_value=controller) as factory:
            window._start_playback(options=range_playback_options((0, 1)), playback_macro=macro,
                                   forced_speed=3, source_label="quick run")
            assert factory.call_args.args == (macro,)
            options = factory.call_args.kwargs
            assert options["event_range"] == (0, 1)
            assert options["repeat_count"] == 1
            assert options["speed"] == 3
            assert not window._playback_highlights_editor
            controller.start.assert_called_once()
            window._toggle_pause()
            controller.pause.assert_called_once()
            window._toggle_pause()
            controller.resume.assert_called_once()
            assert not window._stop_playback()
            assert window._playback_controller is controller
            assert window._state == "playing"
            # Starting a new request must not replace a still-stopping owner.
            window._start_playback(playback_macro=macro)
            factory.assert_called_once()
            controller.stop.return_value = True
            assert window._stop_playback()
            assert window._state == "idle"
            assert window._playback_controller is None
            # Late terminal notification from the stopped owner is ignored.
            options["on_finished"](PlaybackOutcome("failed", RuntimeError("late")))
            app.processEvents()
            assert window._state == "idle"
        window.close()
    ''')
    assert result.returncode == 0, result.stderr


def test_window_waits_for_controller_error_instead_of_polling_completion():
    result = _run_offscreen('''
        from unittest.mock import Mock, patch
        from macroflow.ui.main_window import MainWindow
        from macroflow.ui.playback_repeat import RepeatPlaybackSession
        host = Mock()
        host._state = "playing"
        host._sequencer.is_running.return_value = False
        host._repeat_session = RepeatPlaybackSession(total=1)
        host._repeat_session.mark_finished()
        with patch("macroflow.player.is_playing", return_value=False):
            MainWindow._poll_state(host)
        host._on_play_complete.assert_not_called()
    ''')
    assert result.returncode == 0, result.stderr


def test_synchronous_stop_surfaces_owned_cleanup_error_once():
    result = _run_offscreen('''
        import threading
        from types import SimpleNamespace
        from unittest.mock import patch
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from macroflow import player
        from macroflow.types import MacroData, MacroMeta, MacroSettings, WaitEvent
        from macroflow.ui.main_window import MainWindow
        from macroflow.ui.playback_repeat import range_playback_options

        app = QApplication.instance() or QApplication([])
        MainWindow._restore_settings = lambda self: None
        window = MainWindow()
        event = WaitEvent(id="wait", type="wait", timestamp_ns=0, duration_ms=10000)
        macro = MacroData(meta=MacroMeta(version="1", app_version="test", created_at="now",
                         screen_width=1920, screen_height=1080, dpi_scale=1),
                         settings=MacroSettings(), raw_events=[event], events=[event])
        started = threading.Event()
        handle = SimpleNamespace(result=None, error=None, exited=threading.Event())
        def play(*args, **kwargs):
            started.set()
            return handle
        def wait_for_exit(session):
            assert session.exited.wait(2)
            return True
        def stop(session):
            session.result = "failed"
            session.error = RuntimeError("input release failed")
            session.exited.set()
        with patch("macroflow.win32.start_emergency_hook"), \
             patch("macroflow.win32.stop_emergency_hook"), \
             patch.object(player, "play", side_effect=play), \
             patch.object(player, "wait_for_exit", side_effect=wait_for_exit), \
             patch.object(player, "stop", side_effect=stop), \
             patch.object(QMessageBox, "warning") as warning:
            window._start_playback(options=range_playback_options((0, 1)), playback_macro=macro)
            assert started.wait(1)
            assert window._stop_playback()
            assert window._state == "idle"
            warning.assert_called_once()
            assert "input release failed" in warning.call_args.args[2]
            app.processEvents()
            warning.assert_called_once()
        window.close()
    ''')
    assert result.returncode == 0, result.stderr
