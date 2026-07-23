---
type: community
cohesion: 0.07
members: 43
---

# test editor table.py table

**Cohesion:** 0.07 - loosely connected
**Members:** 43 nodes

## Members
- [[.__init__()_16]] - code - ./tests/test_editor_table.py
- [[.__init__()_15]] - code - ./tests/test_editor_table.py
- [[.__init__()_13]] - code - ./tests/test_editor_table.py
- [[.__init__()_14]] - code - ./tests/test_editor_table.py
- [[.__init__()_11]] - code - ./tests/test_editor_table.py
- [[._repaint_row_default()]] - code - ./src/macroflow/ui/editor.py
- [[._repaint_row_highlight()]] - code - ./src/macroflow/ui/editor.py
- [[.flags()]] - code - ./tests/test_editor_table.py
- [[.highlight_event()]] - code - ./src/macroflow/ui/editor.py
- [[.setAlignment()]] - code - ./tests/test_editor_table.py
- [[.setBackground()]] - code - ./tests/test_editor_table.py
- [[.setFlags()]] - code - ./tests/test_editor_table.py
- [[.setForeground()]] - code - ./tests/test_editor_table.py
- [[.setStyleSheet()]] - code - ./tests/test_editor_table.py
- [[.setTextAlignment()]] - code - ./tests/test_editor_table.py
- [[.setToolTip()]] - code - ./tests/test_editor_table.py
- [[QSS 색상 박스에 안전하게 사용할 수 있는 RRGGBB 값인지 검사한다.]] - rationale - ./src/macroflow/ui/editor_table.py
- [[Qt table rendering helpers for the MacroFlow event editor.  This module intentio]] - rationale - ./src/macroflow/ui/editor_table.py
- [[_AlignmentFlag]] - code - ./tests/test_editor_table.py
- [[_ItemFlag]] - code - ./tests/test_editor_table.py
- [[_QBrush]] - code - ./tests/test_editor_table.py
- [[_QColor]] - code - ./tests/test_editor_table.py
- [[_QLabel]] - code - ./tests/test_editor_table.py
- [[_QTableWidgetItem]] - code - ./tests/test_editor_table.py
- [[_QWidget]] - code - ./tests/test_editor_table.py
- [[_Qt]] - code - ./tests/test_editor_table.py
- [[_cell()]] - code - ./src/macroflow/ui/editor_table.py
- [[_import_editor_table()]] - code - ./tests/test_editor_table.py
- [[_install_fake_pyqt()_2]] - code - ./tests/test_editor_table.py
- [[_is_hex_color()]] - code - ./src/macroflow/ui/editor_table.py
- [[_should_use_color_detail_widget()]] - code - ./src/macroflow/ui/editor_table.py
- [[_table_row_items()]] - code - ./src/macroflow/ui/editor_table.py
- [[editor_table.py]] - code - ./src/macroflow/ui/editor_table.py
- [[test_cell_items_are_not_editable_by_default()]] - code - ./tests/test_editor_table.py
- [[test_color_detail_widget_adds_swatch_only_for_valid_hex_color()]] - code - ./tests/test_editor_table.py
- [[test_editor_table.py]] - code - ./tests/test_editor_table.py
- [[test_is_hex_color_accepts_only_safe_rrggbb_values()]] - code - ./tests/test_editor_table.py
- [[test_should_use_color_detail_widget_accepts_only_valid_row_colors()]] - code - ./tests/test_editor_table.py
- [[test_table_row_items_apply_column_text_alignment_and_type_color()]] - code - ./tests/test_editor_table.py
- [[test_table_row_items_uses_empty_content_text_when_swatch_widget_will_be_used()]] - code - ./tests/test_editor_table.py
- [[이벤트 에디터 Qt table rendering helper 회귀 테스트.]] - rationale - ./tests/test_editor_table.py
- [[표시 row 하나를 QTableWidgetItem 목록으로 렌더링한다.]] - rationale - ./src/macroflow/ui/editor_table.py
- [[표시 row가 내용 열에 색상 swatch 위젯을 사용해야 하면 True를 반환한다.]] - rationale - ./src/macroflow/ui/editor_table.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_editor_table.py_table
SORT file.name ASC
```

## Connections to other communities
- 9 edges to [[_COMMUNITY_EventEditorWidget add single row]]
- 3 edges to [[_COMMUNITY_MacroData MouseButtonEvent KeyEvent MacroSettings]]
- 2 edges to [[_COMMUNITY_FavoritesWidget refresh tree save]]
- 1 edge to [[_COMMUNITY_MacroSequencerWidget EndNode MacroFlow FlowEngine]]
- 1 edge to [[_COMMUNITY_MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions]]

## Top bridge nodes
- [[.highlight_event()]] - degree 4, connects to 2 communities
- [[._repaint_row_default()]] - degree 4, connects to 2 communities
- [[._repaint_row_highlight()]] - degree 4, connects to 2 communities
- [[.setForeground()]] - degree 4, connects to 2 communities
- [[test_editor_table.py]] - degree 18, connects to 1 community