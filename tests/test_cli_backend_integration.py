"""Tests for CLI integration with agent backends."""

import argparse
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from agent_explorer.cli import _get_table_name, _get_db_path
from agent_explorer.backends import get_backend


def test_get_table_name_with_agent_arg():
	"""Test _get_table_name uses backend when agent is specified."""
	args = argparse.Namespace(agent="cursor")
	table_name = _get_table_name(args)
	assert table_name == "cursorDiskKV"


def test_get_table_name_without_agent_arg():
	"""Test _get_table_name defaults to cursor when no agent specified."""
	args = argparse.Namespace()
	table_name = _get_table_name(args)
	assert table_name == "cursorDiskKV"


def test_get_table_name_with_env_var(monkeypatch):
	"""Test _get_table_name respects AGENT_TYPE env var."""
	monkeypatch.setenv("AGENT_TYPE", "cursor")
	args = argparse.Namespace()
	table_name = _get_table_name(args)
	assert table_name == "cursorDiskKV"


def test_get_db_path_with_agent_arg(monkeypatch):
	"""Test _get_db_path uses backend when agent is specified."""
	with tempfile.NamedTemporaryFile(delete=False) as tmp:
		tmp_path = tmp.name
	
	try:
		args = argparse.Namespace(agent="cursor", db=None)
		# Mock the backend to return our test path
		with patch("agent_explorer.cli.default_db_path", return_value=tmp_path):
			result = _get_db_path(args)
			assert result == os.path.abspath(tmp_path)
	finally:
		os.unlink(tmp_path)


def test_get_db_path_with_db_arg():
	"""Test _get_db_path uses db arg when provided."""
	with tempfile.NamedTemporaryFile(delete=False) as tmp:
		tmp_path = tmp.name
	
	try:
		args = argparse.Namespace(agent=None, db=tmp_path)
		result = _get_db_path(args)
		assert result == os.path.abspath(tmp_path)
	finally:
		os.unlink(tmp_path)


def test_get_db_path_with_agent_and_db(monkeypatch):
	"""Test _get_db_path prioritizes db arg over agent backend."""
	with tempfile.NamedTemporaryFile(delete=False) as tmp:
		tmp_path = tmp.name
	
	try:
		args = argparse.Namespace(agent="cursor", db=tmp_path)
		result = _get_db_path(args)
		# db arg should take precedence
		assert result == os.path.abspath(tmp_path)
	finally:
		os.unlink(tmp_path)

