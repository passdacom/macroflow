---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/main_window.py"
type: "rationale"
community: "MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession"
location: "L723"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroSequencerWidget_MainWindow_OverlayWindow_RepeatPlaybackSession
---

# 시퀀서 worker와 관련 overlay/hook/UI 상태를 함께 정리한다.

## Connections
- [[._stop_sequencer()]] - `rationale_for` [EXTRACTED]
- [[EventEditorWidget]] - `uses` [INFERRED]
- [[FavoritesWidget]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[OverlayWindow]] - `uses` [INFERRED]
- [[PlaybackStartOptions]] - `uses` [INFERRED]
- [[RepeatPlaybackSession]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/MacroSequencerWidget_MainWindow_OverlayWindow_RepeatPlaybackSession