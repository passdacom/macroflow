---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_player_runtime_safety.py"
type: "code"
community: "execute event PlayState test"
location: "L58"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/execute_event_PlayState_test
---

# test_stop_interrupts_wait_event_without_post_stop_callback()

## Connections
- [[.stop()_1]] - `calls` [INFERRED]
- [[WaitEvent]] - `calls` [INFERRED]
- [[_make_macro()_1]] - `calls` [EXTRACTED]
- [[is_playing()]] - `calls` [INFERRED]
- [[play()]] - `calls` [INFERRED]
- [[test_player_runtime_safety.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/execute_event_PlayState_test