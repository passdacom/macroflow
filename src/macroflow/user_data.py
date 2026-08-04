"""Stable user-data paths and source-preserving legacy migration."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import uuid
from collections.abc import Mapping, MutableMapping
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

DATA_ROOT_KEY = "user_data/root"
_MIGRATION_VERSION_KEY = "user_data/migration_version"
_LEGACY_ROOT_KEY = "user_data/legacy_root"
_LEGACY_MANIFEST_KEY = "user_data/legacy_manifest"
_MIGRATION_VERSION = 1
_PATH_KEYS = (
    "last_file",
    *(f"quick_run/slot_{index}/path" for index in range(1, 6)),
    *(f"quick_run/recovery/slot_{index}/path" for index in range(1, 6)),
)
_REPARSE_POINT = 0x400
_MAX_FILES = 10_000
_MAX_FILE_BYTES = 256 * 1024 * 1024
_MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024


class SettingsStore(Protocol):
    def value(self, key: str, default: object = None) -> object: ...

    def setValue(self, key: str, value: object) -> None:  # noqa: N802
        ...

    def remove(self, key: str) -> None: ...

    def sync(self) -> None: ...

    def status(self) -> object: ...


class UserDataMode(StrEnum):
    STABLE = "stable"
    MIGRATED = "migrated"
    LEGACY_FALLBACK = "legacy_fallback"


@dataclass(frozen=True)
class UserDataPreparation:
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
    source_manifest: dict[str, str]


def default_user_data_root(
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Return the version-independent per-user data directory."""

    env = os.environ if environ is None else environ
    if local_appdata := env.get("LOCALAPPDATA"):
        return Path(local_appdata).expanduser() / "MacroFlow" / "data"
    if appdata := env.get("APPDATA"):
        # APPDATA fallback is retained for stripped-down/offline Windows profiles.
        return Path(appdata).expanduser() / "MacroFlow" / "Data"
    base_home = Path.home() if home is None else home
    if os.name == "nt":
        return base_home / "AppData" / "Local" / "MacroFlow" / "data"
    return base_home / ".local" / "share" / "MacroFlow" / "data"


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


def _sync_succeeded(settings: MutableMapping[str, object] | SettingsStore) -> bool:
    if isinstance(settings, MutableMapping):
        return True
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


def _is_link_or_reparse(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        attributes = int(getattr(path.lstat(), "st_file_attributes", 0))
    except OSError:
        return False
    return bool(attributes & _REPARSE_POINT)


def _assert_safe_directory(path: Path, *, role: str) -> None:
    if path.exists() and _is_link_or_reparse(path):
        raise OSError(f"{role} directory cannot be a link or junction: {path}")
    if path.exists() and not path.is_dir():
        raise OSError(f"{role} path is not a directory: {path}")


def _exclusive_verified_copy(source: Path, target: Path, source_hash: str) -> None:
    """Copy without ever replacing an existing destination path."""

    target.parent.mkdir(parents=True, exist_ok=True)
    _assert_safe_directory(target.parent, role="destination")
    temporary = target.with_name(f".{target.name}.copying-{uuid.uuid4().hex}")
    created_target = False
    try:
        shutil.copy2(source, temporary)
        if temporary.stat().st_size != source.stat().st_size or _sha256(temporary) != source_hash:
            raise OSError(f"legacy user-data verification failed: {source}")
        try:
            os.link(temporary, target)
            created_target = True
        except FileExistsError:
            if target.is_file() and _sha256(target) == source_hash:
                return
            raise OSError(f"legacy user-data conflict target is occupied: {target}") from None
        except OSError:
            # Filesystems without hard-link support still get exclusive-create semantics.
            try:
                with temporary.open("rb") as source_stream, target.open("xb") as target_stream:
                    created_target = True
                    shutil.copyfileobj(source_stream, target_stream, length=1024 * 1024)
                    target_stream.flush()
                    os.fsync(target_stream.fileno())
            except FileExistsError:
                if target.is_file() and _sha256(target) == source_hash:
                    return
                raise OSError(f"legacy user-data conflict target is occupied: {target}") from None
        if target.stat().st_size != source.stat().st_size or _sha256(target) != source_hash:
            raise OSError(f"legacy user-data destination readback failed: {target}")
    except Exception:
        if created_target:
            target.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)


def _parse_manifest(raw: object) -> dict[str, str]:
    if not isinstance(raw, str) or not raw:
        return {}
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {
        str(key): str(value)
        for key, value in data.items()
        if isinstance(key, str) and isinstance(value, str)
    }


def _read_favorites_index(path: Path) -> dict[str, object] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    if not isinstance(data, dict) or not isinstance(data.get("groups"), list):
        return None
    for group in data["groups"]:
        if (
            not isinstance(group, dict)
            or not isinstance(group.get("id"), str)
            or not isinstance(group.get("name"), str)
            or not isinstance(group.get("items"), list)
            or not all(isinstance(item, str) for item in group["items"])
        ):
            return None
    return data


def _replace_json_with_readback(target: Path, data: Mapping[str, object]) -> None:
    payload = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    temporary = target.with_name(f".{target.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        if target.read_bytes() != payload:
            raise OSError(f"favorites index readback failed: {target}")
    finally:
        temporary.unlink(missing_ok=True)


def _merge_favorites_index(
    source_index: Path,
    target_index: Path,
    destination_root: Path,
    path_map: Mapping[Path, Path],
) -> bool:
    """Merge group metadata while preserving both pre-merge index documents."""
    source_data = _read_favorites_index(source_index)
    target_data = _read_favorites_index(target_index)
    conflict_dir = destination_root / "migration-conflicts"
    source_hash = _sha256(source_index)
    target_hash = _sha256(target_index)
    _exclusive_verified_copy(
        source_index,
        conflict_dir / f"favorites-index-legacy-{source_hash[:12]}.json",
        source_hash,
    )
    if source_data is None or target_data is None:
        return False
    _exclusive_verified_copy(
        target_index,
        conflict_dir / f"favorites-index-current-{target_hash[:12]}.json",
        target_hash,
    )

    merged = deepcopy(target_data)
    merged_groups = merged["groups"]
    assert isinstance(merged_groups, list)
    groups_by_id = {
        group["id"]: group
        for group in merged_groups
        if isinstance(group, dict) and isinstance(group.get("id"), str)
    }
    source_favorites = source_index.parent.resolve(strict=False)
    source_groups = source_data["groups"]
    assert isinstance(source_groups, list)
    for raw_group in source_groups:
        assert isinstance(raw_group, dict)
        group = deepcopy(raw_group)
        mapped_items: list[str] = []
        for item_name in group["items"]:
            source_item = (source_favorites / item_name).resolve(strict=False)
            mapped = path_map.get(source_item)
            mapped_name = (
                mapped.relative_to(target_index.parent).as_posix()
                if mapped is not None and mapped.is_relative_to(target_index.parent)
                else item_name
            )
            if mapped_name not in mapped_items:
                mapped_items.append(mapped_name)
        group["items"] = mapped_items
        existing = groups_by_id.get(group["id"])
        if existing is None:
            merged_groups.append(group)
            groups_by_id[group["id"]] = group
            continue
        existing_items = existing["items"]
        assert isinstance(existing_items, list)
        for item_name in mapped_items:
            if item_name not in existing_items:
                existing_items.append(item_name)

    _replace_json_with_readback(target_index, merged)
    return True


def _copy_and_verify_tree(
    source: Path,
    destination: Path,
    known_manifest: Mapping[str, str] | None = None,
) -> _CopyResult:
    copied = 0
    path_map: dict[Path, Path] = {}
    source_manifest: dict[str, str] = {}
    previous = {} if known_manifest is None else known_manifest
    file_count = 0
    total_bytes = 0

    _assert_safe_directory(destination, role="destination root")
    for directory_name in ("macros", "favorites"):
        source_dir = source / directory_name
        destination_dir = destination / directory_name
        if source_dir.exists():
            _assert_safe_directory(source_dir, role="legacy source")
        if destination_dir.exists():
            _assert_safe_directory(destination_dir, role="destination")
        destination_dir.mkdir(parents=True, exist_ok=True)
        if not source_dir.exists():
            continue

        items = sorted(
            source_dir.rglob("*"),
            key=lambda item: (
                item.is_file() and item.name == "_index.json",
                item.as_posix(),
            ),
        )
        for item in items:
            if _is_link_or_reparse(item):
                raise OSError(f"legacy user data contains an unsupported link: {item}")
            relative = item.relative_to(source_dir)
            target = destination_dir / relative
            if item.is_dir():
                _assert_safe_directory(target, role="destination")
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not item.is_file():
                raise OSError(f"legacy user data contains an unsupported entry: {item}")

            file_count += 1
            size = item.stat().st_size
            total_bytes += size
            if file_count > _MAX_FILES or size > _MAX_FILE_BYTES or total_bytes > _MAX_TOTAL_BYTES:
                raise OSError("legacy user data exceeds the safe migration limits")

            manifest_key = f"{directory_name}/{relative.as_posix()}"
            source_hash = _sha256(item)
            source_manifest[manifest_key] = source_hash
            if previous.get(manifest_key) == source_hash:
                continue

            if target.exists():
                if _is_link_or_reparse(target):
                    raise OSError(f"destination file cannot be a link or junction: {target}")
                if target.is_file() and _sha256(target) == source_hash:
                    path_map[item.resolve(strict=False)] = target.resolve(strict=False)
                    continue
                if directory_name == "favorites" and relative.as_posix() == "_index.json":
                    if _merge_favorites_index(item, target, destination, path_map):
                        path_map[item.resolve(strict=False)] = target.resolve(strict=False)
                        copied += 1
                    continue
                else:
                    target = target.with_name(
                        f"{target.stem}.legacy-{source_hash[:12]}{target.suffix}"
                    )
                if target.exists():
                    if _is_link_or_reparse(target):
                        raise OSError(f"destination file cannot be a link or junction: {target}")
                    if target.is_file() and _sha256(target) == source_hash:
                        path_map[item.resolve(strict=False)] = target.resolve(strict=False)
                        continue
                    raise OSError(f"legacy user-data conflict target is occupied: {target}")

            _exclusive_verified_copy(item, target, source_hash)
            path_map[item.resolve(strict=False)] = target.resolve(strict=False)
            copied += 1

    return _CopyResult(copied, path_map, source_manifest)


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
    source_manifest: Mapping[str, str] | None = None,
) -> bool:
    missing = object()
    keys = (
        DATA_ROOT_KEY,
        _MIGRATION_VERSION_KEY,
        _LEGACY_ROOT_KEY,
        _LEGACY_MANIFEST_KEY,
        *_PATH_KEYS,
    )
    snapshot = {key: _value(settings, key, missing) for key in keys}
    expected: dict[str, object] = {
        DATA_ROOT_KEY: str(new_root),
        _MIGRATION_VERSION_KEY: _MIGRATION_VERSION,
    }
    if old_root is not None and source_manifest is not None:
        expected[_LEGACY_ROOT_KEY] = str(old_root)
        expected[_LEGACY_MANIFEST_KEY] = json.dumps(
            dict(source_manifest), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
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
        if not _sync_succeeded(settings):
            return False
        # Rollback readback is checked even though the caller still receives failure.
        for key, value in snapshot.items():
            current = _value(settings, key, missing)
            if value is missing and current is not missing:
                return False
            if value is not missing and current != value:
                return False
    except (OSError, RuntimeError, TypeError, ValueError):
        return False
    return False


def _ensure_data_directories(root: Path) -> None:
    _assert_safe_directory(root, role="user-data root")
    root.mkdir(parents=True, exist_ok=True)
    for name in ("macros", "favorites"):
        directory = root / name
        _assert_safe_directory(directory, role="user-data")
        directory.mkdir(parents=True, exist_ok=True)


def _legacy_data_exists(root: Path) -> bool:
    return any((root / name).exists() for name in ("macros", "favorites"))


def _legacy_source(
    settings: Mapping[str, object] | SettingsStore,
    executable_root: Path,
) -> Path | None:
    stored = _value(settings, _LEGACY_ROOT_KEY, "")
    if isinstance(stored, str) and stored:
        candidate = Path(stored).expanduser().resolve(strict=False)
        if _legacy_data_exists(candidate):
            return candidate
    return executable_root if _legacy_data_exists(executable_root) else None


def _fallback(root: Path, error: object) -> UserDataPreparation:
    try:
        _ensure_data_directories(root)
    except OSError:
        pass
    return UserDataPreparation(
        root,
        UserDataMode.LEGACY_FALLBACK,
        error=str(error),
    )


def prepare_application_user_data(
    *,
    settings: MutableMapping[str, object] | SettingsStore,
    frozen: bool | None = None,
    executable: Path | None = None,
    cwd: Path | None = None,
    target_root: Path | None = None,
) -> UserDataPreparation:
    """Prepare packaged data, while keeping source checkouts isolated in cwd."""

    if frozen is None:
        import sys

        frozen = bool(getattr(sys, "frozen", False))
        executable = Path(sys.executable)
    if not frozen:
        development_root = (Path.cwd() if cwd is None else cwd).resolve(strict=False)
        _ensure_data_directories(development_root)
        return UserDataPreparation(development_root, UserDataMode.STABLE)
    if executable is None:
        raise ValueError("executable is required for a frozen application")
    return prepare_user_data(
        executable_dir=executable.parent,
        settings=settings,
        target_root=target_root,
    )


def prepare_user_data(
    *,
    executable_dir: Path,
    settings: MutableMapping[str, object] | SettingsStore,
    target_root: Path | None = None,
) -> UserDataPreparation:
    """Resolve stable paths and import legacy deltas without deleting their source."""

    executable_root = executable_dir.expanduser().resolve(strict=False)
    configured = _value(settings, DATA_ROOT_KEY, "")
    stable_root = (
        Path(configured)
        if isinstance(configured, str) and configured
        else default_user_data_root() if target_root is None else target_root
    ).expanduser().resolve(strict=False)
    source_root = _legacy_source(settings, executable_root)
    known_manifest = _parse_manifest(_value(settings, _LEGACY_MANIFEST_KEY, ""))
    stable_existed = stable_root.exists()

    try:
        if source_root is None:
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

        # A missing target cannot trust an old manifest: all source files must be rebuilt.
        effective_manifest = known_manifest if stable_existed else {}
        if not stable_existed:
            stable_root.parent.mkdir(parents=True, exist_ok=True)
            _assert_safe_directory(stable_root.parent, role="destination parent")
            staging = Path(
                tempfile.mkdtemp(prefix=".MacroFlow-migrating-", dir=stable_root.parent)
            )
            try:
                copied = _copy_and_verify_tree(source_root, staging)
                os.rename(staging, stable_root)
            except Exception:
                shutil.rmtree(staging, ignore_errors=True)
                raise
            path_map = {
                source: (stable_root / destination.relative_to(staging)).resolve(strict=False)
                for source, destination in copied.path_map.items()
            }
            copied = _CopyResult(copied.copied_files, path_map, copied.source_manifest)
        else:
            _ensure_data_directories(stable_root)
            copied = _copy_and_verify_tree(source_root, stable_root, effective_manifest)

        manifest_changed = copied.source_manifest != known_manifest
        if not copied.copied_files and not manifest_changed and configured:
            return UserDataPreparation(stable_root, UserDataMode.STABLE)

        persisted = _persist_root_and_remap_paths(
            settings,
            old_root=source_root,
            new_root=stable_root,
            path_map=copied.path_map,
            source_manifest=copied.source_manifest,
        )
        if not persisted:
            return _fallback(source_root, "user-data settings could not be committed")
        return UserDataPreparation(
            stable_root,
            UserDataMode.MIGRATED,
            copied_files=copied.copied_files,
        )
    except (OSError, RuntimeError, TypeError, ValueError) as exc:
        return _fallback(source_root or executable_root, exc)
