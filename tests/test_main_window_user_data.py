"""MainWindow integration contract for stable packaged user data."""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path


def test_frozen_main_window_migrates_and_uses_stable_user_data(tmp_path: Path) -> None:
    legacy = tmp_path / "legacy"
    appdata = tmp_path / "AppData" / "Roaming"
    local_appdata = tmp_path / "AppData" / "Local"
    settings_dir = tmp_path / "settings"
    macro = legacy / "macros" / "업무.json"
    favorite = legacy / "favorites" / "즐겨찾기.json"
    index = legacy / "favorites" / "_index.json"
    macro.parent.mkdir(parents=True)
    favorite.parent.mkdir(parents=True)
    macro.write_text("{}", encoding="utf-8")
    favorite.write_text("{}", encoding="utf-8")
    index.write_text('{"groups":[]}', encoding="utf-8")

    script = textwrap.dedent(
        f"""
        import os
        import sys
        from pathlib import Path

        os.environ["APPDATA"] = {str(appdata)!r}
        os.environ["LOCALAPPDATA"] = {str(local_appdata)!r}
        os.environ["XDG_CONFIG_HOME"] = {str(settings_dir)!r}
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        sys.frozen = True
        sys.executable = {str(legacy / 'MacroFlow.exe')!r}

        from PyQt6.QtCore import QSettings
        from PyQt6.QtWidgets import QApplication

        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
        QSettings.setPath(
            QSettings.Format.IniFormat,
            QSettings.Scope.UserScope,
            {str(settings_dir)!r},
        )
        initial = QSettings("MacroFlow", "MacroFlow")
        initial.setValue("last_file", str(Path({str(macro)!r})))
        initial.setValue("quick_run/slot_1/path", str(Path({str(favorite)!r})))
        initial.sync()

        from macroflow.ui.main_window import MainWindow

        app = QApplication.instance() or QApplication([])
        MainWindow._restore_settings = lambda self: None
        window = MainWindow()
        expected = Path({str(local_appdata / 'MacroFlow' / 'data')!r}).resolve()
        assert window._get_macros_dir() == expected / "macros", window._get_macros_dir()
        assert window._get_favorites_dir() == expected / "favorites", window._get_favorites_dir()
        assert window._favorites._favorites_dir == expected / "favorites", window._favorites._favorites_dir
        assert window._get_default_dir() == str(expected / "macros")
        assert window._sequencer._get_default_dir() == str(expected / "macros")
        assert window._quick_run._default_dir == expected / "macros"
        assert (expected / "macros" / "업무.json").exists(), list(expected.rglob("*"))
        assert (expected / "favorites" / "즐겨찾기.json").exists(), list(expected.rglob("*"))
        assert (Path({str(legacy)!r}) / "macros" / "업무.json").exists()
        persisted = QSettings("MacroFlow", "MacroFlow")
        assert Path(str(persisted.value("last_file"))) == expected / "macros" / "업무.json"
        assert window._quick_run_slots[0].macro_path == expected / "favorites" / "즐겨찾기.json"
        assert "이전 완료" in window._sb_state.text(), window._sb_state.text()
        from unittest.mock import patch
        with patch("macroflow.ui.main_window.QDesktopServices.openUrl", return_value=True) as opened:
            window._open_user_data_dir()
        assert Path(opened.call_args.args[0].toLocalFile()) == expected
        window.close()

        # A later run must repair a split state even when the manifest has no delta.
        persisted.setValue("last_file", str(Path({str(macro)!r})))
        persisted.sync()
        repair_settings = QSettings("MacroFlow", "MacroFlow")
        from macroflow.user_data import prepare_application_user_data
        repaired = prepare_application_user_data(
            settings=repair_settings,
            frozen=True,
            executable=Path({str(legacy / 'MacroFlow.exe')!r}),
        )
        assert repaired.root == expected
        durable_readback = QSettings("MacroFlow", "MacroFlow")
        durable_readback.sync()
        assert Path(str(durable_readback.value("last_file"))) == expected / "macros" / "업무.json"
        """
    )
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    result = subprocess.run(
        [sys.executable, "-c", script],
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
