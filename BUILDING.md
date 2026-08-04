# Building MacroFlow

These instructions are part of the corresponding source for the GPLv3 release.

## Prerequisites

- Windows 10 or later, x86-64
- Python 3.11.15 installed through `uv`
- `uv` 0.11.8
- Git

The dependency graph and exact wheel hashes are pinned by `uv.lock`. The exact
Windows python-build-standalone runtime URL and SHA-256 are pinned by
`build/python-downloads.json`.

## Test and build

From a clean checkout of the release tag:

```powershell
uv python install 3.11.15 --python-downloads-json-url build/python-downloads.json
uv sync --locked --extra dev --extra ui-test --python 3.11.15
$env:QT_QPA_PLATFORM = "offscreen"
uv run pytest tests/ -v
uv run pyinstaller build/macroflow-win.spec
```

The onedir application is written to `dist/MacroFlow/`. The executable and Qt DLLs remain separate so recipients can replace compatible LGPL-covered libraries. The GitHub Actions workflow verifies that layout, smoke-tests the executable, and runs `tools/build_release_bundle.py` to create the public GPL distribution ZIP.

## Rebuilding or modifying Qt/PyQt

The official release uses the versions and source archives recorded in `uv.lock`, `THIRD_PARTY_NOTICES.md`, and generated `SOURCE_CODE.md`. Every release produced by the current hardened workflow publishes the exact MacroFlow commit plus the reviewed PyQt6, PyQt6-sip, Qt `qtbase`/`qtsvg`/`qtimageformats`, CPython, OpenSSL, libffi, bzip2, XZ Utils, PyInstaller, and `python-build-standalone` source archives as same-release companion assets. GitHub Actions downloads each upstream archive, verifies its pinned SHA-256, and only then uploads it. To test a modified compatible Qt build:

1. Build Qt 6.11.0 from the provided `qtbase`/`qtsvg`/`qtimageformats` sources, or build PyQt6 against that Qt using the provided PyQt6 source.
2. Copy compatible replacement DLLs into `dist/MacroFlow/_internal/PyQt6/Qt6/bin/` and replacement plugins into the matching `plugins/` subdirectory.
3. Keep the original directory structure and run `dist/MacroFlow/MacroFlow-v<version>-build<build>.exe`.
4. Run `--smoke-inline-sequence` and the normal GUI startup smoke used in `.github/workflows/build.yml`.

Alternatively, install the rebuilt PyQt6 wheel into the locked environment and rerun `uv run pyinstaller build/macroflow-win.spec`. The resulting onedir build must pass the same tests, inventory gate, and smoke checks. No MacroFlow license term prohibits reverse engineering when needed to debug modifications to LGPL-covered libraries.

## Source identity

Every public distribution ZIP contains `SOURCE_CODE.md` with its full source commit and release tag. Do not build a public binary from a dirty checkout or a commit different from the declared provenance.

`SOURCE_CODE.md` lists every companion source filename, release URL, upstream URL, and SHA-256. Object code and source are provided as equivalent network access under GPLv3 section 6(d). A public release is incomplete—and binary distribution must stop—if any listed source archive or checksum sidecar is missing.
