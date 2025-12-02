# Dependency Installation

This project depends on two local packages that need to be installed separately:

## Required Dependencies

1. **multiscale**: Available on GitHub
   ```bash
   # Option 1: Install from GitHub (recommended for public use)
   uv pip install git+https://github.com/arclabs561/multiscale.git
   
   # Option 2: Install locally (for development)
   uv pip install -e ../multiscale
   ```

2. **llm-helpers**: Currently local-only, needs to be published
   ```bash
   # For now, install locally (for development)
   uv pip install -e ../llm-helpers
   
   # TODO: Once published, use:
   # uv pip install git+https://github.com/user/llm-helpers.git
   ```

## Installation Steps

```bash
# Clone the repository
git clone <repo-url>
cd agent-explorer

# Install main dependencies
uv sync --all-extras --dev

# Install local dependencies (choose one method above)
uv pip install git+https://github.com/arclabs561/multiscale.git
uv pip install -e ../llm-helpers  # Or publish llm-helpers first
```

## Development Setup

For local development with all dependencies:

```bash
# Install main project
uv sync --all-extras --dev

# Install local packages in editable mode
uv pip install -e ../multiscale -e ../llm-helpers
```

