"""Stable user-data paths and source-preserving legacy migration."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import uuid
from collections.abc import Mapping, MutableMapping
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Protocol

DATA_ROOT_KEY = "user_data/root"
_MIGRATION_VERSION_KEY = "user_data/migration_version"
_MIGRATION_VERSION = 1
_PATH_KEYS = (
    "last_file",
    *(f"quick_run/slot_{index}/path" for index in range(1, 6)),
    *(f"quick_run/recovery/slot_{index}/path" for index in range(1, 6)),
)


class SettingsStore(Protocol):
    """Minimal QSettings-compatible persistence interface."""

    def value(self, key: str, default: object = None) -> object: ...

    def setValue(self, key: str, value: object) -> None: ...  # noqa: N802

    def remove(self, key: str) -> None: ...


class UserDataMode(Enum):
    """How the active user-data root was selected."""

    STABLE = "stable"
    MIGRATED = "migrated"
    LEGACY_FALLBACK = "legacy_fallback"


@dataclass(frozen=True)
class UserDataPreparation:
    """Resolved user-data directories and migration result."""

    root: Path
    mode: UserDataMode
    copied_files: int = 0
    error: str | None = None

    @property
    def macros_dir(self) -> Path:
        return self.root / "macros"

    @property
    def favorites_dir(self) -> Path:
        return self.root / "favorites"


@dataclass(frozen=True)
class _CopyResult:
    copied_files: int
    path_map: dict[Path, Path]


def default_user_data_root(
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Return the stable per-user data root without creating it."""

    env = os.environ if environ is None else environ
    if appdata := env.get("APPDATA"):
        return Path(appdata).expanduser() / "MacroFlow"
    base_home = Path.home() if home is None else home
    if os.name == "nt":
        return base_home / "AppData" / "Roaming" / "MacroFlow"
    return base_home / ".local" / "share" / "MacroFlow"


def _value(
    settings: Mapping[str, object] | SettingsStore,
    key: str,
    default: object = None,
) -> object:
    if isinstance(settings, Mapping):
        return settings.get(key, default)
    return settings.value(key, default)


def _set_value(
    settings: MutableMapping[str, object] | SettingsStore,
    key: str,
    value: object,
) -> None:
    if isinstance(settings, MutableMapping):
        settings[key] = value
    else:
        settings.setValue(key, value)


def _remove_value(
    settings: MutableMapping[str, object] | SettingsStore,
    key: str,
) -> None:
    if isinstance(settings, MutableMapping):
        settings.pop(key, None)
    else:
        settings.remove(key)


def _sync_succeeded(settings: object) -> bool:
    sync = getattr(settings, "sync", None)
    if callable(sync):
        sync()
    status = getattr(settings, "status", None)
    if not callable(status):
        return True
    raw_status = status()
    status_value = getattr(raw_status, "value", raw_status)
    try:
        return int(status_value) == 0
    except (TypeError, ValueError):
        return False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _copy_and_verify_tree(source: Path, destination: Path) -> _CopyResult:
    copied = 0
    path_map: dict[Path, Path] = {}
    for directory_name in ("macros", "favorites"):
        source_dir = source / directory_name
        destination_dir = destination / directory_name
        destination_dir.mkdir(parents=True, exist_ok=True)
        if not source_dir.exists():
            continue
        for item in sorted(source_dir.rglob("*")):
            if item.is_symlink():
                raise OSError(f"legacy user data contains an unsupported link: {item}")
            relative = item.relative_to(source_dir)
            target = destination_dir / relative
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not item.is_file():
                raise OSError(f"legacy user data contains an unsupported entry: {item}")
            source_hash = _sha256(item)
            if target.exists():
                if target.is_file() and _sha256(target) == source_hash:
                    path_map[item.resolve(strict=False)] = target.resolve(strict=False)
                    continue
                target = target.with_name(
                    f"{target.stem}.legacy-{source_hash[:12]}{target.suffix}"
                )
                if target.exists():
                    if target.is_file() and _sha256(target) == source_hash:
                        path_map[item.resolve(strict=False)] = target.resolve(strict=False)
                        continue
                    raise OSError(f"legacy user-data conflict target is occupied: {target}")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(f".{target.name}.copying-{uuid.uuid4().hex}")
            shutil.copy2(item, temporary)
            if temporary.stat().st_size != item.stat().st_size or _sha256(temporary) != source_hash:
                temporary.unlink(missing_ok=True)
                raise OSError(f"legacy user-data verification failed: {item}")
            os.replace(temporary, target)
            path_map[item.resolve(strict=False)] = target.resolve(strict=False)
            copied += 1
    return _CopyResult(copied, path_map)


def _remapped_path(
    raw_value: object,
    old_root: Path,
    new_root: Path,
    path_map: Mapping[Path, Path],
) -> object:
    if not isinstance(raw_value, str) or not raw_value:
        return raw_value
    try:
        original = Path(raw_value).expanduser().resolve(strict=False)
        relative = original.relative_to(old_root)
    except (OSError, RuntimeError, ValueError):
        return raw_value
    if original in path_map:
        return str(path_map[original])
    candidate = (new_root / relative).resolve(strict=False)
    return str(candidate) if candidate.exists() else raw_value


def _persist_root_and_remap_paths(
    settings: MutableMapping[str, object] | SettingsStore,
    *,
    old_root: Path | None,
    new_root: Path,
    path_map: Mapping[Path, Path] | None = None,
) -> bool:
    missing = object()
    keys = (DATA_ROOT_KEY, _MIGRATION_VERSION_KEY, *_PATH_KEYS)
    snapshot = {key: _value(settings, key, missing) for key in keys}
    expected: dict[str, object] = {
        DATA_ROOT_KEY: str(new_root),
        _MIGRATION_VERSION_KEY: _MIGRATION_VERSION,
    }
    if old_root is not None:
        remapped_files = {} if path_map is None else path_map
        for key in _PATH_KEYS:
            current = _value(settings, key, missing)
            if current is not missing:
                expected[key] = _remapped_path(
                    current,
                    old_root,
                    new_root,
                    remapped_files,
                )
    try:
        for key, value in expected.items():
            _set_value(settings, key, value)
        if _sync_succeeded(settings) and all(
            _value(settings, key, missing) == value for key, value in expected.items()
        ):
            return True
    except (OSError, RuntimeError, TypeError, ValueError):
        pass

    try:
        for key, value in snapshot.items():
            if value is missing:
                _remove_value(settings, key)
            else:
                _set_value(settings, key, value)
        _sync_succeeded(settings)
    except (OSError, RuntimeError, TypeError, ValueError):
        pass
    return False


def _ensure_data_directories(root: Path) -> None:
    (root / "macros").mkdir(parents=True, exist_ok=True)
    (root / "favorites").mkdir(parents=True, exist_ok=True)


def _legacy_data_exists(root: Path) -> bool:
    return any((root / name).exists() for name in ("macros", "favorites"))


def _user_data_files_exist(root: Path) -> bool:
    for directory_name in ("macros", "favorites"):
        directory = root / directory_name
        if directory.exists() and any(item.is_file() for item in directory.rglob("*")):
            return True
    return False


def prepare_application_user_data(
    *,
    settings: MutableMapping[str, object] | SettingsStore,
    frozen: bool | None = None,
    executable: Path | None = None,
    cwd: Path | None = None,
    target_root: Path | None = None,
) -> UserDataPreparation:
    """Prepare paths for the running app while preserving checkout-local dev data."""

    import sys

    is_frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    executable_path = Path(sys.executable) if executable is None else executable
    working_directory = Path.cwd() if cwd is None else cwd
    if not is_frozen:
        development_root = working_directory.expanduser().resolve(strict=False)
        _ensure_data_directories(development_root)
        return UserDataPreparation(development_root, UserDataMode.STABLE)
    return prepare_user_data(
        executable_dir=executable_path.parent,
        settings=settings,
        target_root=target_root,
    )


def prepare_user_data(
    *,
    executable_dir: Path,
    settings: MutableMapping[str, object] | SettingsStore,
    target_root: Path | None = None,
) -> UserDataPreparation:
    """Resolve stable data paths and migrate legacy sibling data without deleting it."""

    executable_root = executable_dir.expanduser().resolve(strict=False)
    configured = _value(settings, DATA_ROOT_KEY, "")
    if isinstance(configured, str) and configured:
        configured_root = Path(configured).expanduser().resolve(strict=False)
        try:
            recover_from_legacy = _legacy_data_exists(executable_root) and not _user_data_files_exist(
                configured_root
            )
            _ensure_data_directories(configured_root)
            if recover_from_legacy:
                copy_result = _copy_and_verify_tree(executable_root, configured_root)
                if not _persist_root_and_remap_paths(
                    settings,
                    old_root=executable_root,
                    new_root=configured_root,
                    path_map=copy_result.path_map,
                ):
                    return UserDataPreparation(
                        executable_root,
                        UserDataMode.LEGACY_FALLBACK,
                        error="user-data settings could not be committed",
                    )
                return UserDataPreparation(
                    configured_root,
                    UserDataMode.MIGRATED,
                    copied_files=copy_result.copied_files,
                )
            return UserDataPreparation(configured_root, UserDataMode.STABLE)
        except OSError as exc:
            if _legacy_data_exists(executable_root):
                return UserDataPreparation(
                    executable_root,
                    UserDataMode.LEGACY_FALLBACK,
                    error=str(exc),
                )
            raise

    stable_root = (
        default_user_data_root() if target_root is None else target_root
    ).expanduser().resolve(strict=False)
    legacy_exists = _legacy_data_exists(executable_root)

    if stable_root.exists():
        try:
            _ensure_data_directories(stable_root)
            copy_result = (
                _copy_and_verify_tree(executable_root, stable_root)
                if legacy_exists
                else _CopyResult(0, {})
            )
            persisted = _persist_root_and_remap_paths(
                settings,
                old_root=executable_root if legacy_exists else None,
                new_root=stable_root,
                path_map=copy_result.path_map,
            )
            if persisted:
                return UserDataPreparation(
                    stable_root,
                    UserDataMode.MIGRATED if copy_result.copied_files else UserDataMode.STABLE,
                    copied_files=copy_result.copied_files,
                )
            if legacy_exists:
                return UserDataPreparation(
                    executable_root,
                    UserDataMode.LEGACY_FALLBACK,
                    error="user-data settings could not be committed",
                )
            return UserDataPreparation(
                stable_root,
                UserDataMode.STABLE,
                error="user-data settings could not be committed",
            )
        except OSError as exc:
            if legacy_exists:
                return UserDataPreparation(
                    executable_root,
                    UserDataMode.LEGACY_FALLBACK,
                    error=str(exc),
                )
            raise

    if not legacy_exists:
        _ensure_data_directories(stable_root)
        persisted = _persist_root_and_remap_paths(
            settings,
            old_root=None,
            new_root=stable_root,
        )
        return UserDataPreparation(
            stable_root,
            UserDataMode.STABLE,
            error=None if persisted else "user-data settings could not be committed",
        )

    stable_root.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".MacroFlow-migrating-", dir=stable_root.parent))
    copy_result = _CopyResult(0, {})
    try:
        copy_result = _copy_and_verify_tree(executable_root, staging)
        os.replace(staging, stable_root)
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        shutil.rmtree(staging, ignore_errors=True)
        return UserDataPreparation(
            executable_root,
            UserDataMode.LEGACY_FALLBACK,
            error=str(exc),
        )

    committed_path_map = {
        source: (stable_root / destination.relative_to(staging)).resolve(strict=False)
        for source, destination in copy_result.path_map.items()
    }
    persisted = _persist_root_and_remap_paths(
        settings,
        old_root=executable_root,
        new_root=stable_root,
        path_map=committed_path_map,
    )
    if not persisted:
        return UserDataPreparation(
            executable_root,
            UserDataMode.LEGACY_FALLBACK,
            error="user-data settings could not be committed",
        )
    return UserDataPreparation(
        stable_root,
        UserDataMode.MIGRATED,
        copied_files=copy_result.copied_files,
    )
