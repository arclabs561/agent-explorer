"""Memory and recall utilities for chat history."""

from __future__ import annotations

import json
import os
import sys
import hashlib
from typing import Dict, List, Optional, Any, Tuple

from .paths import expand_abs
from . import index as indexmod
import llm_utils as llmmod
import llm_cache


def _cache_key(prefix: str, *args, **kwargs) -> str:
	"""Generate a cache key from arguments.
	
	Handles None, lists, tuples, and normalizes inputs for consistency.
	Limits individual argument length to prevent extremely long keys.
	"""
	normalized_args = []
	for arg in args:
		if isinstance(arg, (list, tuple)):
			normalized_args.append(str(sorted(arg)))
		elif arg is None:
			normalized_args.append("None")
		else:
			# Limit length to prevent extremely long cache keys
			normalized_args.append(str(arg).strip()[:1000])

	normalized_kwargs = []
	for k, v in sorted(kwargs.items()):
		if isinstance(v, (list, tuple)):
			normalized_kwargs.append(f"{k}={sorted(v)}")
		elif v is None:
			normalized_kwargs.append(f"{k}=None")
		else:
			normalized_kwargs.append(f"{k}={str(v).strip()[:1000]}")

	parts = [prefix] + normalized_args + normalized_kwargs
	key_str = "|".join(parts)
	return hashlib.sha256(key_str.encode()).hexdigest()


def _get_index_mtime(index_path: str) -> Optional[float]:
	"""Get modification time of index file."""
	if os.path.exists(index_path):
		return os.path.getmtime(index_path)
	return None


def _is_index_stale(index_path: str, db_path: Optional[str] = None) -> bool:
	"""Check if index is stale compared to source DB.
	
	Returns True if index doesn't exist or is older than source DB.
	Handles file system errors gracefully.
	"""
	if not os.path.exists(index_path):
		return True

	try:
		index_mtime = os.path.getmtime(index_path)
	except OSError:
		# File may have been deleted or is inaccessible
		return True

	# Check if source DB is newer
	if db_path and os.path.exists(db_path):
		try:
			db_mtime = os.path.getmtime(db_path)
			# Add small tolerance (1 second) for clock skew and file system precision
			if db_mtime > (index_mtime + 1.0):
				return True
		except OSError:
			# DB may be inaccessible, assume index is not stale
			pass

	return False


def ensure_indexed(
	index_jsonl: Optional[str] = None,
	vec_db: Optional[str] = None,
	db_path: Optional[str] = None,
	force: bool = False,
) -> Dict[str, str]:
	"""Ensure indexes exist, creating them if needed (idempotent).
	
	Checks if indexes are up-to-date before rebuilding.
	Returns dict with paths to index_jsonl and vec_db.
	"""
	# Default paths (centralized env var resolution)
	from . import env as envmod
	index_path = envmod.get_index_jsonl_path(index_jsonl)
	vec_path = envmod.get_vec_db_path(vec_db)

	# Check if index exists and is up-to-date
	index_exists = os.path.exists(index_path) and os.path.getsize(index_path) > 0
	index_stale = _is_index_stale(index_path, db_path) if index_exists else True

	# Create JSONL index if needed (idempotent: only rebuild if stale or forced)
	if not index_exists or index_stale or force:
		if os.getenv("CURSOR_VERBOSE"):
			print(f"Building index: {index_path} (stale={index_stale}, force={force})", file=sys.stderr)
		count = indexmod.build_index(
			index_path,
			db_path=db_path,
			limit_composers=None,
			max_turns_per=None,
		)
		index_exists = count > 0

	# Check if vec DB exists and is up-to-date with index
	vec_exists = os.path.exists(vec_path) and os.path.getsize(vec_path) > 0
	vec_stale = False
	if vec_exists and index_exists:
		# Check if vec DB is older than index
		vec_mtime = os.path.getmtime(vec_path)
		index_mtime = _get_index_mtime(index_path)
		if index_mtime and index_mtime > vec_mtime:
			vec_stale = True

	# Create vec DB if needed (idempotent: only rebuild if stale or forced)
	if index_exists and (not vec_exists or vec_stale or force):
		try:
			if os.getenv("CURSOR_VERBOSE"):
				print(f"Building vector DB: {vec_path} (stale={vec_stale}, force={force})", file=sys.stderr)
			# Use changed_only=True for idempotency (only update changed items)
			indexmod.build_embeddings_sqlite(
				vec_path,
				index_path,
				table="vec_index",
				changed_only=not force,  # Only update changed items unless forced
			)
			vec_exists = True
		except Exception as e:
			# vec DB creation is optional (requires sqlite-vec)
			if os.getenv("CURSOR_VERBOSE"):
				print(f"Vector DB creation skipped: {e}", file=sys.stderr)
			pass

	return {
		"index_jsonl": index_path if index_exists else None,
		"vec_db": vec_path if vec_exists else None,
		"indexed": index_exists,
		"vectorized": vec_exists,
		"was_stale": index_stale or vec_stale,
	}


def find_solution(
	query: str,
	index_jsonl: Optional[str] = None,
	vec_db: Optional[str] = None,
	db_path: Optional[str] = None,
	k: int = 10,
	auto_index: bool = True,
	use_cache: bool = True,
) -> Dict[str, Any]:
	"""Find past solutions to a problem (cached and idempotent).
	
	High-level wrapper that:
	1. Ensures indexes exist (if auto_index, idempotent)
	2. Searches for relevant conversations (cached)
	3. Returns structured results with conversation context
	"""
	# Ensure indexes exist (idempotent)
	if auto_index:
		indexes = ensure_indexed(index_jsonl, vec_db, db_path)
		index_jsonl = indexes.get("index_jsonl")
		vec_db = indexes.get("vec_db")

	if not index_jsonl or not os.path.exists(index_jsonl):
		return {"error": "Index not found. Run 'index' command first or set auto_index=True."}

	query_normalized = query.strip()[:1000]

	# Check cache for search results (cache key includes query, k, and index mtime)
	cache_key = None
	cache_hit = False
	if use_cache:
		index_mtime = _get_index_mtime(index_jsonl)
		cache_key = _cache_key("find-solution", query_normalized, k, index_jsonl, index_mtime or 0)
		cached = llm_cache.get(cache_key)
		if cached:
			try:
				result = json.loads(cached)
				result["cache_hit"] = True
				return result
			except (json.JSONDecodeError, ValueError):
				pass

	# Try multiple search methods and fuse results using rank-fusion
	# Collect results from all available methods
	vector_results: List[Dict] = []
	sparse_results: List[Dict] = []
	jsonl_results: List[Dict] = []
	
	# Vector search (if available)
	if vec_db and os.path.exists(vec_db):
		try:
			vector_results = indexmod.vec_search(vec_db, "vec_index", query, top_k=k * 2)
		except Exception:
			pass

	# Sparse search (SQLite items table)
	from . import env as envmod
	items_db = envmod.get_items_db_path()
	if os.path.exists(items_db):
		try:
			sparse_results = indexmod.items_search(items_db, "items", query_normalized, k=k * 2)  # Get more for fusion
			except Exception:
				pass

	# JSONL search (always available as fallback, but also used for fusion)
	if not vector_results and not sparse_results:
		# Only run JSONL if no other results (fallback mode)
		try:
			from . import rag as ragmod
			_score = ragmod._score

			# Use streaming approach for large files - process line by line
			# Keep only top candidates in memory to avoid memory issues
			best_results: List[Tuple[float, Dict]] = []  # (score, item)

			with open(index_jsonl, "r", encoding="utf-8") as f:
				malformed_count = 0
				for line_num, line in enumerate(f, 1):
					line = line.strip()
					if not line:  # Skip empty lines
						continue
					try:
						obj = json.loads(line)
						# Build searchable text
						user = obj.get("user", "") or ""
						assistant = obj.get("assistant", "") or ""
						text = (user + "\n" + assistant).strip()
						if not text:
							continue

						# Quick score check - only keep top candidates
						score = _score(query_normalized, text)
						# Light boost for tags (same as search_items)
						ann = obj.get("annotations") or {}
						tags = ann.get("tags") or []
						for t in tags:
							if t and t.lower() in query_normalized.lower():
								score += 2

						if score > 0:
							best_results.append((score, obj))
							# Keep only top k*2 candidates during scan to limit memory
							if len(best_results) > k * 2:
								best_results.sort(key=lambda x: x[0], reverse=True)
								best_results = best_results[:k * 2]
					except json.JSONDecodeError:
						malformed_count += 1
						continue
					except (AttributeError, KeyError, TypeError):
						continue

			# Sort and return top k*2 for potential fusion
			best_results.sort(key=lambda x: x[0], reverse=True)
			jsonl_results = [item for score, item in best_results[:k * 2]]
			except Exception:
				pass

	# Fuse results using rank-fusion if multiple sources available
	results: List[Dict] = []
	search_method = None
	
	# Collect all result lists for fusion
	result_lists = []
	if vector_results:
		result_lists.append(("vector", vector_results))
	if sparse_results:
		result_lists.append(("sparse", sparse_results))
	if jsonl_results:
		result_lists.append(("jsonl", jsonl_results))
	
	if len(result_lists) > 1:
		# Multiple sources: use rank-fusion to combine
		try:
			import rank_fusion
			
			# Convert to rank-fusion format: [(id, score), ...]
			# For vector: use (1.0 - distance) as score (higher is better)
			# For sparse/jsonl: use existing score
			rank_lists = []
			for method_name, method_results in result_lists:
				ranks = []
				for r in method_results:
					# Create unique ID
					cid = r.get("composer_id", "")
					tix = r.get("turn_index", 0)
					item_id = f"{cid}:{tix}"
					
					# Normalize scores (higher is better)
					if method_name == "vector":
						# Distance: lower is better, so invert
						distance = r.get("distance", 1.0)
						score = max(0.0, 1.0 - distance)  # Convert to similarity score
					else:
						# Sparse/JSONL: score is already higher=better, normalize to 0-1
						raw_score = float(r.get("score", 0))
						score = min(1.0, raw_score / 100.0) if raw_score > 0 else 0.0
					
					ranks.append((item_id, score))
				
				if ranks:
					rank_lists.append(ranks)
			
			# Fuse using RRF (Reciprocal Rank Fusion)
			if len(rank_lists) >= 2:
				fused = rank_fusion.rrf_multi(rank_lists, k=k * 2)
				search_method = "fusion"
				
				# Map fused results back to full result objects
				# Create lookup by ID
				all_results_by_id: Dict[str, Dict] = {}
				for method_name, method_results in result_lists:
					for r in method_results:
						cid = r.get("composer_id", "")
						tix = r.get("turn_index", 0)
						item_id = f"{cid}:{tix}"
						if item_id not in all_results_by_id:
							all_results_by_id[item_id] = r.copy()
						# Merge scores from different methods
						if method_name == "vector":
							all_results_by_id[item_id]["vec_distance"] = r.get("distance")
						else:
							all_results_by_id[item_id]["sparse_score"] = r.get("score")
				
				# Build results from fused ranking
				for item_id, fused_score in fused[:k]:
					if item_id in all_results_by_id:
						r = all_results_by_id[item_id].copy()
						r["fused_score"] = fused_score
						results.append(r)
			else:
				# Only one source, use it directly
				search_method, results = result_lists[0]
		except ImportError:
			if vector_results:
				results = vector_results[:k]
				search_method = "vector"
			elif sparse_results:
				results = sparse_results[:k]
				search_method = "sparse"
			elif jsonl_results:
				results = jsonl_results[:k]
				search_method = "jsonl"
		except Exception:
			if vector_results:
				results = vector_results[:k]
				search_method = "vector"
			elif sparse_results:
				results = sparse_results[:k]
				search_method = "sparse"
			elif jsonl_results:
				results = jsonl_results[:k]
				search_method = "jsonl"
	else:
		# Single source: use it directly
		if result_lists:
			search_method, results = result_lists[0]
			results = results[:k]

	# Enrich results with conversation context (limit to k to avoid unnecessary processing)
	enriched = []
	seen = set()  # Deduplicate by (composer_id, turn_index)
	overall_match_type = None  # Track overall match type
	for r in results:
		if len(enriched) >= k:
			break
		composer_id = r.get("composer_id")
		turn_index = r.get("turn_index")
		# Skip entries with missing or invalid composer_id
		if not composer_id or not isinstance(composer_id, str):
			continue
		# Normalize turn_index (handle None, ensure it's an integer)
		if turn_index is None:
			continue
		try:
			turn_index = int(turn_index)
		except (ValueError, TypeError):
			continue
		# Deduplicate: same conversation + turn
		key = (composer_id, turn_index)
		if key not in seen:
			seen.add(key)
			# Determine match type from available scores
			match_type = "fusion" if "fused_score" in r else ("vector" if "distance" in r or "vec_distance" in r else "sparse")
			if overall_match_type is None:
				overall_match_type = match_type
			# Use fused_score if available, otherwise use best available score
			score = r.get("fused_score") or r.get("score") or r.get("distance")
			enriched.append({
				"composer_id": composer_id,
				"turn_index": turn_index,
				"user_head": (r.get("user_head") or "")[:200],
				"assistant_head": (r.get("assistant_head") or "")[:300],
				"score": score,
				"match_type": match_type,
			})

	result = {
		"query": query,
		"results": enriched,
		"count": len(enriched),
		"index_path": index_jsonl,
		"vec_db_path": vec_db,
		"cache_hit": cache_hit,
		"match_type": overall_match_type,  # Overall match type (vector/sparse/fusion)
		"search_method": search_method,  # Which search method was used (vector/sparse/jsonl/fusion)
	}

	# Cache the result
	if use_cache and cache_key and not cache_hit:
		llm_cache.set(cache_key, json.dumps(result, ensure_ascii=False))

	return result


def remember(
	query: str,
	index_jsonl: Optional[str] = None,
	vec_db: Optional[str] = None,
	db_path: Optional[str] = None,
	k: int = 5,
	auto_index: bool = True,
	use_llm: bool = True,
	model: Optional[str] = None,
) -> Dict[str, Any]:
	"""Help recall forgotten things from chat history.
	
	Uses semantic search + optional LLM summarization to help remember
	things you discussed but forgot.
	"""
	# Find relevant conversations (use cache for search)
	solution_results = find_solution(query, index_jsonl, vec_db, db_path, k=k*2, auto_index=auto_index, use_cache=True)

	if "error" in solution_results:
		return solution_results

	results = solution_results.get("results", [])
	if not results:
		return {
			"query": query,
			"message": "No relevant conversations found.",
			"results": [],
		}

	# If LLM available, generate a memory summary (cached)
	memory_summary = None
	memory_cache_hit = False
	if use_llm and results:
		# Build cache key from query and top results (normalize query)
		query_normalized = query.strip()[:1000]
		# Sort result IDs for consistent cache keys
		result_ids = sorted([f"{r.get('composer_id')}:{r.get('turn_index')}" for r in results[:5]])
		cache_key = _cache_key("remember", query_normalized, model or "default", *result_ids)

		# Try cache first
		cached = llm_cache.get(cache_key)
		if cached:
			try:
				memory_summary = json.loads(cached)
				memory_cache_hit = True
			except Exception:
				pass

		# Generate if not cached
		if not memory_summary:
			try:
				client = llmmod.require_client()
				model = model or os.getenv("OPENAI_SMALL_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

				# Build context from top results (limit context size to avoid token limits)
				context_parts = []
				total_length = 0
				max_context_length = 4000  # Limit context to avoid token limits
				for r in results[:5]:
					user_head = (r.get('user_head') or '')[:200]
					assistant_head = (r.get('assistant_head') or '')[:300]
					part = f"Conversation {r['composer_id'][:8]}... (turn {r.get('turn_index', '?')}):\nUser: {user_head}\nAssistant: {assistant_head}"
					if total_length + len(part) > max_context_length:
						break
					context_parts.append(part)
					total_length += len(part)
				context = "\n\n".join(context_parts)

				prompt = f"""You discussed the following topic in past conversations. Help recall what was discussed:

Topic: {query}

Relevant conversation excerpts:
{context}

Provide a concise summary of what was discussed, key points, and any decisions made. Format as JSON with keys: summary, key_points (array), decisions (array), related_topics (array)."""

				# Handle different client types (OpenAI, Anthropic, etc.)
				if hasattr(client, "chat") and hasattr(client.chat, "completions"):
					# OpenAI/Groq/OpenRouter style
					resp = client.chat.completions.create(
						model=model,
						messages=[
							{"role": "system", "content": "You help recall information from past conversations. Return valid JSON only."},
							{"role": "user", "content": prompt},
						],
						temperature=0.3,
						timeout=30.0,
					)
					text = resp.choices[0].message.content or "{}"
					# Cache the result
					usage = getattr(resp, "usage", None)
					llm_cache.set(
						cache_key,
						text,
						prompt_tokens=usage.prompt_tokens if usage else None,
						completion_tokens=usage.completion_tokens if usage else None,
						total_tokens=usage.total_tokens if usage else None,
					)
				elif hasattr(client, "messages") and hasattr(client.messages, "create"):
					# Anthropic style
					resp = client.messages.create(
						model=model,
						max_tokens=1024,
						system="You help recall information from past conversations. Return valid JSON only.",
						messages=[{"role": "user", "content": prompt}],
						timeout=30.0,
					)
					text = resp.content[0].text if resp.content else "{}"
					# Cache the result
					usage = getattr(resp, "usage", None)
					llm_cache.set(
						cache_key,
						text,
						prompt_tokens=usage.input_tokens if usage else None,
						completion_tokens=usage.output_tokens if usage else None,
						total_tokens=(usage.input_tokens + usage.output_tokens) if usage else None,
					)
				else:
					# Fallback for other client types
					text = "{}"

				try:
					memory_summary = json.loads(text)
				except Exception:
					memory_summary = {"raw": text}
			except Exception as e:
				memory_summary = {"error": str(e)}

	result = {
		"query": query,
		"results": results[:k],
		"memory_summary": memory_summary,
		"count": len(results),
		"memory_cache_hit": memory_cache_hit,
	}
	if search_method:
		result["search_method"] = search_method
	return result


def find_design_plans(
	index_jsonl: Optional[str] = None,
	vec_db: Optional[str] = None,
	db_path: Optional[str] = None,
	topics: Optional[List[str]] = None,
	auto_index: bool = True,
	use_llm: bool = True,
	model: Optional[str] = None,
) -> Dict[str, Any]:
	"""Find and organize scattered design plans/wants from conversations.
	
	Looks for design discussions, plans, "I want to", "we should", etc.
	"""
	# Search queries for design-related content
	design_queries = [
		"design plan",
		"architecture decision",
		"we should",
		"I want to",
		"future plan",
		"roadmap",
		"design pattern",
		"system design",
	]

	if topics:
		design_queries.extend([f"{topic} design" for topic in topics])

	# Find all design-related conversations (use cache for individual queries)
	# Deduplicate queries to avoid redundant searches
	unique_queries = list(dict.fromkeys(design_queries))  # Preserves order, removes duplicates
	all_results: Dict[str, List[Dict]] = {}
	for query in unique_queries:
		# Use cache for individual queries to speed up design-coherence
		results = find_solution(query, index_jsonl, vec_db, db_path, k=10, auto_index=auto_index, use_cache=True)
		if "results" in results:
			for r in results["results"]:
				cid = r.get("composer_id")
				if cid:
					all_results.setdefault(cid, []).append(r)

	# Deduplicate and organize by conversation (more efficient deduplication)
	organized: List[Dict] = []
	for cid, results in all_results.items():
		# Get unique turns (deduplicate by turn_index)
		turn_dict = {}
		for r in results:
			tidx = r.get("turn_index")
			if tidx is not None and tidx not in turn_dict:
				turn_dict[tidx] = r
		turns = list(turn_dict.values())[:5]  # Top 5 turns per conversation
		if turns:  # Only add if there are turns
			organized.append({
				"composer_id": cid,
				"design_mentions": len(turns),
				"turns": turns,
			})

	# Sort by number of design mentions
	organized.sort(key=lambda x: x["design_mentions"], reverse=True)

	# If LLM available, generate coherence summary (cached)
	coherence_summary = None
	coherence_cache_hit = False
	if use_llm and organized:
		# Build cache key from topics and top conversations (normalize topics)
		topics_normalized = sorted([str(t).strip()[:100] for t in (topics or [])])  # Sort for consistency
		conv_ids = sorted([c.get("composer_id") for c in organized[:10]])  # Sort for consistency
		cache_key = _cache_key("design-coherence", model or "default", *topics_normalized, *conv_ids)

		# Try cache first
		cached = llm_cache.get(cache_key)
		if cached:
			try:
				coherence_summary = json.loads(cached)
				coherence_cache_hit = True
			except Exception:
				pass

		# Generate if not cached
		if not coherence_summary:
			try:
				client = llmmod.require_client()
				model = model or os.getenv("OPENAI_SMALL_MODEL", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

				# Build context from top conversations (limit context size to avoid token limits)
				context_parts = []
				total_length = 0
				max_context_length = 6000  # Limit context to avoid token limits
				for conv in organized[:10]:
					turns_text = "\n".join([
						f"Turn {t.get('turn_index')}: {(t.get('user_head') or '')[:150]}"
						for t in conv.get("turns", [])[:3]
					])
					part = f"Conversation {conv['composer_id'][:8]}...:\n{turns_text}"
					if total_length + len(part) > max_context_length:
						break
					context_parts.append(part)
					total_length += len(part)

				context = "\n\n---\n\n".join(context_parts)

				prompt = f"""You found scattered design plans and wants across multiple conversations. Organize them into a coherent design document.

Design-related conversations:
{context}

Extract and organize:
1. Main design themes/goals
2. Specific plans mentioned
3. Architecture decisions
4. Future wants/ideas
5. Potential conflicts or contradictions

Format as JSON with keys: themes (array), plans (array of {{topic, description, conversations}}), decisions (array), wants (array), conflicts (array)."""

				if hasattr(client, "chat") and hasattr(client.chat, "completions"):
					resp = client.chat.completions.create(
						model=model,
						messages=[
							{"role": "system", "content": "You organize scattered design discussions into coherent plans. Return valid JSON only."},
							{"role": "user", "content": prompt},
						],
						temperature=0.3,
					)
					text = resp.choices[0].message.content or "{}"
					# Cache the result
					usage = getattr(resp, "usage", None)
					llm_cache.set(
						cache_key,
						text,
						prompt_tokens=usage.prompt_tokens if usage else None,
						completion_tokens=usage.completion_tokens if usage else None,
						total_tokens=usage.total_tokens if usage else None,
					)
				else:
					text = "{}"

				try:
					coherence_summary = json.loads(text)
				except Exception:
					coherence_summary = {"raw": text}
			except Exception as e:
				coherence_summary = {"error": str(e)}

	return {
		"conversations": organized,
		"total_conversations": len(organized),
		"coherence_summary": coherence_summary,
		"coherence_cache_hit": coherence_cache_hit,
	}

