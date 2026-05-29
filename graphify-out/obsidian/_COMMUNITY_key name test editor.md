---
type: community
cohesion: 0.22
members: 10
---

# key name test editor

**Cohesion:** 0.22 - loosely connected
**Members:** 10 nodes

## Members
- [[Editor key-name to VK-code mapping tests.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_editor_keys.py
- [[Key-name to Windows VK-code mapping for the MacroFlow event editor.  This module]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_keys.py
- [[editor_keys.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_keys.py
- [[key_name_to_vk()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_keys.py
- [[test_editor_keys.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_keys.py
- [[test_editor_keys_import_does_not_eagerly_import_pyqt_widgets()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_keys.py
- [[test_key_name_to_vk_maps_standard_names_and_aliases()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_keys.py
- [[test_key_name_to_vk_returns_fallback_for_unknown_name()]] - code - /root/.openclaw/workspace/macroflow/tests/test_editor_keys.py
- [[키 매핑 helper는 Qt 런타임 없이 독립 import 가능해야 한다.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_editor_keys.py
- [[키 이름 문자열을 VK 코드로 변환한다.      1) NAME_TO_VK 딕셔너리에서 찾는다.     2) Windows 환경에서 단일 문자이]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/ui/editor_keys.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/key_name_test_editor
SORT file.name ASC
```

## Connections to other communities
- 1 edge to [[_COMMUNITY_EventEditorWidget add single row]]

## Top bridge nodes
- [[key_name_to_vk()]] - degree 5, connects to 1 community