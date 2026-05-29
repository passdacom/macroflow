---
source_file: "/root/.openclaw/workspace/macroflow/tests/test_favorites_batch.py"
type: "rationale"
community: "FavoritesWidget refresh tree save"
location: "L24"
tags:
  - graphify/rationale
  - graphify/EXTRACTED
  - community/FavoritesWidget_refresh_tree_save
---

# Recover real PyQt modules if earlier source-level tests left fakes in sys.module

## Connections
- [[FavoritesWidget]] - `uses` [INFERRED]
- [[_ensure_real_qt()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/EXTRACTED #community/FavoritesWidget_refresh_tree_save