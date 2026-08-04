from __future__ import annotations

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

    assert default_user_data_root(environ={"APPDATA": str(appdata)}) == appdata / "MacroFlow"


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
