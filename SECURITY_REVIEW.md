# Security Review & Publishing Recommendations

##  Red Team Security Review

### Files Created/Modified in This Session

1. **REPO_CLEANUP_PLAN.md** -  Safe (no secrets)
2. **VALIDATION_REPORT.md** -  Safe (no secrets)
3. **NAMING_RECOMMENDATIONS.md** -  Safe (no secrets)
4. **SECURITY_REVIEW.md** -  Safe (this file)
5. **data/README.md** -  Safe (documentation)
6. **cognee-storage/README.md** -  Safe (documentation)
7. **docs/archive/2025-11/README.md** -  Safe (documentation)
8. **.gitignore** -  Safe (patterns only)

###  Files with Personal Information

#### 1. dotfiles/home/.gitconfig
**Status**:  **CONTAINS PERSONAL INFO**
- Email: `henry@henrywallace.io`
- Name: `Henry Wallace`
- Absolute path: `/Users/arc/Documents/dev/devdev/dotfiles/misc/git-hooks`
- GitHub username: `henrywallace`

**Action Required**:
- **DO NOT PUBLISH** as-is
-  Template created: `.gitconfig.example`
- Remove personal info from template
- Document that users should copy and customize

#### 2. dotfiles/misc/systemd/user/up.service*
**Status**:  **CONTAINS HARDCODED PATHS**
- `/home/henrywallace/go/bin/notify`
- `/home/henrywallace/bin/upd`

**Action Required**:
- Replace with `$HOME` or environment variables
- Or exclude from public dotfiles repo

#### 3. bin/gp
**Status**:  **CONTAINS PERSONAL DOMAIN**
- `https://henrywallace.io`

**Action Required**:
- Replace with placeholder or config variable
- Or exclude from public repo

#### 4. bin/rmount
**Status**:  **CONTAINS HARDCODED PATH**
- `/home/henrywallace/mnt/`

**Action Required**:
- Replace with `$HOME/mnt/` or config variable
- Or exclude from public repo

#### 5. data/*.jsonl files
**Status**:  **SAFE** (gitignored)
- Contains email in chat data, but `data/` is gitignored
- No action needed

#### 2. dotfiles/home/.pathrc
**Status**:  **CONTAINS PATHS**
- Contains `$HOME` paths (OK, portable)
- No absolute paths found
- **May be safe** but review for personal paths

**Action Required**:
- Review for any hardcoded personal paths
- Ensure all paths use `$HOME` or environment variables

#### 3. dotfiles/home/.zshrc
**Status**:  **REVIEW NEEDED**
- Previously had hardcoded `/Users/henry/` paths (fixed)
- May contain other personal configurations

**Action Required**:
- Review for any remaining personal paths or configs
- Ensure all paths are portable

###  Safe to Publish

- `REPO_CLEANUP_PLAN.md`
- `VALIDATION_REPORT.md`
- `NAMING_RECOMMENDATIONS.md`
- `data/README.md`
- `cognee-storage/README.md`
- `docs/archive/2025-11/README.md`
- `.gitignore` (patterns only)
- `dotfiles/setup` (script, no secrets)
- `dotfiles/README.md`

## 📦 Publishing Recommendations

### cursor_explorer -  SHOULD BE PUBLISHED

**Status**: Ready for publication with minor cleanup

**What to Publish**:
- `src/` - Source code
- `tests/` - Tests
- `scripts/` - Build scripts
- `Justfile` - Task runner config
- `pyproject.toml` - Project config
- `README.md` - Documentation
- `pytest.ini` - Test config
- `docs/` - Documentation (excluding archive if sensitive)

**What NOT to Publish**:
- `data/` - Generated data (already gitignored)
- `logs/` - Logs (already gitignored)
- `cognee-storage/` - Cognee data (already gitignored)
- `.env` - Environment variables (already gitignored)
- `dotfiles/` - Personal config (see below)

**Pre-Publication Checklist**:
- [ ] Review all files for hardcoded paths
- [ ] Ensure no API keys or secrets
- [ ] Remove any personal information
- [ ] Verify `.gitignore` is comprehensive
- [ ] Test that sensitive files are ignored

### dotfiles -  EXISTING REPO: github.com/arclabs561/dotfiles

**Status**: Repository already exists on GitHub

**Current Situation**:
- Remote repo: `github.com/arclabs561/dotfiles` (exists)
- Local directory: `./dotfiles/` (in this repo)
- Need to verify if local matches remote or if they're separate

**Issues to Address**:
1. `.gitconfig` contains:
   - Personal email: `henry@henrywallace.io`
   - Personal name: `Henry Wallace`
   - Machine-specific paths

2. Other dotfiles may contain:
   - Personal aliases
   - Personal paths
   - Personal configurations

**Action Plan**:
1.  Template created: `.gitconfig.example`
2. Verify remote repo privacy status
3. Sync local dotfiles/ with remote repo (if needed)
4. Ensure personal info is appropriate for repo visibility
5. Review all dotfiles for personal info before syncing

**Recommended Structure**:
```
# Option A: If remote is private (recommended)
github.com/arclabs561/dotfiles (private)
├── home/
│   ├── .gitconfig          # Personal version (OK if private)
│   └── ...
└── ...

# Option B: If remote is public
github.com/arclabs561/dotfiles (public)
├── home/
│   ├── .gitconfig.example  # Template (sanitized)
│   └── ...                 # All personal info removed
└── ...
```

## 🔧 Git History Cleanup

### Current Status
- Repository may have messy history
- May contain sensitive commits
- Need to clean before publishing

### Options

#### Option A: Fresh Start (Recommended for Public)
```bash
# Create new repo with clean history
git checkout --orphan clean-main
git add .
git commit -m "Initial commit: cursor-explorer"
git branch -D main  # Delete old branch
git branch -m main  # Rename current to main
```

#### Option B: Interactive Rebase
```bash
# Clean up specific commits
git rebase -i HEAD~N  # N = number of commits to review
# Remove or squash commits with sensitive info
```

#### Option C: BFG Repo Cleaner
```bash
# Remove sensitive files from history
bfg --delete-files sensitive-file.txt
git reflog expire --expire=now --all
git gc --prune=now --aggressive
```

### Recommended Approach

1. **For cursor_explorer** (public):
   - Fresh start with clean history
   - Only include necessary files
   - Exclude dotfiles entirely

2. **For dotfiles** (private):
   - Keep existing history (if not too messy)
   - Or fresh start in separate private repo
   - Sanitize before any public sharing

## 🛡 Security Checklist

### Before Publishing cursor_explorer

- [ ] No API keys in code
- [ ] No hardcoded paths
- [ ] No personal information
- [ ] `.gitignore` comprehensive
- [ ] `.env` files ignored
- [ ] Test files don't contain secrets
- [ ] Documentation doesn't expose sensitive info
- [ ] Git history cleaned (if needed)

### Before Publishing dotfiles

- [ ] Personal email removed
- [ ] Personal name removed
- [ ] Machine-specific paths removed
- [ ] Personal aliases reviewed
- [ ] Credential helpers removed or templated
- [ ] All paths use variables (`$HOME`, etc.)
- [ ] Create `.example` templates for sensitive files

##  Next Steps

1. **Immediate**: 
   - Verify `github.com/arclabs561/dotfiles` privacy status
   - If private: Personal info is OK, can sync
   - If public: Must sanitize before syncing

2. **Dotfiles Sync**:
   - Check if local `./dotfiles/` matches remote
   - Decide: Keep in this repo or remove (use remote directly)
   - If keeping separate: Remove `dotfiles/` from cursor_explorer repo

3. **Before Publishing cursor_explorer**: 
   - Complete security checklist
   - Remove `dotfiles/` directory (or ensure it's gitignored)
   - Initialize git with clean history

4. **Git History**: 
   - Not a repo yet - can start fresh
   - See `GIT_HISTORY_CLEANUP.md` for steps

