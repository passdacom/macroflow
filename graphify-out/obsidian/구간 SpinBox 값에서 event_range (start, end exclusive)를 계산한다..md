---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/main_window.py"
type: "rationale"
community: "MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions"
location: "L756"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions
---

# 구간 SpinBox 값에서 event_range (start, end exclusive)를 계산한다.

## Connections
- [[._calc_event_range()]] - `rationale_for` [EXTRACTED]
- [[EventEditorWidget]] - `uses` [INFERRED]
- [[FavoritesWidget]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[OverlayWindow]] - `uses` [INFERRED]
- [[PlaybackStartOptions]] - `uses` [INFERRED]
- [[RepeatPlaybackSession]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions