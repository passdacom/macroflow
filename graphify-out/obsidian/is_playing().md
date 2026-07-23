---
source_file: "./src/macroflow/player.py"
type: "code"
community: "rdp runtime safety smoke.py"
location: "L732"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/rdp_runtime_safety_smoke.py
---

# is_playing()

## Connections
- [[._poll_state()]] - `calls` [INFERRED]
- [[._stop_playback()]] - `calls` [INFERRED]
- [[_run_hotkey_smoke()]] - `calls` [INFERRED]
- [[player.py]] - `contains` [EXTRACTED]
- [[test_stop_interrupts_wait_event_without_post_stop_callback()]] - `calls` [INFERRED]

#graphify/code #graphify/INFERRED #community/rdp_runtime_safety_smoke.py