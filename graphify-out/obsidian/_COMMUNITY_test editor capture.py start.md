---
type: community
cohesion: 0.24
members: 15
---

# test editor capture.py start

**Cohesion:** 0.24 - loosely connected
**Members:** 15 nodes

## Members
- [[.__init__()_10]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py
- [[._restore_f6_capture_dialog()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor.py
- [[._start_f6_capture()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor.py
- [[.cancel_f6_capture()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor.py
- [[Event editor F6 capture lifecycle behavior with Qt mocked out.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py
- [[_FakeWidget_1]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py
- [[_Signal_1]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py
- [[_import_editor()_1]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py
- [[_install_fake_pyqt()_1]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py
- [[_make_widget()_1]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py
- [[test_cancel_f6_capture_only_emits_when_active()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py
- [[test_consume_f6_capture_runs_once_and_emits_end()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py
- [[test_editor_f6_capture.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py
- [[test_restore_f6_capture_dialog_reenables_button_and_raises_dialog()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py
- [[test_start_f6_capture_sets_callback_updates_controls_and_minimizes_dialog()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_f6_capture.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_editor_capture.py_start
SORT file.name ASC
```

## Connections to other communities
- 4 edges to [[_COMMUNITY_EventEditorWidget add single row]]
- 2 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MouseMoveEvent]]
- 1 edge to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]

## Top bridge nodes
- [[._start_f6_capture()]] - degree 6, connects to 2 communities
- [[._restore_f6_capture_dialog()]] - degree 3, connects to 2 communities
- [[test_consume_f6_capture_runs_once_and_emits_end()]] - degree 5, connects to 1 community
- [[.cancel_f6_capture()]] - degree 2, connects to 1 community