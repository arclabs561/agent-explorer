import os
import sys
from typing import Optional

# Import backend system
from .backends import get_backend
_USE_AGENT_BACKEND = True


def default_db_path(agent_type: Optional[str] = None) -> str:
    """Return the default agent SQLite DB path.
    
    Supports multiple agents via backend system. Defaults to Cursor for backward compatibility.

    - Respects `CURSOR_STATE_DB` (or agent-specific env var) if set
    - Uses backend system for agent-specific path detection
    
    Args:
        agent_type: Agent identifier (e.g., 'cursor', 'cline'). 
                   Defaults to 'cursor' for backward compatibility.
    """
    if _USE_AGENT_BACKEND:
        try:
            backend = get_backend(agent_type)
            return backend.get_db_path()
        except (ValueError, ImportError):
            # Fall back to legacy Cursor implementation
            pass

    # Legacy Cursor-specific implementation (backward compatibility)
    # This fallback ensures compatibility if backend system fails
    env_override = os.getenv("CURSOR_STATE_DB")
    if env_override:
        return os.path.abspath(os.path.expanduser(os.path.expandvars(env_override)))

    # Use Cursor backend directly for legacy fallback
    try:
        from .backends.cursor import CursorBackend
        backend = CursorBackend()
        return backend.get_db_path()
    except Exception:
        # Ultimate fallback: hardcoded macOS path
        return os.path.expanduser(
            "~/Library/Application Support/Cursor/User/globalStorage/state.vscdb"
        )


def expand_abs(path: str) -> str:
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))
