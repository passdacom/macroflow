# MacroFlow Versioning Policy

MacroFlow follows [Semantic Versioning](https://semver.org/) using `MAJOR.MINOR.PATCH`.
A release-ready user-visible change must include exactly one version decision before final tests and packaging.
When one change set contains multiple categories, use the highest required category.
An explicit version requested by the user or release owner overrides the automatic classification.

## MAJOR — `X.0.0`

Increment MAJOR and reset MINOR/PATCH to zero when existing users or files require a deliberate migration, for example:

- an existing macro or sequence format can no longer be opened or keeps different meaning;
- a supported command, hotkey, setting, file location, or workflow is removed or incompatibly changed;
- an API or automation contract used by existing integrations is broken;
- installation or privilege requirements change incompatibly.

Example: `1.4.1 → 2.0.0`.

## MINOR — `x.Y.0`

Increment MINOR and reset PATCH to zero for backward-compatible capabilities, for example:

- a new user-facing feature, editor action, hotkey, event type, or workflow;
- a new optional file-format field that older content can continue to use;
- a substantial UI capability that does not break existing behavior.

Example: `1.4.1 → 1.5.0`.

## PATCH — `x.y.Z`

Increment PATCH for backward-compatible corrections, for example:

- bug, crash, race, focus, timing, or data-loss prevention fixes;
- security hardening with no required user migration;
- performance or reliability improvements;
- small UX, wording, sizing, or layout improvements;
- packaging/build fixes that alter the distributed binary but not its user contract.

Example: `1.4.1 → 1.4.2`.

## No version bump

Do not bump for documentation-only, test-only, comment-only, or internal CI maintenance changes that do not produce a new user-distributed application. If such a change is included in a release with user-visible work, the user-visible work determines the bump.

## Timing and procedure

1. Determine the highest category after the release scope is known.
2. Do not bump once per commit; bump once for the release-ready change set.
3. Run `python tools/bump_version.py major|minor|patch` or pass an explicit version such as `1.6.0`.
4. Verify that `pyproject.toml`, `src/macroflow/__init__.py`, and `uv.lock` changed together.
5. Run `pytest`, Ruff, mypy, and `git diff --check` before packaging.
6. The package filename, window title, artifact metadata, and GitHub release derive from this synchronized version.
