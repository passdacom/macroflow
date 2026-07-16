---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/main_window.py"
type: "rationale"
community: "MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession"
location: "L1"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroSequencerWidget_MainWindow_OverlayWindow_RepeatPlaybackSession
---

# MacroFlow 메인 창.  전체 상태 머신(idle / recording / stopping / playing)을 관리한다. F6/F7 글로

## Connections
- [[EventEditorWidget]] - `uses` [INFERRED]
- [[FavoritesWidget]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[OverlayWindow]] - `uses` [INFERRED]
- [[PlaybackStartOptions]] - `uses` [INFERRED]
- [[RepeatPlaybackSession]] - `uses` [INFERRED]
- [[main_window.py]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroSequencerWidget_MainWindow_OverlayWindow_RepeatPlaybackSession