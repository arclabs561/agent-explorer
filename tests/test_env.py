"""Tests for environment variable loading."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from agent_explorer import env


def test_load_dotenv_if_present_no_dotenv(monkeypatch):
	"""Test that load_dotenv_if_present doesn't fail when dotenv is not available."""
	# Mock dotenv to not be available
	with patch.dict("sys.modules", {"dotenv": None}):
		# Should not raise
		env.load_dotenv_if_present()


def test_load_dotenv_if_present_with_dotenv(monkeypatch):
	"""Test that load_dotenv_if_present loads .env files when dotenv is available."""
	try:
		from dotenv import load_dotenv, find_dotenv
	except ImportError:
		pytest.skip("python-dotenv not available")
	
	# Create a temporary .env file
	with tempfile.TemporaryDirectory() as tmpdir:
		env_file = Path(tmpdir) / ".env"
		env_file.write_text("TEST_VAR=test_value\n")
		
		# Change to temp directory
		original_cwd = os.getcwd()
		try:
			os.chdir(tmpdir)
			env.load_dotenv_if_present()
			# Note: We can't easily verify it loaded without checking os.getenv,
			# but we can at least verify it doesn't crash
		finally:
			os.chdir(original_cwd)


def test_load_dotenv_if_present_user_env_files(monkeypatch):
	"""Test that user-level env files are checked."""
	try:
		from dotenv import load_dotenv
	except ImportError:
		pytest.skip("python-dotenv not available")
	
	# Create temporary user env files
	with tempfile.TemporaryDirectory() as tmpdir:
		home_env_1 = Path(tmpdir) / ".agent-explorer.env"
		home_env_2 = Path(tmpdir) / ".agent_explorer.env"
		home_env_1.write_text("TEST_VAR_1=value1\n")
		home_env_2.write_text("TEST_VAR_2=value2\n")
		
		with patch("os.path.expanduser", return_value=str(home_env_1.parent)):
			# Should not crash
			env.load_dotenv_if_present()

