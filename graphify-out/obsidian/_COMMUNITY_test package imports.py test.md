---
type: community
cohesion: 0.50
members: 4
---

# test package imports.py test

**Cohesion:** 0.50 - moderately connected
**Members:** 4 nodes

## Members
- [[UI package import boundaries.]] - rationale - ./tests/test_ui_package_imports.py
- [[test_editor_rows_import_does_not_eagerly_import_pyqt_widgets()]] - code - ./tests/test_ui_package_imports.py
- [[test_ui_package_imports.py]] - code - ./tests/test_ui_package_imports.py
- [[순수 표시 row 모듈은 PyQt 런타임 의존성 없이 import 가능해야 한다.]] - rationale - ./tests/test_ui_package_imports.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_package_imports.py_test
SORT file.name ASC
```
