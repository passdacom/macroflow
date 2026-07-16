---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/main_window.py"
type: "rationale"
community: "MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions"
location: "L67"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions
---

# MacroFlow 메인 창. 녹화·재생 상태 머신 + UI 통합.

## Connections
- [[EventEditorWidget]] - `uses` [INFERRED]
- [[FavoritesWidget]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[MainWindow]] - `rationale_for` [EXTRACTED]
- [[OverlayWindow]] - `uses` [INFERRED]
- [[PlaybackStartOptions]] - `uses` [INFERRED]
- [[RepeatPlaybackSession]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions