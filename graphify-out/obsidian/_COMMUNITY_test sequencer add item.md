---
type: community
cohesion: 0.40
members: 5
---

# test sequencer add item

**Cohesion:** 0.40 - moderately connected
**Members:** 5 nodes

## Members
- [[test_add_item_rejects_duplicate_paths_before_append()]] - code - ./tests/test_sequencer_add_item_validation.py
- [[test_add_item_rejects_missing_files_before_append()]] - code - ./tests/test_sequencer_add_item_validation.py
- [[test_sequencer_add_item_validation.py]] - code - ./tests/test_sequencer_add_item_validation.py
- [[같은 매크로 경로는 중복 append 전에 차단해야 한다.]] - rationale - ./tests/test_sequencer_add_item_validation.py
- [[존재하지 않는 파일은 시퀀서 목록 append 전에 차단해야 한다.]] - rationale - ./tests/test_sequencer_add_item_validation.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_sequencer_add_item
SORT file.name ASC
```
