import os
from typing import Optional

from .backends import get_backend


def default_db_path(agent_type: Optional[str] = None) -> str:
    """Return the default agent SQLite DB path.
    
    Supports multiple agents via backend system. Defaults to Cursor for backward compatibility.

    - Respects `CURSOR_STATE_DB` (or agent-specific env var) if set
    - Uses backend system for agent-specific path detection
    
    Args:
        agent_type: Agent identifier (e.g., 'cursor', 'cline'). 
                   Defaults to 'cursor' for backward compatibility.
    
    Raises:
        ValueError: If backend system fails and no fallback available
    """
    try:
        backend = get_backend(agent_type)
        return backend.get_db_path()
    except (ValueError, ImportError) as e:
        # Backend system failed - try direct Cursor backend as fallback
        try:
            from .backends.cursor import CursorBackend
            backend = CursorBackend()
            return backend.get_db_path()
        except Exception:
            raise ValueError(
                f"Failed to determine database path for agent '{agent_type}'. "
                f"Set CURSOR_STATE_DB environment variable. "
                f"Error: {e}"
            ) from e


def expand_abs(path: str) -> str:
    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))
