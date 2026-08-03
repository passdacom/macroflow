#!/usr/bin/env python3
"""Synchronize MacroFlow's application version across canonical files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_VERSION_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
_TARGETS = {
    "pyproject.toml": re.compile(r'(?m)^(version = ")([^"]+)(")$'),
    "src/macroflow/__init__.py": re.compile(r'(?m)^(__version__ = ")([^"]+)(")$'),
    "uv.lock": re.compile(
        r'(?m)(\[\[package\]\]\nname = "macroflow"\nversion = ")([^"]+)(")'
    ),
    "tools/build_release_bundle.py": re.compile(
        r'(?m)(^\s*"macroflow":\s*")([^"]+)(",$)'
    ),
}


def _next_version(current: str, request: str) -> str:
    match = _VERSION_RE.fullmatch(current)
    if match is None:
        raise ValueError(f"invalid current version: {current}")
    major, minor, patch = (int(part) for part in match.groups())
    if request == "major":
        return f"{major + 1}.0.0"
    if request == "minor":
        return f"{major}.{minor + 1}.0"
    if request == "patch":
        return f"{major}.{minor}.{patch + 1}"
    if _VERSION_RE.fullmatch(request) is None:
        raise ValueError("version must be major, minor, patch, or X.Y.Z")
    return request


def update_versions(root: Path, request: str) -> tuple[str, str]:
    """Validate all version sources, then update them to one computed version."""
    contents: dict[Path, str] = {}
    versions: dict[Path, str] = {}
    for relative, pattern in _TARGETS.items():
        path = root / relative
        text = path.read_text(encoding="utf-8")
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            raise ValueError(f"expected one version declaration in {relative}, found {len(matches)}")
        contents[path] = text
        versions[path] = matches[0].group(2)

    distinct = set(versions.values())
    if len(distinct) != 1:
        details = ", ".join(f"{path.relative_to(root)}={version}" for path, version in versions.items())
        raise ValueError(f"version sources are not synchronized: {details}")

    current = distinct.pop()
    target = _next_version(current, request)
    if target == current:
        raise ValueError(f"target version is already {current}")

    replacements: dict[Path, str] = {}
    for relative, pattern in _TARGETS.items():
        path = root / relative
        replacements[path] = pattern.sub(rf"\g<1>{target}\g<3>", contents[path], count=1)

    temporary_paths: list[tuple[Path, Path]] = []
    try:
        for path, text in replacements.items():
            temporary = path.with_name(f".{path.name}.version.tmp")
            temporary.write_text(text, encoding="utf-8")
            temporary_paths.append((temporary, path))
        for temporary, path in temporary_paths:
            temporary.replace(path)
    finally:
        for temporary, _ in temporary_paths:
            temporary.unlink(missing_ok=True)

    return current, target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="major, minor, patch, or an explicit X.Y.Z")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        current, target = update_versions(args.root.resolve(), args.version)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"MacroFlow version: {current} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
