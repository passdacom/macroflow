---
source_file: "./tests/test_sequencer_backlog.py"
type: "rationale"
community: "MacroSequencerWidget EndNode MacroFlow FlowEngine"
location: "L115"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine
---

# 시퀀스 실제 대기와 병합 timestamp 간격의 speed 의미를 구분한다.

## Connections
- [[EndNode]] - `uses` [INFERRED]
- [[MacroFlow]] - `uses` [INFERRED]
- [[MacroNode]] - `uses` [INFERRED]
- [[WaitFixedNode]] - `uses` [INFERRED]
- [[test_gap_tooltip_distinguishes_runtime_and_merged_timeline_speed()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/MacroSequencerWidget_EndNode_MacroFlow_FlowEngine