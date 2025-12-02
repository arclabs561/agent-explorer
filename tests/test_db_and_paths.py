import os
import sqlite3
from pathlib import Path

from agent_explorer import db as dbmod
from agent_explorer import paths as pathmod


def _make_kv_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "kv.sqlite"
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("CREATE TABLE cursorDiskKV(key TEXT PRIMARY KEY, value BLOB)")
    # seed a few rows
    cur.execute("INSERT INTO cursorDiskKV(key, value) VALUES(?, ?)", ("composerData:abc", b'{"title":"Chat A"}'))
    cur.execute("INSERT INTO cursorDiskKV(key, value) VALUES(?, ?)", ("misc:foo", b"hello world"))
    cur.execute("INSERT INTO cursorDiskKV(key, value) VALUES(?, ?)", ("other", b"nope"))
    conn.commit()
    conn.close()
    return db_path


def test_path_to_readonly_uri_and_connect(tmp_path):
    db_path = _make_kv_db(tmp_path)
    uri = dbmod.path_to_readonly_uri(str(db_path))
    assert uri.startswith("file:") and uri.endswith("?mode=ro")
    conn = dbmod.connect_readonly(str(db_path))
    # list tables returns our kv table
    tables = dbmod.list_tables(conn)
    assert "cursorDiskKV" in tables


def test_kv_helpers_and_search(tmp_path):
    db_path = _make_kv_db(tmp_path)
    conn = dbmod.connect_readonly(str(db_path))
    assert dbmod.has_table(conn, "cursorDiskKV")
    info = dbmod.table_info(conn, "cursorDiskKV")
    assert len(info) >= 2
    # keys filters
    keys = dbmod.kv_keys(conn, prefix="composerData:", limit=10)
    assert keys == ["composerData:abc"]
    keys_like = dbmod.kv_keys(conn, like="%misc%", limit=10)
    assert any("misc" in k for k in keys_like)
    # value and search
    v = dbmod.kv_value(conn, "misc:foo")
    assert isinstance(v, (bytes, bytearray))
    rows = dbmod.search_kv(conn, key_like="%misc%", value_contains="world", limit=10)
    assert rows and rows[0][0] == "misc:foo" and rows[0][1] > 0
    # composer_data_keys uses prefix
    cds = dbmod.composer_data_keys(conn, limit=10)
    assert cds == ["composerData:abc"]


def test_paths_default_and_expand_abs(tmp_path, monkeypatch):
	"""Test default_db_path and expand_abs functions."""
	# Test expand_abs
	expanded = pathmod.expand_abs("~/test")
	assert os.path.isabs(expanded)
	
	# Test default_db_path with env override
	test_db = str(tmp_path / "test.db")
	monkeypatch.setenv("CURSOR_STATE_DB", test_db)
	result = pathmod.default_db_path()
	assert result == os.path.abspath(test_db)
	
	# Test default_db_path with agent_type
	result = pathmod.default_db_path(agent_type="cursor")
	assert isinstance(result, str)
	assert len(result) > 0


def test_paths_default_db_path_with_backend(monkeypatch):
	"""Test default_db_path uses backend system when available."""
	# Should use backend system
	result = pathmod.default_db_path(agent_type="cursor")
	assert isinstance(result, str)
	assert len(result) > 0


def test_paths_default_db_path_fallback(monkeypatch):
	"""Test default_db_path falls back to legacy implementation."""
	# Mock backend to fail
	with monkeypatch.context() as m:
		m.setattr(pathmod, "_USE_AGENT_BACKEND", False)
		# Should fall back to legacy implementation
		result = pathmod.default_db_path()
		assert isinstance(result, str)
    # env override wins
    fake = tmp_path / "state.vscdb"
    monkeypatch.setenv("CURSOR_STATE_DB", str(fake))
    assert pathmod.default_db_path() == str(fake)
    # expand_abs resolves user/vars
    monkeypatch.setenv("X_HOME", str(tmp_path))
    p = pathmod.expand_abs("$X_HOME/../" + tmp_path.name)
    assert os.path.isabs(p) and os.path.exists(p)


