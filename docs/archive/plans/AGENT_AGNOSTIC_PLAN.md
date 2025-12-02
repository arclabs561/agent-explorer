# Agent-Agnostic Refactoring Plan

## Research Findings

### Key Patterns for Agent-Agnostic Tools

1. **MCP (Model Context Protocol)** - Standard protocol for agent integration
   - Enables dynamic capability discovery
   - Works with any MCP-compatible agent
   - Provides standardized interface

2. **Abstraction Layers**
   - Abstract agent-specific storage formats
   - Support multiple backends (Cursor, Cline, Aider, etc.)
   - Configuration-driven, not hardcoded

3. **Machine-Friendly CLI**
   - Structured output (JSON by default)
   - Explicit flags, no interactive prompts
   - Semantic exit codes
   - Stable API contracts

## Current Cursor-Specific Elements

### 1. Database Path Detection ✅ COMPLETE
- **File**: `src/agent_explorer/paths.py` (renamed)
- **Status**: Abstracted to support multiple agents via backend system
- **Implementation**: Uses `AgentBackend` abstraction with platform-specific paths

### 2. Table Names ✅ COMPLETE
- **Status**: Table names are configurable per agent via backend system
- **Implementation**: Each `AgentBackend` provides `get_table_name()` method

### 3. Naming ✅ COMPLETE
- **Status**: Package renamed to `agent_explorer`, CLI to `agent-explorer`
- **Implementation**: All references updated, backward compatibility aliases maintained

### 4. Environment Variables ✅ COMPLETE
- **Status**: Generic `AGENT_*` variables with `CURSOR_*` fallbacks for backward compatibility
- **Implementation**: Supports `AGENT_STATE_DB`, `AGENT_INDEX_JSONL`, `AGENT_VEC_DB` with legacy fallbacks

## Refactoring Strategy

### Phase 1: Abstract Storage Layer

Create agent backend abstraction:

```python
# src/agent_explorer/backends/base.py
class AgentBackend:
    def get_db_path(self) -> str:
        """Return path to agent's state database."""
        raise NotImplementedError
    
    def get_table_name(self) -> str:
        """Return name of key-value table."""
        raise NotImplementedError
    
    def get_agent_name(self) -> str:
        """Return agent identifier."""
        raise NotImplementedError

# src/agent_explorer/backends/cursor.py
class CursorBackend(AgentBackend):
    def get_db_path(self) -> str:
        # Current Cursor logic
    
    def get_table_name(self) -> str:
        return "cursorDiskKV"
    
    def get_agent_name(self) -> str:
        return "cursor"

# src/agent_explorer/backends/cline.py
class ClineBackend(AgentBackend):
    # Similar structure for Cline
```

### Phase 2: Configuration System

```python
# Support multiple agents via config
AGENT_BACKENDS = {
    "cursor": CursorBackend,
    "cline": ClineBackend,
    "aider": AiderBackend,
}

# Environment variable
AGENT_TYPE = os.getenv("AGENT_TYPE", "cursor")  # Default to cursor for backward compat
```

### Phase 3: Rename Package/CLI

- Package: `cursor_explorer` → `agent_explorer`
- CLI: `cursor-explorer` → `agent-explorer`
- Keep `cursor-explorer` as alias for backward compatibility

### Phase 4: MCP Integration

- Wrap as MCP server
- Expose tools via MCP protocol
- Enable discovery by any MCP-compatible agent

## Implementation Steps

1. ✅ **Create backend abstraction** (Phase 1) - COMPLETE
2. ✅ **Update paths.py** to use backend abstraction - COMPLETE
3. ✅ **Update CLI** to support `--agent` flag - COMPLETE
4. ✅ **Rename package** (with backward compat) - COMPLETE
5. ⏳ **Add MCP server** (optional, Phase 4) - PENDING
6. ✅ **Update documentation** - COMPLETE

## Backward Compatibility

- Keep `CURSOR_STATE_DB` env var working
- Keep `cursor-explorer` CLI name as alias
- Default to Cursor backend if no agent specified
- Gradual migration path

