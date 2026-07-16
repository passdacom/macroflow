---
source_file: "./src/macroflow/ui/sequencer.py"
type: "rationale"
community: "MacroSequencerWidget EndNode MacroFlow FlowEngine"
location: "L653"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine
---

# 현재 목록에서 선형 MacroFlow를 생성한다.          gap_ms > 0 이면 매크로 노드 사이에 WaitFixedNode를 삽입한

## Connections
- [[._build_flow()]] - `rationale_for` [EXTRACTED]
- [[EndNode]] - `uses` [INFERRED]
- [[FlowEngine]] - `uses` [INFERRED]
- [[MacroData]] - `uses` [INFERRED]
- [[MacroFlow]] - `uses` [INFERRED]
- [[MacroNode]] - `uses` [INFERRED]
- [[WaitFixedNode]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine