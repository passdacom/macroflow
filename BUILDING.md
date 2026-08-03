# Building MacroFlow

These instructions are part of the corresponding source for the GPLv3 release.

## Prerequisites

- Windows 10 or later, x86-64
- Python 3.11.15 installed through `uv`
- `uv` 0.11.8
- Git

The dependency graph and exact wheel hashes are pinned by `uv.lock`.

## Test and build

From a clean checkout of the release tag:

```powershell
uv python install 3.11.15
uv sync --locked --extra dev --extra ui-test --python 3.11.15
$env:QT_QPA_PLATFORM = "offscreen"
uv run pytest tests/ -v
uv run pyinstaller build/macroflow-win.spec
```

The onedir application is written to `dist/MacroFlow/`. The executable and Qt DLLs remain separate so recipients can replace compatible LGPL-covered libraries. The GitHub Actions workflow verifies that layout, smoke-tests the executable, and runs `tools/build_release_bundle.py` to create the public GPL distribution ZIP.

## Rebuilding or modifying Qt/PyQt

The official release uses the versions and source archives recorded in `uv.lock`, `THIRD_PARTY_NOTICES.md`, generated `SOURCE_CODE.md`, and the companion `python-build-standalone-20260414-7af98d60e411de479ab16f5537efc7184dffc25a.tar.gz` asset. GitHub Actions verifies that asset against SHA-256 `8f012da286789efb4916bdc7fdd85af15a8ff616de559f99c0c63067a821506c` before publication. To test a modified compatible Qt build:

1. Build Qt 6.11.0 from the provided `qtbase`/`qtsvg` sources, or build PyQt6 against that Qt using the provided PyQt6 source.
2. Copy compatible replacement DLLs into `dist/MacroFlow/_internal/PyQt6/Qt6/bin/` and replacement plugins into the matching `plugins/` subdirectory.
3. Keep the original directory structure and run `dist/MacroFlow/MacroFlow-v<version>-build<build>.exe`.
4. Run `--smoke-inline-sequence` and the normal GUI startup smoke used in `.github/workflows/build.yml`.

Alternatively, install the rebuilt PyQt6 wheel into the locked environment and rerun `uv run pyinstaller build/macroflow-win.spec`. The resulting onedir build must pass the same tests, inventory gate, and smoke checks. No MacroFlow license term prohibits reverse engineering when needed to debug modifications to LGPL-covered libraries.

## Source identity

Every public distribution ZIP contains `SOURCE_CODE.md` with its full source commit and release tag. Do not build a public binary from a dirty checkout or a commit different from the declared provenance.
