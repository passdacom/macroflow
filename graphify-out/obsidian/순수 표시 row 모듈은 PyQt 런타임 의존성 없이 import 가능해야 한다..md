---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_ui_package_imports.py"
type: "rationale"
community: "test package imports.py test"
location: "L10"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/test_package_imports.py_test
---

# 순수 표시 row 모듈은 PyQt 런타임 의존성 없이 import 가능해야 한다.

## Connections
- [[test_editor_rows_import_does_not_eagerly_import_pyqt_widgets()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/test_package_imports.py_test