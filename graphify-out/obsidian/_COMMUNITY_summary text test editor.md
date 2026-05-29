---
type: community
cohesion: 0.29
members: 8
---

# summary text test editor

**Cohesion:** 0.29 - loosely connected
**Members:** 8 nodes

## Members
- [[Event editor summary text helper regression tests.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_editor_summary.py
- [[Pure summary text helpers for the MacroFlow event editor.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_summary.py
- [[Return the event editor footer summary text.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_summary.py
- [[_summary_text()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_summary.py
- [[editor_summary.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_summary.py
- [[test_editor_summary.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_summary.py
- [[test_summary_text_appends_edited_tag_when_macro_is_edited()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_summary.py
- [[test_summary_text_matches_current_refresh_format_without_edited_tag()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_summary.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/summary_text_test_editor
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_EventEditorWidget add single row]]

## Top bridge nodes
- [[_summary_text()]] - degree 5, connects to 1 community