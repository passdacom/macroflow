---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/main_window.py"
type: "rationale"
community: "MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions"
location: "L939"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions
---

# 시퀀스 완료/오류 시 emergency hook 해제 후 툴바·상태바를 갱신한다.

## Connections
- [[._on_sequence_done()]] - `rationale_for` [EXTRACTED]
- [[EventEditorWidget]] - `uses` [INFERRED]
- [[FavoritesWidget]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[OverlayWindow]] - `uses` [INFERRED]
- [[PlaybackStartOptions]] - `uses` [INFERRED]
- [[RepeatPlaybackSession]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions