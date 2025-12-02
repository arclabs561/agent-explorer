from __future__ import annotations

import os
from typing import Optional
from .paths import expand_abs


def load_dotenv_if_present() -> None:
	"""Load .env files if python-dotenv is available."""
	try:
		from dotenv import load_dotenv, find_dotenv  # type: ignore
		# Project/local .env (auto-discovered)
		path = find_dotenv(usecwd=True)
		load_dotenv(path, override=False)
		# User-level env files (optional)
		home_env_1 = os.path.expanduser("~/.agent-explorer.env")
		home_env_2 = os.path.expanduser("~/.agent_explorer.env")
		load_dotenv(home_env_1, override=False)
		load_dotenv(home_env_2, override=False)
	except Exception:
		# Optional dependency; ignore if missing
		return


def get_index_jsonl_path(override: Optional[str] = None) -> str:
	"""Get index JSONL path with fallback to defaults.
	
	Priority: override > AGENT_INDEX_JSONL > CURSOR_INDEX_JSONL > default
	"""
	if override:
		return expand_abs(override)
	return expand_abs(
		os.getenv("AGENT_INDEX_JSONL") or 
		os.getenv("CURSOR_INDEX_JSONL", "./cursor_index.jsonl")
	)


def get_vec_db_path(override: Optional[str] = None) -> str:
	"""Get vector DB path with fallback to defaults.
	
	Priority: override > AGENT_VEC_DB > CURSOR_VEC_DB > default
	"""
	if override:
		return expand_abs(override)
	return expand_abs(
		os.getenv("AGENT_VEC_DB") or 
		os.getenv("CURSOR_VEC_DB", "./cursor_vec.db")
	)


def get_items_db_path(override: Optional[str] = None) -> str:
	"""Get items SQLite DB path with fallback to defaults.
	
	Priority: override > AGENT_ITEMS_DB > CURSOR_ITEMS_DB > default
	"""
	if override:
		return expand_abs(override)
	return expand_abs(
		os.getenv("AGENT_ITEMS_DB") or 
		os.getenv("CURSOR_ITEMS_DB", "./cursor_items.db")
	)
