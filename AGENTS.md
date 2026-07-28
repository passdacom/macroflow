# Project Instructions

## Graphify First

This project has generated Graphify analysis in `graphify-out/`.

- Read `graphify-out/GRAPH_REPORT.md` before broad architecture, debugging, review, or implementation work.
- Use `graphify query`, `graphify explain`, or `graphify path` with `graphify-out/graph.json` to narrow relevant modules before opening many raw files.
- After meaningful code changes, regenerate the graph:

```bash
/root/.local/share/graphify-venv/bin/python /root/.local/bin/graphify-code-ast-build /root/.openclaw/workspace/macroflow --name macroflow --obsidian-root /root/.openclaw/workspace/obsidian-data/10_Projects/Graphify
```

## Automatic versioning

- Apply the Semantic Versioning policy in `docs/versioning.md` to every release-ready change set.
- Backward-incompatible changes bump MAJOR, backward-compatible features bump MINOR, and backward-compatible fixes or small UX improvements bump PATCH.
- Use the highest category present, bump once per release-ready change set, and honor an explicit user-specified version over automatic classification.
- Documentation/test-only work does not bump the application version unless it ships with user-visible work.
- Before final verification and packaging, run `python tools/bump_version.py major|minor|patch` (or an explicit `X.Y.Z`) so `pyproject.toml`, `src/macroflow/__init__.py`, and `uv.lock` stay synchronized.
