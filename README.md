# Agent Explorer

CLI tool for exploring AI agent chat data.

## Install

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --all-extras --dev
uv pip install git+https://github.com/arclabs561/multiscale.git
uv pip install -e ../llm-helpers
```

Optional: rank-fusion and rank-refine (not on PyPI):
```bash
uv pip install -e ../rank-fusion/rank-fusion-python
uv pip install -e ../rank-refine/rank-refine-python
```

## Usage

```bash
uv run ae chats
uv run ae convo <composer_id>
uv run ae find-solution "query"
uv run ae remember "query"
uv run ae ensure-indexed
```

## Commands

Basic:
- `info` - Database info
- `chats` - List conversations
- `convo <id>` - Show conversation
- `keys [--prefix] [--like]` - List keys
- `show <key>` - Show key value

Search:
- `find-solution <query>` - Search conversation history
- `remember <query>` - Recall with optional LLM summarization
- `ensure-indexed` - Build indexes

Analysis:
- `pairs <id>` - Extract QA pairs
- `multiscale` - Hierarchical summarization
- `design-coherence` - Organize design plans

See `uv run agent-explorer --help` for all commands.

## Config

- `AGENT_TYPE` - Agent type (default: `cursor`)
- `AGENT_STATE_DB` / `CURSOR_STATE_DB` - Database path
- `AGENT_INDEX_JSONL` / `CURSOR_INDEX_JSONL` - Index path (default: `./cursor_index.jsonl`)
- `AGENT_VEC_DB` / `CURSOR_VEC_DB` - Vector DB path (default: `./cursor_vec.db`)
- `OPENAI_API_KEY` - Required for LLM features
- `OPENAI_MODEL` - Model (default: `gpt-4o-mini`)
- `OPENAI_EMBED_MODEL` - Embedding model (default: `text-embedding-3-small`)

## Features

- Agent-agnostic design (Cursor implemented, extensible for Cline/Aider)
- Multi-source search (vector + sparse, rank-fusion optional)
- Conversation recall (LLM summarization optional)
- Key-value access to agent databases
- Hierarchical summarization
- Idempotent indexing with caching
- Read-only database access

## Notes

- Commands output JSON (pipe to `jq` for formatting)
- Close agent before accessing database
