---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/playback_repeat.py"
type: "rationale"
community: "MacroSequencerWidget MainWindow OverlayWindow RepeatPlaybackSession"
location: "L72"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/MacroSequencerWidget_MainWindow_OverlayWindow_RepeatPlaybackSession
---

# Keep the session active while no player thread is alive between cycles.

## Connections
- [[.mark_between_cycles()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/MacroSequencerWidget_MainWindow_OverlayWindow_RepeatPlaybackSession