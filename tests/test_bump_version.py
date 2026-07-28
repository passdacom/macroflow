"""Version bump automation tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _load_bump_module() -> ModuleType:
    path = Path("tools/bump_version.py")
    spec = importlib.util.spec_from_file_location("bump_version", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_version_sources(root: Path, version: str) -> None:
    (root / "src/macroflow").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        f'[project]\nname = "macroflow"\nversion = "{version}"\n', encoding="utf-8"
    )
    (root / "src/macroflow/__init__.py").write_text(
        f'__version__ = "{version}"\n', encoding="utf-8"
    )
    (root / "uv.lock").write_text(
        f'[[package]]\nname = "macroflow"\nversion = "{version}"\n', encoding="utf-8"
    )


def _read_declared_versions(root: Path) -> set[str]:
    values: set[str] = set()
    for relative in ("pyproject.toml", "src/macroflow/__init__.py", "uv.lock"):
        text = (root / relative).read_text(encoding="utf-8")
        declaration = next(line for line in text.splitlines() if "version" in line)
        values.add(declaration.split('"', 2)[1])
    return values


@pytest.mark.parametrize(
    ("bump_request", "expected"),
    [("major", "2.0.0"), ("minor", "1.5.0"), ("patch", "1.4.2"), ("3.7.9", "3.7.9")],
)
def test_update_versions_synchronizes_all_sources(
    tmp_path: Path, bump_request: str, expected: str
) -> None:
    module = _load_bump_module()
    _write_version_sources(tmp_path, "1.4.1")

    current, target = module.update_versions(tmp_path, bump_request)

    assert (current, target) == ("1.4.1", expected)
    assert _read_declared_versions(tmp_path) == {expected}


def test_update_versions_rejects_mismatch_without_writing(tmp_path: Path) -> None:
    module = _load_bump_module()
    _write_version_sources(tmp_path, "1.4.1")
    init_path = tmp_path / "src/macroflow/__init__.py"
    init_path.write_text('__version__ = "1.4.0"\n', encoding="utf-8")
    before = {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()}

    with pytest.raises(ValueError, match="not synchronized"):
        module.update_versions(tmp_path, "minor")

    assert {path: path.read_bytes() for path in tmp_path.rglob("*") if path.is_file()} == before
