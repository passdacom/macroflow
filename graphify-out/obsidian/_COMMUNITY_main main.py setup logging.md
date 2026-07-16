---
type: community
cohesion: 0.36
members: 8
---

# main main.py setup logging

**Cohesion:** 0.36 - loosely connected
**Members:** 8 nodes

## Members
- [[MacroFlow 진입점.  실행 즉시 파일 로그를 시작하고, PyQt6 메인 창을 표시한다. PyQt6 로드 실패 시 ctypes Messag]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/main.py
- [[Win32 MessageBoxW로 치명적 오류를 표시한다 (PyQt6 폴백).      Args         title 다이얼로그 제목.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/main.py
- [[_fatal_dialog()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/main.py
- [[_get_log_dir()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/main.py
- [[_setup_logging()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/main.py
- [[main()]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/main.py
- [[main.py]] - code - /root/.openclaw/workspace/macroflow/src/macroflow/main.py
- [[파일 로그 핸들러를 설정하고 로그 파일 경로를 반환한다.]] - rationale - /root/.openclaw/workspace/macroflow/src/macroflow/main.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/main_main.py_setup_logging
SORT file.name ASC
```

## Connections to other communities
- 2 edges to [[_COMMUNITY_MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession]]

## Top bridge nodes
- [[main()]] - degree 5, connects to 1 community