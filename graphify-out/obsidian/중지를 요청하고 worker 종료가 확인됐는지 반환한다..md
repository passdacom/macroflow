---
source_file: "./src/macroflow/ui/sequencer.py"
type: "rationale"
community: "MacroSequencerWidget EndNode MacroFlow FlowEngine"
location: "L478"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine
---

# 중지를 요청하고 worker 종료가 확인됐는지 반환한다.

## Connections
- [[.stop_sequence()]] - `rationale_for` [EXTRACTED]
- [[EndNode]] - `uses` [INFERRED]
- [[FlowEngine]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroFlow]] - `uses` [INFERRED]
- [[MacroNode]] - `uses` [INFERRED]
- [[WaitFixedNode]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine