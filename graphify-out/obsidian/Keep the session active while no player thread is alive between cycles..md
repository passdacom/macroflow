---
source_file: "./src/macroflow/ui/playback_repeat.py"
type: "rationale"
community: "MainWindow OverlayWindow RepeatPlaybackSession PlaybackStartOptions"
location: "L72"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions
---

# Keep the session active while no player thread is alive between cycles.

## Connections
- [[.mark_between_cycles()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/MainWindow_OverlayWindow_RepeatPlaybackSession_PlaybackStartOptions