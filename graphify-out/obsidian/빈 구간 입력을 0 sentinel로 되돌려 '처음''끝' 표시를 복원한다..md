---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/main_window.py"
type: "rationale"
community: "MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions"
location: "L750"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions
---

# 빈 구간 입력을 0 sentinel로 되돌려 '처음'/'끝' 표시를 복원한다.

## Connections
- [[._normalize_range_spinboxes()]] - `rationale_for` [EXTRACTED]
- [[EventEditorWidget]] - `uses` [INFERRED]
- [[FavoritesWidget]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[OverlayWindow]] - `uses` [INFERRED]
- [[PlaybackStartOptions]] - `uses` [INFERRED]
- [[RepeatPlaybackSession]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions