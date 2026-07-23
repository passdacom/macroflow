---
source_file: "./tests/test_sequencer_backlog.py"
type: "rationale"
community: "MacroSequencerWidget EndNode MacroFlow FlowEngine"
location: "L125"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine
---

# 메인 창 Ctrl+S/다른 이름 저장은 시퀀서 탭에서 플로우 저장으로 위임한다.

## Connections
- [[EndNode]] - `uses` [INFERRED]
- [[MacroFlow]] - `uses` [INFERRED]
- [[MacroNode]] - `uses` [INFERRED]
- [[WaitFixedNode]] - `uses` [INFERRED]
- [[test_main_save_shortcuts_route_to_sequencer_on_sequencer_tab()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine