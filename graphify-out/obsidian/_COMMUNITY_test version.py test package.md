---
type: community
cohesion: 0.40
members: 5
---

# test version.py test package

**Cohesion:** 0.40 - moderately connected
**Members:** 5 nodes

## Members
- [[QApplication 버전도 하드코딩하지 않고 패키지 버전을 사용해야 한다.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_version.py
- [[test_package_version_matches_project_metadata()]] - code - /root/.openclaw/workspace/macroflow/tests/test_version.py
- [[test_qapplication_version_uses_package_version()]] - code - /root/.openclaw/workspace/macroflow/tests/test_version.py
- [[test_version.py]] - code - /root/.openclaw/workspace/macroflow/tests/test_version.py
- [[메인 창 타이틀에 쓰는 __version__은 pyproject 버전과 일치해야 한다.]] - rationale - /root/.openclaw/workspace/macroflow/tests/test_version.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_version.py_test_package
SORT file.name ASC
```
