---
type: community
cohesion: 0.32
members: 8
---

# test favorites search.py get

**Cohesion:** 0.32 - loosely connected
**Members:** 8 nodes

## Members
- [[FavoritesWidget._setup_ui에 _search_box와 QLineEdit이 있어야 한다.]] - rationale - ./tests/test_favorites_search.py
- [[FavoritesWidget에 _apply_search_filter 메서드가 정의되어야 한다.]] - rationale - ./tests/test_favorites_search.py
- [[_get_favorites_source()]] - code - ./tests/test_favorites_search.py
- [[favorites.py 소스 코드를 직접 읽어 반환한다.]] - rationale - ./tests/test_favorites_search.py
- [[test_favorites_search.py]] - code - ./tests/test_favorites_search.py
- [[test_favorites_widget_has_apply_search_filter()]] - code - ./tests/test_favorites_search.py
- [[test_favorites_widget_has_search_box_in_setup_ui()]] - code - ./tests/test_favorites_search.py
- [[즐겨찾기 검색 필터 존재 여부 테스트.]] - rationale - ./tests/test_favorites_search.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/test_favorites_search.py_get
SORT file.name ASC
```
