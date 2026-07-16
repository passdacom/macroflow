---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/main_window.py"
type: "rationale"
community: "MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession"
location: "L935"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroSequencerWidget_MainWindow_OverlayWindow_RepeatPlaybackSession
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

#graphify/rationale #graphify/INFERRED #community/MacroSequencerWidget_MainWindow_OverlayWindow_RepeatPlaybackSession