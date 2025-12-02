"""Tests for agent backend system."""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from agent_explorer.backends import get_backend
from agent_explorer.backends.base import AgentBackend
from agent_explorer.backends.cursor import CursorBackend


def test_get_backend_defaults_to_cursor():
	"""Test that get_backend defaults to cursor when no type specified."""
	backend = get_backend()
	assert isinstance(backend, CursorBackend)
	assert backend.get_agent_name() == "cursor"


def test_get_backend_with_cursor_type():
	"""Test getting cursor backend explicitly."""
	backend = get_backend("cursor")
	assert isinstance(backend, CursorBackend)
	assert backend.get_agent_name() == "cursor"


def test_get_backend_with_env_var(monkeypatch):
	"""Test that AGENT_TYPE env var is respected."""
	monkeypatch.setenv("AGENT_TYPE", "cursor")
	backend = get_backend()
	assert isinstance(backend, CursorBackend)


def test_get_backend_unknown_type():
	"""Test that unknown agent type raises ValueError."""
	with pytest.raises(ValueError, match="Unknown agent type"):
		get_backend("unknown_agent")


def test_cursor_backend_table_name():
	"""Test CursorBackend returns correct table name."""
	backend = CursorBackend()
	assert backend.get_table_name() == "cursorDiskKV"


def test_cursor_backend_agent_name():
	"""Test CursorBackend returns correct agent name."""
	backend = CursorBackend()
	assert backend.get_agent_name() == "cursor"


def test_cursor_backend_env_var_name():
	"""Test CursorBackend returns correct env var name."""
	backend = CursorBackend()
	assert backend.get_env_var_name() == "CURSOR_STATE_DB"


def test_cursor_backend_expand_path():
	"""Test path expansion in CursorBackend."""
	backend = CursorBackend()
	
	# Test with absolute path
	abs_path = "/absolute/path/to/db"
	assert backend.expand_path(abs_path) == abs_path
	
	# Test with tilde expansion
	home = os.path.expanduser("~")
	expanded = backend.expand_path("~/test.db")
	assert expanded.startswith(home)
	assert expanded.endswith("/test.db")
	
	# Test with environment variable
	with patch.dict(os.environ, {"TEST_VAR": "/test/path"}):
		expanded = backend.expand_path("$TEST_VAR/db.db")
		assert expanded == "/test/path/db.db"


def test_cursor_backend_db_path_with_env_override(monkeypatch):
	"""Test CursorBackend respects CURSOR_STATE_DB env var."""
	with tempfile.NamedTemporaryFile(delete=False) as tmp:
		tmp_path = tmp.name
	
	try:
		monkeypatch.setenv("CURSOR_STATE_DB", tmp_path)
		backend = CursorBackend()
		result = backend.get_db_path()
		assert result == os.path.abspath(tmp_path)
	finally:
		os.unlink(tmp_path)


def test_cursor_backend_db_path_with_override_param():
	"""Test CursorBackend respects env_override parameter."""
	with tempfile.NamedTemporaryFile(delete=False) as tmp:
		tmp_path = tmp.name
	
	try:
		backend = CursorBackend()
		result = backend.get_db_path(env_override=tmp_path)
		assert result == os.path.abspath(tmp_path)
	finally:
		os.unlink(tmp_path)


def test_cursor_backend_db_path_macos(monkeypatch):
	"""Test CursorBackend returns macOS paths on darwin."""
	monkeypatch.setattr(sys, "platform", "darwin")
	monkeypatch.delenv("CURSOR_STATE_DB", raising=False)
	
	backend = CursorBackend()
	path = backend.get_db_path()
	
	# Should return macOS path structure
	assert "Library/Application Support/Cursor" in path
	assert path.endswith("state.vscdb")


def test_cursor_backend_db_path_windows(monkeypatch):
	"""Test CursorBackend returns Windows paths on Windows."""
	monkeypatch.setattr(sys, "platform", "win32")
	monkeypatch.setattr(os, "name", "nt")
	monkeypatch.delenv("CURSOR_STATE_DB", raising=False)
	monkeypatch.setenv("APPDATA", "C:\\Users\\Test\\AppData\\Roaming")
	
	backend = CursorBackend()
	path = backend.get_db_path()
	
	# Should return Windows path structure
	assert "Cursor" in path
	assert path.endswith("state.vscdb")


def test_cursor_backend_db_path_linux(monkeypatch):
	"""Test CursorBackend returns Linux paths on Linux."""
	monkeypatch.setattr(sys, "platform", "linux")
	monkeypatch.setattr(os, "name", "posix")
	monkeypatch.delenv("CURSOR_STATE_DB", raising=False)
	
	backend = CursorBackend()
	path = backend.get_db_path()
	
	# Should return Linux path structure
	assert ".config/Cursor" in path
	assert path.endswith("state.vscdb")


def test_agent_backend_abstract_methods():
	"""Test that AgentBackend cannot be instantiated directly."""
	with pytest.raises(TypeError):
		AgentBackend()


def test_backend_registry():
	"""Test that backend registry contains expected backends."""
	from agent_explorer.backends import BACKENDS
	
	assert "cursor" in BACKENDS
	assert BACKENDS["cursor"] == CursorBackend

