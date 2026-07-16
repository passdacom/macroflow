---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/main_window.py"
type: "rationale"
community: "MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions"
location: "L1429"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions
---

# 즐겨찾기 저장용 favorites 디렉토리 경로를 반환한다.          macros/ 와 별도의 favorites/ 폴더를 사용한다.

## Connections
- [[._get_favorites_dir()]] - `rationale_for` [EXTRACTED]
- [[EventEditorWidget]] - `uses` [INFERRED]
- [[FavoritesWidget]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroSequencerWidget]] - `uses` [INFERRED]
- [[OverlayWindow]] - `uses` [INFERRED]
- [[PlaybackStartOptions]] - `uses` [INFERRED]
- [[RepeatPlaybackSession]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions