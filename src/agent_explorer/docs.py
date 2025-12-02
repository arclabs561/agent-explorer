from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from .paths import expand_abs


def index_markdown_dir(
	root_dir: str,
	out_path: str,
	extensions: Optional[List[str]] = None,
	include_hidden: bool = False,
) -> int:
	"""Index Markdown-like files under a directory into a JSONL compatible with existing flows.

	Each file becomes one item with keys:
	  {composer_id, turn_index, user_head, assistant_head, annotations, user, assistant}

	- composer_id: stable hash of absolute path prefixed with "doc_"
	- turn_index: 0
	- user: "" (empty)
	- assistant: full file text
	- user_head: filename
	- assistant_head: first non-empty line of the file
	- annotations: {path: relpath_from_root, tags: [], kind: "doc"}
	"""
	import hashlib

	root_abs = expand_abs(root_dir)
	out_abs = expand_abs(out_path)
	os.makedirs(os.path.dirname(out_abs) or ".", exist_ok=True)

	if not extensions:
		extensions = [".md", ".markdown", ".mdown", ".mkd"]
	_extset = set(e.lower() for e in (extensions or []))

	def _keep(path: str) -> bool:
		base = os.path.basename(path)
		if not include_hidden and base.startswith('.'):
			return False
		_, ext = os.path.splitext(base)
		return ext.lower() in _extset

	count = 0
	with open(out_abs, "w", encoding="utf-8") as out:
		for dirpath, dirnames, filenames in os.walk(root_abs):
			if not include_hidden:
				dirnames[:] = [d for d in dirnames if not d.startswith('.')]
			for fname in filenames:
				fpath = os.path.join(dirpath, fname)
				if not _keep(fpath):
					continue
				try:
					with open(fpath, "r", encoding="utf-8") as f:
						text = f.read()
				except Exception:
					continue
				rel = os.path.relpath(fpath, root_abs)
				cid = "doc_" + hashlib.sha1(fpath.encode("utf-8")).hexdigest()[:16]
				first_line = ""
				for line in (text or "").splitlines():
					if line.strip():
						first_line = line.strip()
						break
				item: Dict[str, object] = {
					"composer_id": cid,
					"turn_index": 0,
					"user_head": os.path.basename(fpath)[:160],
					"assistant_head": first_line[:200],
					"annotations": {"path": rel, "tags": [], "kind": "doc"},
					"user": "",
					"assistant": text or "",
				}
				try:
					out.write(json.dumps(item, ensure_ascii=False) + "\n")
					count += 1
				except Exception:
					continue
	return count



# ------------------- note authoring (Obsidian-friendly) -------------------

def _sanitize_filename(title: str) -> str:
	name = (title or "").strip()
	# Replace path separators and control chars
	for ch in ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]:
		name = name.replace(ch, "-")
	# Collapse whitespace
	name = " ".join(name.split())
	return name or "note"


def create_markdown_note(
	root_dir: str,
	title: Optional[str] = None,
	body: Optional[str] = None,
	subdir: Optional[str] = None,
	tags: Optional[List[str]] = None,
	aliases: Optional[List[str]] = None,
	frontmatter_extra: Optional[Dict[str, object]] = None,
	filename: Optional[str] = None,
	date_prefix: bool = True,
) -> str:
	"""Create a Markdown note in a vault directory with YAML front matter.

	Returns absolute path to the created file.
	"""
	from datetime import datetime

	vault = expand_abs(root_dir)
	name = filename or _sanitize_filename(title or "")
	stamp = datetime.now().strftime("%Y-%m-%d")
	if date_prefix and name:
		name = f"{stamp} - {name}"
	if not name.endswith(".md"):
		name = name + ".md"

	# Build directory
	dirpath = os.path.join(vault, subdir) if subdir else vault
	os.makedirs(dirpath, exist_ok=True)
	path = os.path.join(dirpath, name)
	# Avoid overwrite silently: add suffix if exists
	if os.path.exists(path):
		base, ext = os.path.splitext(path)
		i = 1
		alt = f"{base} ({i}){ext}"
		while os.path.exists(alt):
			i += 1
			alt = f"{base} ({i}){ext}"
		path = alt

	created_iso = datetime.now().astimezone().isoformat(timespec="seconds")
	fm: Dict[str, object] = {
		"title": title or _sanitize_filename(name.rsplit(".", 1)[0]),
		"created": created_iso,
		"updated": created_iso,
	}
	if tags:
		fm["tags"] = [t for t in tags if isinstance(t, str) and t]
	if aliases:
		fm["aliases"] = [a for a in aliases if isinstance(a, str) and a]
	if isinstance(frontmatter_extra, dict):
		for k, v in frontmatter_extra.items():
			if k not in fm:
				fm[k] = v

	def _dump_yaml(d: Dict[str, object]) -> str:
		# Minimal YAML emitter with simple unquoted scalars when safe.
		def is_safe_unquoted(s: str) -> bool:
			# Allow letters, numbers, spaces, dash, underscore, dot; no leading/trailing spaces
			if not s:
				return False
			if s != s.strip():
				return False
			import re as _re
			return bool(_re.fullmatch(r"[A-Za-z0-9 _\-.]+", s)) and (":" not in s)
		def q(s: str) -> str:
			return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
		lines: List[str] = ["---"]
		for k, v in d.items():
			if isinstance(v, list):
				lines.append(f"{k}:")
				for it in v:
					if isinstance(it, str):
						lines.append(f"  - {it if is_safe_unquoted(it) else q(it)}")
					else:
						lines.append(f"  - {it}")
			else:
				if isinstance(v, str):
					lines.append(f"{k}: {v if is_safe_unquoted(v) else q(v)}")
				else:
					lines.append(f"{k}: {v}")
		lines.append("---")
		return "\n".join(lines)

	content = (body or "").rstrip() + "\n"
	fm_text = _dump_yaml(fm)
	with open(path, "w", encoding="utf-8") as f:
		f.write(fm_text)
		f.write("\n")
		f.write(content)
	return expand_abs(path)

