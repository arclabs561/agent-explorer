# Public Release Checklist

##  CRITICAL - Must Fix Before Public Release

### 1. Hardcoded Local Paths
- [x] **FIXED**: Removed hardcoded `file:///Users/arc/...` paths from `pyproject.toml`
- [ ] **TODO**: Decide on dependency strategy:
  - Option A: Publish `multiscale` and `llm-helpers` to PyPI
  - Option B: Use git URLs in dependencies
  - Option C: Include as git submodules
  - Option D: Document manual installation in README

### 2. Personal Directories
- [ ] **TODO**: Remove or gitignore `dotfiles/` directory (contains personal config)
- [ ] **TODO**: Remove or gitignore `bin/` directory (personal scripts)
- [ ] **TODO**: Verify these are not tracked: `git ls-files | grep -E "^(dotfiles|bin)/"`

### 3. Sensitive Files
- [x] **FIXED**: Updated `.gitignore` to exclude:
  - `cursor_index.jsonl`
  - `cursor_vec.db`
  - `cursor_items.db`
  - `.env*` files
  - `dotfiles/` and `bin/` directories
- [ ] **TODO**: Verify no sensitive files are tracked: `git ls-files | grep -E "(\.env|\.db|\.sqlite)"`

### 4. Large External Dependencies
- [ ] **TODO**: Decide on `cognee/` directory:
  - Option A: Make it a proper git submodule
  - Option B: Remove it (if not needed for this repo)
  - Option C: Document it as optional external dependency

### 5. Duplicate/Temporary Files
- [ ] **TODO**: Remove duplicate files:
  - `src/cursor_explorer/memory 2.py`
  - `src/cursor_explorer/db 2.py`
  - Any other `* 2.*` files

##  WARNINGS - Review Before Release

### 6. Internal Documentation
- [ ] **REVIEW**: Consider if these should be public:
  - `CHONKIE_ASSESSMENT.md` - Internal assessment
  - `USECASE_ANALYSIS.md` - Internal analysis
  - `WEAK_POINTS_ANALYSIS.md` - Internal notes
  - `IMPROVEMENTS.md` - Development notes
  - `SECURITY_REVIEW.md` - May contain sensitive info
  - `REPO_CLEANUP_PLAN.md` - Internal planning
  - `DOTFILES_SYNC_PLAN.md` - Personal planning
  - `GIT_HISTORY_CLEANUP.md` - Internal notes
  - `URGENT_DOTFILES_FIX.md` - Personal notes

### 7. Submodules
- [ ] **VERIFY**: Check if `cognee` should be a submodule:
  - `git submodule status`
  - If yes, add to `.gitmodules`
  - If no, remove or gitignore

### 8. Git History
- [ ] **REVIEW**: Check commit history for sensitive info:
  - `git log --all --full-history --source -- "*env*" "*key*" "*secret*"`
  - Consider using `git filter-repo` if needed

##  GOOD - Already Handled

- `.gitignore` covers sensitive file patterns
- No API keys found in tracked code (only in env vars)
- Test files use `.env.example` templates
- README is appropriate for public release

##  Recommended Actions

1. **Immediate**: Fix `pyproject.toml` dependencies (DONE)
2. **Before Release**: Remove or gitignore `dotfiles/` and `bin/`
3. **Before Release**: Remove duplicate files
4. **Before Release**: Decide on `cognee/` submodule status
5. **Before Release**: Review internal .md files
6. **Before Release**: Test fresh clone works without local paths

##  Testing Before Release

```bash
# Test that repo can be cloned and set up
git clone <repo-url> test-clone
cd test-clone
uv sync --all-extras --dev
uv run pytest -q
```

