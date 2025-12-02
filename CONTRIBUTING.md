# Contributing

Thank you for considering contributing to cursor-explorer!

## Development Setup

1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd cursor-explorer
   ```

2. Install dependencies:
   ```bash
   uv sync --all-extras --dev
   uv pip install git+https://github.com/arclabs561/multiscale.git
   uv pip install -e ../llm-helpers  # For local development
   ```

3. Run tests:
   ```bash
   uv run pytest
   ```

## Code Style

- Follow PEP 8
- Use `ruff` for linting: `uv run ruff check .`
- Maximum line length: 220 characters

## Submitting Changes

1. Create a feature branch
2. Make your changes
3. Run tests and linting
4. Submit a pull request

