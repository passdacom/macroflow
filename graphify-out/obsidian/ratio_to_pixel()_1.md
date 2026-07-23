---
source_file: "./src/macroflow/win32/dpi.py"
type: "code"
community: "mock.py hooks.py get logical"
location: "L76"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/mock.py_hooks.py_get_logical
---

# ratio_to_pixel()

## Connections
- [[._run_color_check_node()]] - `calls` [INFERRED]
- [[_execute_event()]] - `calls` [INFERRED]
- [[_wait_for_color()]] - `calls` [INFERRED]
- [[dpi.py]] - `contains` [EXTRACTED]
- [[get_logical_screen_size()_1]] - `calls` [EXTRACTED]
- [[화면 비율 좌표를 현재 해상도의 픽셀 좌표로 변환한다.      Args         x_ratio X 좌표 비율 (0.0~1.0).]] - `rationale_for` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/mock.py_hooks.py_get_logical