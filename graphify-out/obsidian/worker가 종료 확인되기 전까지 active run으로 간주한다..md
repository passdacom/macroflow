---
source_file: "./src/macroflow/ui/sequencer.py"
type: "rationale"
community: "MacroSequencerWidget EndNode MacroFlow FlowEngine"
location: "L469"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine
---

# worker가 종료 확인되기 전까지 active run으로 간주한다.

## Connections
- [[.is_running()_1]] - `rationale_for` [EXTRACTED]
- [[EndNode]] - `uses` [INFERRED]
- [[FlowEngine]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroFlow]] - `uses` [INFERRED]
- [[MacroNode]] - `uses` [INFERRED]
- [[WaitFixedNode]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine