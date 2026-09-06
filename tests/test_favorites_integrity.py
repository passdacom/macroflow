"""Regression coverage for migration identity and non-destructive startup recovery."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from macroflow.user_data import prepare_user_data


@pytest.mark.parametrize("existing_index", [False, True])
def test_migrated_group_opens_legacy_content_after_restart(tmp_path: Path, existing_index: bool) -> None:
    legacy = tmp_path / "legacy"
    target = tmp_path / "target"
    source = legacy / "favorites"
    dest = target / "favorites"
    source.mkdir(parents=True)
    dest.mkdir(parents=True)
    payload = b'{"events":[{"type":"text","text":"LEGACY ACTION"}]}'
    unrelated = b'{"events":[{"type":"text","text":"UNRELATED ACTION"}]}'
    (source / "a.json").write_bytes(payload)
    (dest / "a.json").write_bytes(unrelated)
    index = json.dumps({"version": 1, "groups": [
        {"id": "work", "name": "Work", "expanded": True, "items": ["a.json"]}
    ]}).encode()
    (source / "_index.json").write_bytes(index)
    if existing_index:
        (dest / "_index.json").write_bytes(index)
    settings: dict[str, object] = {}
    for _ in range(2):
        result = prepare_user_data(executable_dir=legacy, settings=settings, target_root=target)
        assert result.root == target
        groups = json.loads((dest / "_index.json").read_bytes())["groups"]
        imported = next(group for group in groups if group["id"] == "work")
        # An existing target group may legitimately retain its original member.
        names = imported["items"]
        assert any((dest / name).read_bytes() == payload for name in names)
        if not existing_index:
            assert len(names) == 1
            assert (dest / names[0]).read_bytes() == payload
        assert (dest / "a.json").read_bytes() == unrelated
        assert (source / "a.json").read_bytes() == payload
        assert (source / "_index.json").read_bytes() == index


@pytest.mark.parametrize("payload", [
    b'{"groups":', b'\xff', b'null', b'[]', b'{"groups":null}',
    b'{"groups":[null]}',
    b'{"groups":[{"id":"x","name":"X","items":null}]}',
    b'{"groups":[{"id":"x","name":"X","items":[{}]}]}',
    b'{"groups":[{"id":"x","name":"X","expanded":"yes","items":[]}]}',
    b'{"groups":[{"id":"x","name":"X","items":["../outside.json"]}]}',
    b'{"groups":[{"id":"x","name":"X","items":[]},{"id":"x","name":"Y","items":[]}]}',
])
def test_damaged_index_main_window_startup_preserves_bytes(tmp_path: Path, payload: bytes) -> None:
    favorites = tmp_path / "favorites"
    favorites.mkdir()
    (favorites / "_index.json").write_bytes(payload)
    (favorites / "a.json").write_bytes(b'{}')
    script = '''
import os
from pathlib import Path
from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication, QMessageBox
from macroflow.ui.main_window import MainWindow
root = Path.cwd()
QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope, str(root / "settings"))
def no_modal(*args, **kwargs):
    raise AssertionError("startup recovery must not open a modal")
QMessageBox.warning = no_modal
QMessageBox.critical = no_modal
app = QApplication([])
MainWindow._restore_settings = lambda self: None
window = MainWindow()
widget = window._favorites
assert not widget._index_warning.isHidden()
assert widget._index_warning.text()
widget._refresh_tree()
assert widget._find_group("default")["items"] == ["a.json"]
window.close()
'''
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", XDG_CONFIG_HOME=str(tmp_path / "settings"))
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=25)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (favorites / "a.json").read_bytes() == b'{}'
    backups = list(favorites.glob("_index.json.corrupt-*.bak"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == payload
    assert json.loads((favorites / "_index.json").read_bytes())["groups"]


def test_backup_failure_blocks_index_writes_not_widget_startup(tmp_path: Path) -> None:
    script = '''
from pathlib import Path
from unittest.mock import patch
from PyQt6.QtWidgets import QApplication
from macroflow.ui.favorites import FavoritesWidget
root = Path.cwd()
index = root / "_index.json"
index.write_bytes(b'{"groups":')
app = QApplication([])
widget = FavoritesWidget()
with patch("macroflow.favorites_index.tempfile.NamedTemporaryFile", side_effect=PermissionError("read only")):
    widget.set_favorites_dir(root)
    widget._refresh_tree()
    assert widget._save_index() is False
# Restoring filesystem access must not bypass the failed-backup guard.
assert widget._save_index() is False
assert index.read_bytes() == b'{"groups":'
assert not widget._index_warning.isHidden()
widget.close()
'''
    result = subprocess.run([sys.executable, "-c", script], cwd=tmp_path,
                            env=dict(os.environ, QT_QPA_PLATFORM="offscreen"),
                            capture_output=True, text=True, timeout=25)
    assert result.returncode == 0, result.stdout + result.stderr
