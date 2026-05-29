---
source_file: "/root/.openclaw/workspace/macroflow/src/macroflow/ui/sequencer.py"
type: "rationale"
community: "MacroSequencerWidget FlowEngine EndNode MacroFlow"
location: "L427"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroSequencerWidget_FlowEngine_EndNode_MacroFlow
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

#graphify/rationale #graphify/INFERRED #community/MacroSequencerWidget_FlowEngine_EndNode_MacroFlow