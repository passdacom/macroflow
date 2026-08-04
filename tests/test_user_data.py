from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from macroflow.user_data import (
    DATA_ROOT_KEY,
    UserDataMode,
    default_user_data_root,
    prepare_application_user_data,
    prepare_user_data,
)


class FakeSettings:
    def __init__(self, values: dict[str, object] | None = None) -> None:
        self.values = dict(values or {})
        self.sync_ok = True

    def value(self, key: str, default: object = None) -> object:
        return self.values.get(key, default)

    def setValue(self, key: str, value: object) -> None:  # noqa: N802
        self.values[key] = value

    def remove(self, key: str) -> None:
        self.values.pop(key, None)

    def sync(self) -> None:
        return None

    def status(self) -> int:
        return 0 if self.sync_ok else 1


def test_default_user_data_root_uses_roaming_appdata(tmp_path: Path) -> None:
    appdata = tmp_path / "Roaming"

    assert default_user_data_root(environ={"APPDATA": str(appdata)}) == (
        appdata / "MacroFlow" / "Data"
    )


def test_default_user_data_root_prefers_local_appdata(tmp_path: Path) -> None:
    local = tmp_path / "Local"
    roaming = tmp_path / "Roaming"

    assert default_user_data_root(
        environ={"LOCALAPPDATA": str(local), "APPDATA": str(roaming)}
    ) == local / "MacroFlow" / "data"


def test_non_frozen_application_keeps_development_data_in_working_directory(
    tmp_path: Path,
) -> None:
    settings = FakeSettings()

    result = prepare_application_user_data(
        settings=settings,
        frozen=False,
        executable=tmp_path / "python",
        cwd=tmp_path / "checkout",
    )

    assert result.mode is UserDataMode.STABLE
    assert result.root == (tmp_path / "checkout").resolve()
    assert result.macros_dir.is_dir()
    assert result.favorites_dir.is_dir()
    assert DATA_ROOT_KEY not in settings.values


def test_explicit_portable_marker_keeps_data_beside_executable(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "portable"
    executable_dir.mkdir()
    (executable_dir / "portable.mode").write_text("", encoding="utf-8")
    macro = executable_dir / "macros" / "portable.json"
    macro.parent.mkdir()
    macro.write_text("{}", encoding="utf-8")
    settings = FakeSettings()

    result = prepare_application_user_data(
        settings=settings,
        frozen=True,
        executable=executable_dir / "MacroFlow.exe",
        target_root=tmp_path / "profile" / "MacroFlow" / "Data",
    )

    assert result.mode is UserDataMode.STABLE
    assert result.root == executable_dir
    assert (result.macros_dir / "portable.json").exists()
    assert DATA_ROOT_KEY not in settings.values


def test_frozen_application_migrates_from_executable_directory(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy = executable_dir / "macros" / "업무.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("{}", encoding="utf-8")
    settings = FakeSettings()
    target = tmp_path / "Roaming" / "MacroFlow"

    result = prepare_application_user_data(
        settings=settings,
        frozen=True,
        executable=executable_dir / "MacroFlow.exe",
        cwd=tmp_path / "ignored",
        target_root=target,
    )

    assert result.mode is UserDataMode.MIGRATED
    assert result.root == target.resolve()
    assert (result.macros_dir / "업무.json").exists()
    assert legacy.exists()


def test_fresh_profile_creates_stable_data_directories(tmp_path: Path) -> None:
    executable_dir = tmp_path / "app" / "1.9.0"
    executable_dir.mkdir(parents=True)
    settings = FakeSettings()
    target = tmp_path / "profile" / "MacroFlow"

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=target,
    )

    assert result.mode is UserDataMode.STABLE
    assert result.root == target
    assert result.macros_dir.is_dir()
    assert result.favorites_dir.is_dir()
    assert settings.values[DATA_ROOT_KEY] == str(target.resolve())


def test_legacy_data_is_copied_verified_and_source_is_preserved(tmp_path: Path) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy_macro = executable_dir / "macros" / "업무.json"
    legacy_favorite = executable_dir / "favorites" / "즐겨찾기.json"
    legacy_index = executable_dir / "favorites" / "_index.json"
    legacy_macro.parent.mkdir(parents=True)
    legacy_favorite.parent.mkdir(parents=True)
    legacy_macro.write_text('{"name":"macro"}', encoding="utf-8")
    legacy_favorite.write_text('{"name":"favorite"}', encoding="utf-8")
    legacy_index.write_text('{"groups":[]}', encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow"
    settings = FakeSettings()

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=target,
    )

    assert result.mode is UserDataMode.MIGRATED
    assert (target / "macros" / "업무.json").read_bytes() == legacy_macro.read_bytes()
    assert (target / "favorites" / "즐겨찾기.json").read_bytes() == legacy_favorite.read_bytes()
    assert (target / "favorites" / "_index.json").read_bytes() == legacy_index.read_bytes()
    assert legacy_macro.exists()
    assert legacy_favorite.exists()
    assert result.copied_files == 3
    assert settings.values[DATA_ROOT_KEY] == str(target.resolve())


def test_legacy_migration_remaps_only_paths_inside_copied_data(tmp_path: Path) -> None:
    executable_dir = tmp_path / "legacy-app"
    macro_path = executable_dir / "macros" / "업무.json"
    favorite_path = executable_dir / "favorites" / "즐겨찾기.json"
    macro_path.parent.mkdir(parents=True)
    favorite_path.parent.mkdir(parents=True)
    macro_path.write_text("{}", encoding="utf-8")
    favorite_path.write_text("{}", encoding="utf-8")
    external = tmp_path / "external" / "외부.json"
    external.parent.mkdir()
    external.write_text("{}", encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow"
    settings = FakeSettings(
        {
            "last_file": str(macro_path),
            "quick_run/slot_1/path": str(favorite_path),
            "quick_run/slot_2/path": str(external),
            "quick_run/recovery/slot_1/path": str(macro_path),
        }
    )

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=target,
    )

    assert result.mode is UserDataMode.MIGRATED
    assert settings.values["last_file"] == str((target / "macros" / "업무.json").resolve())
    assert settings.values["quick_run/slot_1/path"] == str(
        (target / "favorites" / "즐겨찾기.json").resolve()
    )
    assert settings.values["quick_run/recovery/slot_1/path"] == str(
        (target / "macros" / "업무.json").resolve()
    )
    assert settings.values["quick_run/slot_2/path"] == str(external)


def test_existing_profile_with_only_temp_data_still_imports_legacy_files(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    macro_path = executable_dir / "macros" / "업무.json"
    macro_path.parent.mkdir(parents=True)
    macro_path.write_text("{}", encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow"
    (target / "temp").mkdir(parents=True)
    (target / "temp" / "autosave.json").write_text("{}", encoding="utf-8")
    settings = FakeSettings()

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=target,
    )

    assert result.mode is UserDataMode.MIGRATED
    assert (target / "macros" / "업무.json").read_bytes() == macro_path.read_bytes()
    assert (target / "temp" / "autosave.json").exists()
    assert macro_path.exists()


def test_existing_profile_preserves_different_same_named_legacy_file(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy = executable_dir / "macros" / "업무.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"source":"legacy"}', encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow"
    current = target / "macros" / "업무.json"
    current.parent.mkdir(parents=True)
    current.write_text('{"source":"stable"}', encoding="utf-8")
    settings = FakeSettings()

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=target,
    )

    preserved = list((target / "macros").glob("업무.legacy-*.json"))
    assert result.mode is UserDataMode.MIGRATED
    assert current.read_text(encoding="utf-8") == '{"source":"stable"}'
    assert len(preserved) == 1
    assert preserved[0].read_bytes() == legacy.read_bytes()
    assert legacy.exists()


def test_missing_configured_root_recovers_again_from_preserved_legacy_data(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy = executable_dir / "macros" / "업무.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("{}", encoding="utf-8")
    target = tmp_path / "deleted-profile" / "MacroFlow"
    settings = FakeSettings(
        {
            DATA_ROOT_KEY: str(target),
            "user_data/migration_version": 1,
        }
    )

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=tmp_path / "ignored",
    )

    assert result.mode is UserDataMode.MIGRATED
    assert (target / "macros" / "업무.json").read_bytes() == legacy.read_bytes()
    assert legacy.exists()


def test_favorites_index_conflict_is_merged_without_exposing_index_as_macro(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy_dir = executable_dir / "favorites"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / "_index.json").write_text(
        '{"version":1,"groups":[{"id":"legacy","name":"기존","items":["업무.json"]}]}',
        encoding="utf-8",
    )
    (legacy_dir / "업무.json").write_text("{}", encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow" / "Data"
    target_favorites = target / "favorites"
    target_favorites.mkdir(parents=True)
    current_index = '{"version":1,"groups":[]}'
    (target_favorites / "_index.json").write_text(current_index, encoding="utf-8")
    (target_favorites / "업무.json").write_text('{"current":true}', encoding="utf-8")

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=FakeSettings(),
        target_root=target,
    )

    assert result.mode is UserDataMode.MIGRATED
    merged = json.loads((target_favorites / "_index.json").read_text(encoding="utf-8"))
    legacy_group = next(group for group in merged["groups"] if group["id"] == "legacy")
    assert legacy_group["name"] == "기존"
    imported = list(target_favorites.glob("업무.legacy-*.json"))
    assert len(imported) == 1
    assert legacy_group["items"] == [imported[0].name]
    assert (target_favorites / "업무.json").read_text(encoding="utf-8") == (
        '{"current":true}'
    )
    assert not list(target_favorites.glob("_index.legacy-*.json"))
    conflicts = list((target / "migration-conflicts").glob("favorites-index-*.json"))
    assert len(conflicts) == 2
    assert imported[0].read_text(encoding="utf-8") == "{}"


def test_malformed_current_favorites_index_is_backed_up_and_replaced(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy_favorites = executable_dir / "favorites"
    legacy_favorites.mkdir(parents=True)
    (legacy_favorites / "업무.json").write_text("{}", encoding="utf-8")
    (legacy_favorites / "_index.json").write_text(
        '{"version":1,"groups":[{"id":"legacy","name":"기존","items":["업무.json"]}]}',
        encoding="utf-8",
    )
    target = tmp_path / "profile" / "MacroFlow" / "Data"
    target_favorites = target / "favorites"
    target_favorites.mkdir(parents=True)
    (target_favorites / "_index.json").write_text("{malformed", encoding="utf-8")

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=FakeSettings(),
        target_root=target,
    )

    assert result.mode is UserDataMode.MIGRATED
    assert result.error is not None
    merged = json.loads((target_favorites / "_index.json").read_text(encoding="utf-8"))
    assert merged["groups"][0]["name"] == "기존"
    assert len(list((target / "migration-conflicts").glob("favorites-index-*.json"))) == 2


def test_malformed_legacy_favorites_index_is_archived_with_warning(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy_favorites = executable_dir / "favorites"
    legacy_favorites.mkdir(parents=True)
    (legacy_favorites / "업무.json").write_text("{}", encoding="utf-8")
    (legacy_favorites / "_index.json").write_text("{malformed", encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow" / "Data"
    target_favorites = target / "favorites"
    target_favorites.mkdir(parents=True)
    valid_current = '{"version":1,"groups":[{"id":"current","name":"현재","items":[]}]}'
    (target_favorites / "_index.json").write_text(valid_current, encoding="utf-8")

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=FakeSettings(),
        target_root=target,
    )

    assert result.mode is UserDataMode.MIGRATED
    assert result.error is not None
    assert json.loads((target_favorites / "_index.json").read_text(encoding="utf-8"))[
        "groups"
    ][0]["name"] == "현재"
    assert len(list((target / "migration-conflicts").glob("favorites-index-*.json"))) == 2


def test_malformed_legacy_index_without_current_index_is_archived(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy_favorites = executable_dir / "favorites"
    legacy_favorites.mkdir(parents=True)
    (legacy_favorites / "업무.json").write_text("{}", encoding="utf-8")
    (legacy_favorites / "_index.json").write_text("{malformed", encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow" / "Data"

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=FakeSettings(),
        target_root=target,
    )

    assert result.mode is UserDataMode.MIGRATED
    assert result.error is not None
    index = json.loads((target / "favorites" / "_index.json").read_text(encoding="utf-8"))
    assert index["groups"] == []
    assert len(list((target / "migration-conflicts").glob("favorites-index-*.json"))) == 1
    assert (target / "favorites" / "업무.json").exists()


def test_partial_configured_migration_retries_instead_of_adopting_incomplete_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import shutil

    executable_dir = tmp_path / "legacy-app"
    macros = executable_dir / "macros"
    macros.mkdir(parents=True)
    (macros / "a.json").write_text('{"id":"a"}', encoding="utf-8")
    (macros / "b.json").write_text('{"id":"b"}', encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow" / "Data"
    partial = target / "macros" / "a.json"
    partial.parent.mkdir(parents=True)
    partial.write_text('{"id":"a"}', encoding="utf-8")
    settings = FakeSettings({DATA_ROOT_KEY: str(target)})
    real_copy2 = shutil.copy2

    def fail_second(source: Path, destination: Path) -> object:
        if Path(source).name == "b.json":
            raise OSError("injected second-file failure")
        return real_copy2(source, destination)

    monkeypatch.setattr("macroflow.user_data.shutil.copy2", fail_second)
    first = prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=tmp_path / "ignored",
    )
    assert first.mode is UserDataMode.LEGACY_FALLBACK
    assert (target / "macros" / "a.json").exists()
    assert not (target / "macros" / "b.json").exists()

    monkeypatch.setattr("macroflow.user_data.shutil.copy2", real_copy2)
    second = prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=tmp_path / "ignored",
    )

    assert second.mode is UserDataMode.MIGRATED
    assert (target / "macros" / "a.json").exists()
    assert (target / "macros" / "b.json").exists()


def test_new_legacy_delta_is_imported_but_deleted_canonical_file_is_not_resurrected(
    tmp_path: Path,
) -> None:
    legacy_root = tmp_path / "legacy-app"
    legacy_macros = legacy_root / "macros"
    legacy_macros.mkdir(parents=True)
    (legacy_macros / "a.json").write_text('{"id":"a"}', encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow" / "Data"
    settings = FakeSettings()

    first = prepare_user_data(
        executable_dir=legacy_root,
        settings=settings,
        target_root=target,
    )
    assert first.mode is UserDataMode.MIGRATED

    (legacy_macros / "b.json").write_text('{"id":"b"}', encoding="utf-8")
    second = prepare_user_data(
        executable_dir=tmp_path / "new-app-location",
        settings=settings,
        target_root=tmp_path / "ignored",
    )
    assert second.mode is UserDataMode.MIGRATED
    assert (target / "macros" / "b.json").exists()

    (target / "macros" / "a.json").unlink()
    third = prepare_user_data(
        executable_dir=tmp_path / "newer-app-location",
        settings=settings,
        target_root=tmp_path / "ignored-again",
    )
    assert third.mode is UserDataMode.STABLE
    assert not (target / "macros" / "a.json").exists()


def test_occupied_conflict_name_uses_numbered_non_overwriting_destination(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy = executable_dir / "macros" / "same.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"owner":"legacy"}', encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow" / "Data"
    target_macros = target / "macros"
    target_macros.mkdir(parents=True)
    (target_macros / "same.json").write_text('{"owner":"current"}', encoding="utf-8")
    source_hash = hashlib.sha256(legacy.read_bytes()).hexdigest()
    occupied = target_macros / f"same.legacy-{source_hash[:12]}.json"
    occupied.write_text('{"owner":"unrelated"}', encoding="utf-8")

    settings = FakeSettings()
    prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=target,
    )

    preserved = target_macros / f"same.legacy-{source_hash[:12]}-2.json"
    assert json.loads(occupied.read_text(encoding="utf-8"))["owner"] == "unrelated"
    assert json.loads(preserved.read_text(encoding="utf-8"))["owner"] == "legacy"

    occupied.unlink()
    settings.setValue("last_file", str(legacy))
    prepare_user_data(
        executable_dir=tmp_path / "new-app",
        settings=settings,
        target_root=target,
    )
    assert Path(str(settings.value("last_file"))) == preserved


def test_manifest_noop_remaps_settings_to_preserved_conflict_file(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy = executable_dir / "macros" / "same.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text('{"owner":"legacy"}', encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow" / "Data"
    (target / "macros").mkdir(parents=True)
    (target / "macros" / "same.json").write_text(
        '{"owner":"current"}', encoding="utf-8"
    )
    settings = FakeSettings({"last_file": str(legacy)})

    prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=target,
    )
    settings.setValue("last_file", str(legacy))
    result = prepare_user_data(
        executable_dir=tmp_path / "new-app",
        settings=settings,
        target_root=target,
    )

    assert result.mode is UserDataMode.STABLE
    remapped = Path(str(settings.value("last_file")))
    assert remapped.name.startswith("same.legacy-")
    assert json.loads(remapped.read_text(encoding="utf-8"))["owner"] == "legacy"


def test_index_only_delta_keeps_group_mapped_to_preserved_conflict(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy_favorites = executable_dir / "favorites"
    legacy_favorites.mkdir(parents=True)
    (legacy_favorites / "same.json").write_text(
        '{"owner":"legacy"}', encoding="utf-8"
    )
    source_index = legacy_favorites / "_index.json"
    source_index.write_text(
        '{"version":1,"groups":[{"id":"old","name":"Old","items":["same.json"]}]}',
        encoding="utf-8",
    )
    target = tmp_path / "profile" / "MacroFlow" / "Data"
    target_favorites = target / "favorites"
    target_favorites.mkdir(parents=True)
    (target_favorites / "same.json").write_text(
        '{"owner":"current"}', encoding="utf-8"
    )
    (target_favorites / "_index.json").write_text(
        '{"version":1,"groups":[]}', encoding="utf-8"
    )
    settings = FakeSettings()

    prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=target,
    )
    source_index.write_text(
        '{"version":1,"groups":[{"id":"new","name":"New","items":["same.json"]}]}',
        encoding="utf-8",
    )
    prepare_user_data(
        executable_dir=tmp_path / "new-app",
        settings=settings,
        target_root=target,
    )

    merged = json.loads((target_favorites / "_index.json").read_text(encoding="utf-8"))
    new_group = next(group for group in merged["groups"] if group["id"] == "new")
    assert len(new_group["items"]) == 1
    mapped_name = new_group["items"][0]
    assert mapped_name.startswith("same.legacy-")
    assert json.loads((target_favorites / mapped_name).read_text(encoding="utf-8"))[
        "owner"
    ] == "legacy"


def test_stable_fast_path_repairs_legacy_qsettings_paths(tmp_path: Path) -> None:
    executable_dir = tmp_path / "legacy-app"
    legacy = executable_dir / "macros" / "a.json"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("{}", encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow" / "Data"
    settings = FakeSettings({"last_file": str(legacy)})

    first = prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=target,
    )
    assert first.mode is UserDataMode.MIGRATED
    settings.setValue("last_file", str(legacy))

    second = prepare_user_data(
        executable_dir=tmp_path / "new-app",
        settings=settings,
        target_root=tmp_path / "ignored",
    )

    assert second.mode is UserDataMode.STABLE
    assert settings.value("last_file") == str(target / "macros" / "a.json")


def test_symlinked_legacy_directory_fails_closed_without_copying_external_data(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    executable_dir.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.json").write_text("{}", encoding="utf-8")
    try:
        (executable_dir / "macros").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    target = tmp_path / "profile" / "MacroFlow" / "Data"

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=FakeSettings(),
        target_root=target,
    )

    assert result.mode is UserDataMode.STABLE
    assert result.root == target
    assert result.error is not None
    assert "link or junction" in result.error
    assert not (target / "macros" / "secret.json").exists()


def test_symlinked_legacy_root_is_not_resolved_into_a_trusted_source(
    tmp_path: Path,
) -> None:
    real_legacy = tmp_path / "real-legacy"
    macro = real_legacy / "macros" / "secret.json"
    macro.parent.mkdir(parents=True)
    macro.write_text("{}", encoding="utf-8")
    linked_legacy = tmp_path / "linked-legacy"
    try:
        linked_legacy.symlink_to(real_legacy, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")
    target = tmp_path / "profile" / "MacroFlow" / "Data"

    result = prepare_user_data(
        executable_dir=linked_legacy,
        settings=FakeSettings(),
        target_root=target,
    )

    assert result.mode is UserDataMode.STABLE
    assert result.error is not None
    assert not (target / "macros" / "secret.json").exists()


def test_symlinked_stable_root_is_not_resolved_and_written_through(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    macro = executable_dir / "macros" / "safe.json"
    macro.parent.mkdir(parents=True)
    macro.write_text("{}", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    linked_target = tmp_path / "linked-profile"
    try:
        linked_target.symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=FakeSettings(),
        target_root=linked_target,
    )

    assert result.mode is UserDataMode.LEGACY_FALLBACK
    assert not (outside / "macros" / "safe.json").exists()
    assert macro.exists()


def test_symlinked_destination_directory_fails_closed_without_external_write(
    tmp_path: Path,
) -> None:
    executable_dir = tmp_path / "legacy-app"
    macro = executable_dir / "macros" / "safe.json"
    macro.parent.mkdir(parents=True)
    macro.write_text("{}", encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow" / "Data"
    target.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (target / "macros").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks are unavailable on this platform")

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=FakeSettings(),
        target_root=target,
    )

    assert result.mode is UserDataMode.LEGACY_FALLBACK
    assert not (outside / "safe.json").exists()
    assert macro.exists()


def test_unavailable_stable_root_does_not_crash_fresh_application(tmp_path: Path) -> None:
    executable_dir = tmp_path / "app"
    executable_dir.mkdir()
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=FakeSettings(),
        target_root=blocker / "MacroFlow" / "Data",
    )

    assert result.mode is UserDataMode.LEGACY_FALLBACK
    assert result.root == executable_dir.resolve()
    assert result.error


def test_copy_failure_falls_back_to_legacy_without_changing_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    executable_dir = tmp_path / "legacy-app"
    macro_path = executable_dir / "macros" / "업무.json"
    macro_path.parent.mkdir(parents=True)
    macro_path.write_text("{}", encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow"
    settings = FakeSettings({"last_file": str(macro_path)})

    def fail_copy(_source: Path, _destination: Path) -> None:
        raise OSError("injected copy failure")

    monkeypatch.setattr("macroflow.user_data._copy_and_verify_tree", fail_copy)

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=target,
    )

    assert result.mode is UserDataMode.LEGACY_FALLBACK
    assert result.root == executable_dir.resolve()
    assert settings.values == {"last_file": str(macro_path)}
    assert macro_path.exists()
    assert not target.exists()


def test_settings_failure_restores_paths_and_uses_legacy_data(tmp_path: Path) -> None:
    executable_dir = tmp_path / "legacy-app"
    macro_path = executable_dir / "macros" / "업무.json"
    macro_path.parent.mkdir(parents=True)
    macro_path.write_text("{}", encoding="utf-8")
    target = tmp_path / "profile" / "MacroFlow"
    settings = FakeSettings({"last_file": str(macro_path)})
    settings.sync_ok = False

    result = prepare_user_data(
        executable_dir=executable_dir,
        settings=settings,
        target_root=target,
    )

    assert result.mode is UserDataMode.LEGACY_FALLBACK
    assert result.root == executable_dir.resolve()
    assert settings.values == {"last_file": str(macro_path)}
    assert macro_path.exists()
