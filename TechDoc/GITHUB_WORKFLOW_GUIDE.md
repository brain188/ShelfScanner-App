# ShelfScanner - GitHub Workflow Guide

**Complete Guide to Managing the Project with Git & GitHub**

Version: 1.0.0  
Last Updated: January 2024  
Team: ShelfScanner Engineering

---

## Table of Contents

1. [Branch Strategy](#1-branch-strategy)
2. [Commit Guidelines](#2-commit-guidelines)
3. [Pull Request Process](#3-pull-request-process)
4. [Code Review Guidelines](#4-code-review-guidelines)
5. [Merge Strategy](#5-merge-strategy)
6. [Release Process](#6-release-process)
7. [Hotfix Workflow](#7-hotfix-workflow)
8. [Git Best Practices](#8-git-best-practices)
9. [GitHub Actions & Automation](#9-github-actions--automation)
10. [Common Scenarios](#10-common-scenarios)
11. [Troubleshooting](#11-troubleshooting)
12. [Quick Reference](#12-quick-reference)

---

# 1. Branch Strategy

## 1.1 Branch Structure

```
main (production)
  ↑
staging (pre-production)
  ↑
develop (integration)
  ↑
feature/* (feature development)
bugfix/* (bug fixes)
hotfix/* (production fixes)
```

### Branch Purposes

| Branch | Purpose | Deploy Target | Protection |
|--------|---------|--------------|------------|
| **main** | Production-ready code | Production | ✅ Protected |
| **staging** | Pre-production testing | Staging server | ✅ Protected |
| **develop** | Integration branch | Development server | ✅ Protected |
| **feature/*** | New features | Local/Dev | ❌ Not protected |
| **bugfix/*** | Bug fixes | Local/Dev | ❌ Not protected |
| **hotfix/*** | Urgent production fixes | Production | ⚠️ Fast-track |

## 1.2 Branch Naming Conventions

### Feature Branches
```bash
feature/user-authentication
feature/book-scanning
feature/ai-recommendations
feature/JIRA-123-user-profile

# Format: feature/<brief-description>
# Or:     feature/<ticket-number>-<brief-description>
```

### Bugfix Branches
```bash
bugfix/fix-ocr-timeout
bugfix/resolve-login-error
bugfix/JIRA-456-scan-upload

# Format: bugfix/<brief-description>
# Or:     bugfix/<ticket-number>-<brief-description>
```

### Hotfix Branches
```bash
hotfix/critical-auth-bug
hotfix/database-connection-leak
hotfix/v1.2.1

# Format: hotfix/<critical-issue>
# Or:     hotfix/v<version>
```

### Release Branches (Optional)
```bash
release/v1.0.0
release/v1.1.0

# Format: release/v<version>
```

## 1.3 Initial Repository Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/shelfscanner.git
cd shelfscanner

# Set up all branches
git checkout -b develop
git push -u origin develop

git checkout -b staging
git push -u origin staging

git checkout -b main
git push -u origin main

# Set default branch to develop in GitHub Settings
```

## 1.4 Branch Protection Rules

### On GitHub: Settings → Branches → Add Rule

**For `main` branch:**
```yaml
Branch name pattern: main

Settings:
  ✅ Require pull request before merging
    ✅ Require approvals (minimum: 2)
    ✅ Dismiss stale pull request approvals
    ✅ Require review from Code Owners
  ✅ Require status checks to pass
    - CI/CD Pipeline
    - Tests
    - Code Coverage
    - Linting
  ✅ Require conversation resolution
  ✅ Require signed commits (recommended)
  ✅ Include administrators
  ✅ Restrict pushes
  ✅ Allow force pushes: NO
  ✅ Allow deletions: NO
```

**For `staging` branch:**
```yaml
Branch name pattern: staging

Settings:
  ✅ Require pull request before merging
    ✅ Require approvals (minimum: 1)
  ✅ Require status checks to pass
    - CI/CD Pipeline
    - Tests
  ✅ Include administrators
  ✅ Allow force pushes: NO
```

**For `develop` branch:**
```yaml
Branch name pattern: develop

Settings:
  ✅ Require pull request before merging
    ✅ Require approvals (minimum: 1)
  ✅ Require status checks to pass
    - Tests
  ✅ Allow force pushes: NO
```

---

# 2. Commit Guidelines

## 2.1 Commit Message Format

We follow the **Conventional Commits** specification.

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Example
```
feat(auth): add JWT token refresh mechanism

Implement automatic token refresh to improve user experience.
Tokens are now refreshed 5 minutes before expiry.

Closes #123
```

## 2.2 Commit Types

| Type | Description | Example |
|------|-------------|---------|
| **feat** | New feature | `feat(books): add book search functionality` |
| **fix** | Bug fix | `fix(ocr): resolve timeout error` |
| **docs** | Documentation | `docs(api): update endpoint documentation` |
| **style** | Code style (formatting) | `style: format code with black` |
| **refactor** | Code refactoring | `refactor(auth): simplify JWT validation` |
| **perf** | Performance improvement | `perf(db): optimize book query with index` |
| **test** | Add/update tests | `test(scan): add unit tests for OCR service` |
| **build** | Build system changes | `build: update dependencies` |
| **ci** | CI/CD changes | `ci: add deployment workflow` |
| **chore** | Maintenance tasks | `chore: update .gitignore` |
| **revert** | Revert previous commit | `revert: revert "feat(auth): add OAuth"` |

## 2.3 Commit Scope

Scopes help identify which part of the codebase is affected:

```
auth       - Authentication & authorization
books      - Book management
scan       - OCR and scanning
recommendations - Recommendation engine
api        - API endpoints
db         - Database
models     - Data models
services   - Service layer
utils      - Utilities
tests      - Testing
docs       - Documentation
config     - Configuration
ci         - CI/CD
```

## 2.4 Good Commit Examples

✅ **GOOD:**
```bash
feat(scan): add support for batch scanning
fix(auth): resolve token expiration bug
docs(api): add authentication examples
test(books): increase coverage to 90%
perf(db): add index on books.user_id
refactor(ocr): extract text cleaning logic
```

❌ **BAD:**
```bash
update stuff
fixed bug
changes
WIP
asdf
quick fix
```

## 2.5 Commit Best Practices

### Write Atomic Commits
```bash
# ✅ Good - One logical change
git commit -m "feat(auth): add login endpoint"

# ❌ Bad - Multiple unrelated changes
git commit -m "add login, fix bug, update docs"
```

### Write Meaningful Messages
```bash
# ✅ Good
git commit -m "fix(ocr): handle timeout errors gracefully

Added retry logic with exponential backoff.
Increased timeout from 10s to 15s.

Fixes #456"

# ❌ Bad
git commit -m "fix stuff"
```

### Keep Commits Small
```bash
# ✅ Good - Small, focused commits
git commit -m "feat(auth): add user model"
git commit -m "feat(auth): add login endpoint"
git commit -m "test(auth): add login tests"

# ❌ Bad - One massive commit
git commit -m "feat(auth): complete authentication system"
```

## 2.6 Practical Commit Workflow

```bash
# 1. Make changes to files
vim app/api/v1/auth.py

# 2. Check what changed
git status
git diff

# 3. Stage specific files
git add app/api/v1/auth.py

# 4. Review staged changes
git diff --staged

# 5. Commit with message
git commit -m "feat(auth): add logout endpoint"

# 6. Or use interactive commit
git commit
# Opens editor for detailed message

# 7. Push to remote
git push origin feature/user-authentication
```

## 2.7 Amending Commits

```bash
# Forgot to add a file?
git add forgotten_file.py
git commit --amend --no-edit

# Want to change commit message?
git commit --amend -m "feat(auth): add logout endpoint with session cleanup"

# ⚠️ WARNING: Only amend commits that haven't been pushed!
# If already pushed, you'll need to force push:
git push --force-with-lease origin feature/your-branch
```

---

# 3. Pull Request Process

## 3.1 Creating a Pull Request

### Step 1: Ensure Your Branch is Up-to-Date

```bash
# Switch to your feature branch
git checkout feature/user-authentication

# Fetch latest changes
git fetch origin

# Rebase on develop (or merge if preferred)
git rebase origin/develop

# Or merge if you prefer
# git merge origin/develop

# Push your branch
git push origin feature/user-authentication
```

### Step 2: Create PR on GitHub

1. **Go to GitHub Repository**
   - Navigate to your repository
   - Click "Pull requests" tab
   - Click "New pull request"

2. **Select Branches**
   ```
   base: develop  ←  compare: feature/user-authentication
   ```

3. **Fill Out PR Template**

## 3.2 Pull Request Template

Create `.github/PULL_REQUEST_TEMPLATE.md`:

```markdown
## Description
<!-- Provide a detailed description of your changes -->

## Type of Change
<!-- Mark with an X -->
- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🎨 Style update (formatting, renaming)
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] ✅ Test update
- [ ] 🔧 Build configuration change

## Related Issues
<!-- Link to related issues -->
Closes #issue_number
Relates to #issue_number

## Changes Made
<!-- List the specific changes -->
- Added login endpoint
- Implemented JWT token generation
- Added authentication middleware
- Updated API documentation

## Testing
<!-- Describe the tests you ran -->
- [ ] Unit tests pass (`pytest`)
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Code coverage maintained/improved

## Screenshots (if applicable)
<!-- Add screenshots for UI changes -->

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Additional Notes
<!-- Any additional information -->
```

## 3.3 PR Naming Convention

```
feat(auth): implement JWT authentication
fix(ocr): resolve timeout issue in batch processing
docs(api): add authentication examples
perf(db): optimize book queries with composite index
```

## 3.4 PR Labels

Create these labels in GitHub (Settings → Labels):

| Label | Color | Description |
|-------|-------|-------------|
| `bug` 🐛 | #d73a4a | Something isn't working |
| `feature` ✨ | #a2eeef | New feature or request |
| `documentation` 📝 | #0075ca | Documentation improvements |
| `enhancement` ⚡ | #a2eeef | Improvement to existing feature |
| `critical` 🚨 | #b60205 | Critical issue, needs immediate attention |
| `high priority` 🔴 | #d93f0b | High priority |
| `medium priority` 🟡 | #fbca04 | Medium priority |
| `low priority` 🟢 | #0e8a16 | Low priority |
| `needs review` 👀 | #fbca04 | Needs code review |
| `work in progress` 🚧 | #ffcc00 | Work in progress |
| `ready to merge` ✅ | #0e8a16 | Approved and ready to merge |
| `do not merge` ⛔ | #b60205 | Do not merge |
| `breaking change` 💥 | #d73a4a | Breaking change |
| `dependencies` 📦 | #0366d6 | Dependency updates |
| `security` 🔒 | #ee0701 | Security-related |

## 3.5 PR Workflow States

```
Draft → Open → In Review → Changes Requested → Approved → Merged
         ↓                      ↓
      Closed               Update & Review
```

### Draft PR
```bash
# Create a draft PR for early feedback
# On GitHub: Click "Create draft pull request"
# Or use GitHub CLI:
gh pr create --draft --base develop --head feature/my-feature
```

### Converting Draft to Ready
```bash
# When ready for formal review
# On GitHub: Click "Ready for review"
# Or use CLI:
gh pr ready
```

## 3.6 PR Size Guidelines

| Size | Files Changed | Lines Changed | Review Time |
|------|---------------|---------------|-------------|
| **XS** | 1-5 | <50 | < 15 min |
| **S** | 5-10 | 50-200 | < 30 min |
| **M** | 10-20 | 200-500 | 1-2 hours |
| **L** | 20-50 | 500-1000 | 2-4 hours |
| **XL** | 50+ | 1000+ | 4+ hours |

**Recommendation:** Keep PRs **Small to Medium** for faster reviews!

### Breaking Down Large Changes

```bash
# ❌ Bad - One massive PR
git checkout -b feature/complete-authentication
# ... 50 files changed, 2000 lines

# ✅ Good - Multiple focused PRs
git checkout -b feature/auth-models
# PR 1: Add user models (5 files, 200 lines)

git checkout -b feature/auth-endpoints
# PR 2: Add auth endpoints (8 files, 300 lines)

git checkout -b feature/auth-middleware
# PR 3: Add middleware (3 files, 100 lines)
```

---

# 4. Code Review Guidelines

## 4.1 For PR Authors

### Before Requesting Review

```bash
# 1. Self-review your code
git diff develop...HEAD

# 2. Run tests locally
pytest
pytest --cov=app

# 3. Run linters
black app/
flake8 app/
mypy app/

# 4. Update documentation
# Edit relevant .md files

# 5. Check for sensitive data
git diff | grep -i "password\|secret\|key"
```

### Responding to Review Comments

✅ **Do:**
- Thank reviewers for their time
- Ask for clarification if needed
- Implement reasonable suggestions
- Explain your reasoning for disagreements
- Mark conversations as resolved when addressed

❌ **Don't:**
- Argue defensively
- Ignore review comments
- Make changes without discussion
- Take criticism personally

### Example Responses

```markdown
# ✅ Good Response
Thanks for catching that! You're right, this could cause a race condition.
I've updated the code to use a transaction lock.

# ✅ Good Question
Interesting point about performance. I chose this approach because...
What are your thoughts on using caching instead?

# ❌ Bad Response
This works fine, I don't see the problem.
```

## 4.2 For Reviewers

### Review Checklist

```markdown
## Code Quality
- [ ] Code is readable and well-structured
- [ ] No unnecessary complexity
- [ ] Follows project style guidelines
- [ ] No duplicated code
- [ ] Proper error handling

## Functionality
- [ ] Solves the stated problem
- [ ] No obvious bugs
- [ ] Edge cases handled
- [ ] Backward compatible (or breaking change documented)

## Testing
- [ ] Tests included for new features
- [ ] Tests cover edge cases
- [ ] All tests pass
- [ ] Code coverage maintained

## Security
- [ ] No security vulnerabilities
- [ ] Input validation present
- [ ] No sensitive data logged
- [ ] Authentication/authorization correct

## Performance
- [ ] No obvious performance issues
- [ ] Database queries optimized
- [ ] No N+1 queries
- [ ] Appropriate caching

## Documentation
- [ ] Code comments for complex logic
- [ ] API documentation updated
- [ ] README updated if needed
- [ ] CHANGELOG updated
```

### Review Comments Types

#### Request Changes
```markdown
🚨 **Request Changes:**

The timeout value of 5 seconds is too low for batch processing.
This will cause failures for large scans.

**Suggestion:** Increase to at least 30 seconds or make it configurable.

```python
# Instead of:
TIMEOUT = 5

# Consider:
TIMEOUT = os.getenv("SCAN_TIMEOUT", 30)
```
```

#### Suggestion (Non-blocking)
```markdown
💡 **Suggestion:**

Consider extracting this logic into a separate function for reusability.

```python
def validate_book_data(book_data: dict) -> bool:
    # validation logic here
    pass
```

Feel free to address this in a follow-up PR if you prefer.
```

#### Question
```markdown
❓ **Question:**

Why are we using sync code here instead of async?
Is there a specific reason, or could we make this async for better performance?
```

#### Praise
```markdown
✨ **Great work!**

Love how you handled the edge case for empty book titles.
The error message is very clear.
```

### Review Response Time

| Priority | Response Time |
|----------|---------------|
| **Critical/Hotfix** | < 2 hours |
| **High Priority** | < 4 hours |
| **Normal** | < 24 hours |
| **Low Priority** | < 48 hours |

## 4.3 Review Workflow

```bash
# 1. Checkout the PR branch locally
gh pr checkout 123

# Or manually:
git fetch origin
git checkout -b review/pr-123 origin/feature/user-authentication

# 2. Review the changes
git log develop..HEAD
git diff develop...HEAD

# 3. Test locally
pytest
python -m app.main

# 4. Leave review on GitHub
# Go to "Files changed" tab
# Add comments
# Submit review (Approve / Request Changes / Comment)
```

---

# 5. Merge Strategy

## 5.1 Merge Types

### Squash and Merge (Recommended for `feature/*` → `develop`)

**When to use:** Most feature branches

**Advantages:**
- Clean, linear history
- One commit per feature
- Easy to revert

```bash
# On GitHub: "Squash and merge" button

# Result:
feat(auth): implement user authentication (#123)

* Added login endpoint
* Added JWT token generation  
* Added authentication middleware
* Updated documentation
```

### Rebase and Merge (For `develop` → `staging` → `main`)

**When to use:** Promoting between main branches

**Advantages:**
- Linear history
- Preserves individual commits
- Clear commit trail

```bash
# On GitHub: "Rebase and merge" button

# Or manually:
git checkout staging
git rebase develop
git push origin staging
```

### Merge Commit (For `hotfix/*`)

**When to use:** Hotfixes, important to track the merge

**Advantages:**
- Preserves branch history
- Shows when hotfix was applied

```bash
# On GitHub: "Create a merge commit" button

# Or manually:
git checkout main
git merge --no-ff hotfix/critical-bug
git push origin main
```

## 5.2 Merge Workflow

### Feature → Develop

```bash
# 1. Ensure feature branch is up-to-date
git checkout feature/user-authentication
git fetch origin
git rebase origin/develop

# 2. Push (may need force push after rebase)
git push origin feature/user-authentication --force-with-lease

# 3. Create PR on GitHub
# 4. Get approval
# 5. Click "Squash and merge"
# 6. Delete feature branch

# Or via CLI:
gh pr merge 123 --squash --delete-branch
```

### Develop → Staging

```bash
# 1. Ensure develop is stable
# All tests pass, no known issues

# 2. Create PR: develop → staging
gh pr create --base staging --head develop \
  --title "Release v1.2.0 to staging" \
  --body "Deploying new features to staging for testing"

# 3. After approval, rebase and merge
gh pr merge 456 --rebase

# 4. Verify staging deployment
# Check staging server, run smoke tests
```

### Staging → Main (Production)

```bash
# 1. Verify staging is stable
# Complete QA testing
# Stakeholder approval

# 2. Create PR: staging → main
gh pr create --base main --head staging \
  --title "Release v1.2.0 to production" \
  --body "Deploying v1.2.0 to production. All tests pass."

# 3. After approvals (2+), rebase and merge
gh pr merge 789 --rebase

# 4. Tag the release
git checkout main
git pull origin main
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0

# 5. Create GitHub Release
gh release create v1.2.0 \
  --title "v1.2.0 - User Authentication" \
  --notes "Release notes here"
```

## 5.3 Merge Conflicts

### Prevention
```bash
# Keep your branch updated
git checkout feature/my-feature
git fetch origin
git rebase origin/develop
```

### Resolution
```bash
# When conflict occurs during rebase
git rebase origin/develop

# Git will pause and show conflicts
# CONFLICT (content): Merge conflict in app/api/v1/auth.py

# 1. Open conflicted files
vim app/api/v1/auth.py

# 2. Resolve conflicts (look for <<<<<<, =======, >>>>>>>)
# Keep what you need, remove markers

# 3. Stage resolved files
git add app/api/v1/auth.py

# 4. Continue rebase
git rebase --continue

# Or abort if needed
git rebase --abort
```

### Example Conflict Resolution

```python
# <<<<<<< HEAD (develop)
def login(email: str, password: str):
    user = get_user(email)
    if not user:
        raise ValueError("User not found")
# =======
def login(email: str, password: str):
    user = authenticate(email, password)
    if not user:
        return None
# >>>>>>> feature/my-branch

# After resolution:
def login(email: str, password: str):
    """Authenticate user with email and password."""
    user = authenticate(email, password)
    if not user:
        raise ValueError("Invalid credentials")
    return user
```

---

# 6. Release Process

## 6.1 Semantic Versioning

We follow [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

Example: v1.2.3
```

- **MAJOR** (1.x.x): Breaking changes
- **MINOR** (x.2.x): New features (backward compatible)
- **PATCH** (x.x.3): Bug fixes (backward compatible)

### Examples

```
v1.0.0 → v1.1.0  # Added book recommendations (new feature)
v1.1.0 → v1.1.1  # Fixed OCR timeout bug (bugfix)
v1.1.1 → v2.0.0  # Changed API response format (breaking change)
```

## 6.2 Release Checklist

```markdown
## Pre-Release
- [ ] All features merged to develop
- [ ] All tests passing
- [ ] Code coverage > 80%
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in code

## Staging Deployment
- [ ] Merge develop → staging
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] QA testing completed
- [ ] Performance tests passed
- [ ] Security scan completed

## Production Deployment
- [ ] Stakeholder approval
- [ ] Backup database
- [ ] Merge staging → main
- [ ] Create git tag
- [ ] Deploy to production
- [ ] Run smoke tests
- [ ] Monitor for 30 minutes
- [ ] Create GitHub Release
- [ ] Announce release

## Post-Release
- [ ] Update documentation site
- [ ] Notify users (if applicable)
- [ ] Monitor error rates
- [ ] Check performance metrics
- [ ] Plan next release
```

## 6.3 Creating a Release

### Step 1: Update Version

```python
# app/__init__.py
__version__ = "1.2.0"
```

```yaml
# docker-compose.yml
services:
  api:
    image: shelfscanner/api:1.2.0
```

### Step 2: Update CHANGELOG.md

```markdown
# Changelog

## [1.2.0] - 2024-02-01

### Added
- JWT token refresh mechanism
- Book batch upload feature
- AI-powered recommendations

### Changed
- Improved OCR accuracy by 15%
- Updated API response format for books

### Fixed
- Resolved timeout issue in batch scanning
- Fixed authentication token expiration bug

### Security
- Updated dependencies with security patches
```

### Step 3: Commit and Tag

```bash
# Commit version changes
git checkout staging
git add app/__init__.py CHANGELOG.md docker-compose.yml
git commit -m "chore: bump version to v1.2.0"
git push origin staging

# After merge to main
git checkout main
git pull origin main

# Create annotated tag
git tag -a v1.2.0 -m "Release v1.2.0 - Enhanced Authentication"

# Push tag
git push origin v1.2.0
```

### Step 4: Create GitHub Release

```bash
# Using GitHub CLI
gh release create v1.2.0 \
  --title "v1.2.0 - Enhanced Authentication" \
  --notes-file RELEASE_NOTES.md \
  --latest

# Or manually on GitHub:
# Go to Releases → Draft a new release
# Choose tag v1.2.0
# Add release notes
# Publish release
```

## 6.4 Release Notes Template

```markdown
# ShelfScanner v1.2.0

## 🎉 Highlights

This release brings enhanced authentication with JWT token refresh and improved OCR accuracy.

## ✨ New Features

- **JWT Token Refresh**: Automatic token refresh for better UX (#123)
- **Batch Upload**: Upload multiple book images at once (#145)
- **AI Recommendations**: Personalized book recommendations (#167)

## 🐛 Bug Fixes

- Fixed OCR timeout in batch processing (#178)
- Resolved authentication token expiration issue (#182)
- Fixed book search pagination (#190)

## ⚡ Improvements

- Improved OCR accuracy by 15%
- Reduced API response time by 20%
- Enhanced error messages

## 🔒 Security

- Updated dependencies with security patches
- Improved input validation
- Added rate limiting

## 📚 Documentation

- Updated API documentation
- Added authentication examples
- Improved README

## 🙏 Contributors

Thanks to @developer1, @developer2 for their contributions!

## 📦 Installation

```bash
docker pull shelfscanner/api:1.2.0
```

## 🔗 Links

- [Full Changelog](https://github.com/user/repo/compare/v1.1.0...v1.2.0)
- [Documentation](https://docs.shelfscanner.com)
```

---

# 7. Hotfix Workflow

## 7.1 When to Use Hotfix

Use hotfix for **CRITICAL** production issues:

- ✅ Security vulnerabilities
- ✅ Data loss bugs
- ✅ Critical service outages
- ✅ Payment processing failures

Do NOT use for:
- ❌ Minor bugs
- ❌ Feature requests
- ❌ Performance improvements

## 7.2 Hotfix Process

```bash
# 1. Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-auth-bug

# 2. Fix the issue
vim app/core/security.py

# 3. Commit fix
git add app/core/security.py
git commit -m "fix(auth): resolve critical token validation bug"

# 4. Test thoroughly
pytest
pytest tests/test_auth.py -v

# 5. Push hotfix branch
git push origin hotfix/critical-auth-bug

# 6. Create PR to main (fast-track)
gh pr create --base main --head hotfix/critical-auth-bug \
  --title "🚨 HOTFIX: Critical auth bug" \
  --label "critical,hotfix"

# 7. Get emergency approval (1 reviewer minimum)
# 8. Merge to main
gh pr merge --squash

# 9. Tag hotfix version
git checkout main
git pull origin main
git tag -a v1.2.1 -m "Hotfix: Critical auth bug"
git push origin v1.2.1

# 10. Deploy to production immediately
# Monitor closely

# 11. Backport to staging and develop
git checkout staging
git cherry-pick <commit-hash>
git push origin staging

git checkout develop
git cherry-pick <commit-hash>
git push origin develop

# 12. Delete hotfix branch
git branch -d hotfix/critical-auth-bug
git push origin --delete hotfix/critical-auth-bug
```

## 7.3 Hotfix Checklist

```markdown
## Immediate Actions (within 1 hour)
- [ ] Identify root cause
- [ ] Create hotfix branch
- [ ] Implement fix
- [ ] Write test for the bug
- [ ] Get emergency review
- [ ] Deploy to production

## Follow-up (within 24 hours)
- [ ] Backport to staging
- [ ] Backport to develop
- [ ] Update documentation
- [ ] Post-mortem document
- [ ] Prevent future occurrence

## Communication
- [ ] Notify team
- [ ] Update status page
- [ ] Inform affected users
- [ ] Document incident
```

---

# 8. Git Best Practices

## 8.1 Daily Workflow

```bash
# Morning routine
git checkout develop
git pull origin develop
git checkout feature/my-feature
git rebase origin/develop

# During the day
# Make changes, commit frequently
git add .
git commit -m "feat: add validation logic"

# End of day
git push origin feature/my-feature
```

## 8.2 Common Commands

```bash
# View status
git status
git log --oneline --graph

# View changes
git diff
git diff --staged
git diff main...develop

# Undo changes
git restore <file>                    # Discard working changes
git restore --staged <file>           # Unstage file
git reset HEAD~1                      # Undo last commit (keep changes)
git reset --hard HEAD~1               # Undo last commit (discard changes)

# Stash changes
git stash                              # Stash all changes
git stash push -m "WIP: feature X"    # Stash with message
git stash list                         # View stashes
git stash pop                          # Apply and remove stash
git stash apply stash@{0}             # Apply specific stash

# Branch management
git branch                             # List local branches
git branch -r                          # List remote branches
git branch -d feature/old-feature     # Delete local branch
git push origin --delete feature/old  # Delete remote branch

# Clean up
git fetch --prune                      # Remove deleted remote branches
git clean -fd                          # Remove untracked files
```

## 8.3 Git Aliases

Add to `~/.gitconfig`:

```ini
[alias]
    # Shortcuts
    co = checkout
    br = branch
    ci = commit
    st = status
    
    # Logging
    lg = log --oneline --graph --all --decorate
    last = log -1 HEAD --stat
    
    # Diff
    df = diff
    dfs = diff --staged
    
    # Undo
    undo = reset HEAD~1
    unstage = restore --staged
    
    # Clean up
    cleanup = !git fetch --prune && git branch --merged | grep -v '\\*\\|main\\|develop\\|staging' | xargs -n 1 git branch -d
```

Usage:
```bash
git co develop          # Instead of git checkout develop
git lg                  # Pretty git log
git cleanup             # Delete merged branches
```

## 8.4 .gitignore

Ensure you have a comprehensive `.gitignore`:

```bash
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment
.env
.env.local
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover

# Build
dist/
build/
*.egg-info/

# Database
*.db
*.sqlite3

# Docker
docker-compose.override.yml

# Temporary
tmp/
temp/
*.tmp
```

## 8.5 Git Hooks

Create `.git/hooks/pre-commit` for automated checks:

```bash
#!/bin/bash

echo "Running pre-commit checks..."

# Run linters
echo "Running black..."
black --check app/
if [ $? -ne 0 ]; then
    echo "❌ Black formatting failed. Run: black app/"
    exit 1
fi

echo "Running flake8..."
flake8 app/
if [ $? -ne 0 ]; then
    echo "❌ Flake8 linting failed."
    exit 1
fi

# Run tests
echo "Running tests..."
pytest tests/ -x
if [ $? -ne 0 ]; then
    echo "❌ Tests failed."
    exit 1
fi

echo "✅ All checks passed!"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

# 9. GitHub Actions & Automation

## 9.1 Automated Workflows

### Branch Protection Automation

```yaml
# .github/workflows/branch-protection.yml
name: Branch Protection

on:
  pull_request:
    branches: [main, staging, develop]

jobs:
  enforce-labels:
    runs-on: ubuntu-latest
    steps:
      - name: Check labels
        uses: mheap/github-action-required-labels@v1
        with:
          mode: exactly
          count: 1
          labels: "bug, feature, documentation, enhancement"
```

### Auto-assign Reviewers

```yaml
# .github/auto_assign.yml
addReviewers: true
addAssignees: false

reviewers:
  - team-lead
  - senior-dev

numberOfReviewers: 2

skipKeywords:
  - wip
  - draft
```

### Auto-label PRs

```yaml
# .github/workflows/labeler.yml
name: Labeler

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  label:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/labeler@v4
        with:
          repo-token: "${{ secrets.GITHUB_TOKEN }}"
          configuration-path: .github/labeler.yml
```

```yaml
# .github/labeler.yml
'documentation':
  - 'docs/**/*'
  - '**/*.md'

'api':
  - 'app/api/**/*'

'tests':
  - 'tests/**/*'

'database':
  - 'app/db/**/*'
  - 'alembic/**/*'
```

## 9.2 Release Automation

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          generate_release_notes: true
          draft: false
          prerelease: false
```

---

# 10. Common Scenarios

## 10.1 Starting a New Feature

```bash
# 1. Update develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/book-recommendations

# 3. Work on feature (make commits)
# ... code, commit, code, commit ...

# 4. Push to remote
git push origin feature/book-recommendations

# 5. Create PR when ready
gh pr create --base develop --head feature/book-recommendations
```

## 10.2 Updating Your Branch

```bash
# Method 1: Rebase (recommended, keeps linear history)
git checkout feature/my-feature
git fetch origin
git rebase origin/develop

# If conflicts, resolve and:
git add <resolved-files>
git rebase --continue

# Force push (your branch only!)
git push origin feature/my-feature --force-with-lease

# Method 2: Merge (preserves history)
git checkout feature/my-feature
git fetch origin
git merge origin/develop

# Resolve conflicts if any
git add <resolved-files>
git commit

# Push
git push origin feature/my-feature
```

## 10.3 Fixing a Mistake in Last Commit

```bash
# Forgot to add a file
git add forgotten_file.py
git commit --amend --no-edit
git push --force-with-lease

# Wrong commit message
git commit --amend -m "fix(auth): correct authentication logic"
git push --force-with-lease

# Committed to wrong branch
git log # Copy commit hash
git reset --hard HEAD~1 # Undo commit
git checkout correct-branch
git cherry-pick <commit-hash>
```

## 10.4 Reviewing Someone's PR

```bash
# 1. Fetch all branches
git fetch origin

# 2. Checkout PR branch
gh pr checkout 123

# Or manually:
git checkout -b review-pr-123 origin/feature/user-auth

# 3. Test locally
pytest
python -m app.main

# 4. Review code
git log develop..HEAD
git diff develop...HEAD

# 5. Leave comments on GitHub
# 6. Approve or request changes
```

## 10.5 Emergency Production Fix

```bash
# 1. Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug

# 2. Fix and test
# ... fix code ...
pytest

# 3. Fast-track merge
gh pr create --base main --head hotfix/critical-bug --label critical
# Get approval ASAP
gh pr merge --squash

# 4. Tag and deploy
git checkout main
git pull
git tag v1.2.1
git push origin v1.2.1

# 5. Backport to other branches
git checkout staging
git cherry-pick <commit-hash>
git push origin staging

git checkout develop
git cherry-pick <commit-hash>
git push origin develop
```

---

# 11. Troubleshooting

## 11.1 Common Issues

### "Diverged branches"

```bash
# Problem: Your branch and origin/branch have diverged

# Solution 1: Rebase (if you haven't shared your commits)
git fetch origin
git rebase origin/feature/my-feature
git push --force-with-lease

# Solution 2: Merge (if others are using your branch)
git fetch origin
git merge origin/feature/my-feature
git push
```

### "Merge conflicts"

```bash
# During rebase
git rebase origin/develop
# ... conflicts occur ...

# 1. See conflicted files
git status

# 2. Resolve in editor
vim conflicted_file.py

# 3. Stage resolved files
git add conflicted_file.py

# 4. Continue rebase
git rebase --continue

# Or abort
git rebase --abort
```

### "Accidentally committed to wrong branch"

```bash
# You're on develop but should be on feature branch

# 1. Save commit hash
git log -1  # Copy hash

# 2. Undo commit (keep changes)
git reset HEAD~1

# 3. Stash changes
git stash

# 4. Switch to correct branch
git checkout -b feature/my-feature

# 5. Apply stashed changes
git stash pop

# 6. Commit properly
git add .
git commit -m "feat: add feature"
```

### "Need to undo a public commit"

```bash
# Don't use git reset on public branches!
# Use revert instead

git revert <commit-hash>
git push origin develop
```

### "Lost commits after reset"

```bash
# Use reflog to find lost commits
git reflog

# Find your commit and:
git cherry-pick <commit-hash>

# Or reset to that point:
git reset --hard <commit-hash>
```

## 11.2 Getting Help

```bash
# Git help
git help <command>
git help commit
git help rebase

# Check git version
git --version

# View configuration
git config --list
```

---

# 12. Quick Reference

## 12.1 Branch Workflow Cheat Sheet

```bash
# NEW FEATURE
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
# ... work ...
git push origin feature/my-feature
# Create PR on GitHub

# UPDATE BRANCH
git fetch origin
git rebase origin/develop
git push --force-with-lease

# MERGE TO DEVELOP
# Use "Squash and merge" on GitHub

# RELEASE TO STAGING
# Create PR: develop → staging
# Use "Rebase and merge"

# RELEASE TO PRODUCTION
# Create PR: staging → main
# Use "Rebase and merge"
# Tag: git tag v1.2.0

# HOTFIX
git checkout main
git checkout -b hotfix/critical-bug
# ... fix ...
gh pr create --base main --label critical
# Merge immediately
# Tag: git tag v1.2.1
# Backport to staging and develop
```

## 12.2 Commit Message Examples

```bash
feat(auth): add JWT token refresh
fix(ocr): resolve timeout in batch processing
docs(api): update authentication examples
style(code): format with black
refactor(db): simplify query logic
perf(api): add caching for book list
test(scan): increase coverage to 90%
build(deps): update fastapi to 0.109.0
ci(github): add automated release workflow
chore(config): update .gitignore
```

## 12.3 Essential Git Commands

```bash
# Status & Info
git status
git log --oneline --graph
git diff
git show <commit>

# Branching
git branch                      # List branches
git checkout -b feature/new     # Create and switch
git branch -d feature/old       # Delete branch
git push origin --delete old    # Delete remote

# Staging & Committing
git add <file>
git add .
git commit -m "message"
git commit --amend

# Remote Operations
git fetch origin
git pull origin develop
git push origin feature
git push --force-with-lease

# Undoing Changes
git restore <file>              # Discard changes
git restore --staged <file>     # Unstage
git reset HEAD~1                # Undo commit
git revert <commit>             # Revert commit

# Stashing
git stash
git stash pop
git stash list
git stash drop

# Rebasing
git rebase origin/develop
git rebase --continue
git rebase --abort
```

## 12.4 GitHub CLI Commands

```bash
# PRs
gh pr create
gh pr list
gh pr view 123
gh pr checkout 123
gh pr merge 123 --squash
gh pr close 123

# Issues
gh issue create
gh issue list
gh issue view 456

# Releases
gh release create v1.2.0
gh release list

# Repository
gh repo view
gh repo clone user/repo
```

---

## Appendix: Tools & Resources

### Recommended Tools

- **GitHub CLI**: https://cli.github.com/
- **Git GUI Clients**: GitKraken, Sourcetree, GitHub Desktop
- **VS Code Extensions**: GitLens, Git Graph
- **Pre-commit Hooks**: https://pre-commit.com/

### Learning Resources

- **Pro Git Book**: https://git-scm.com/book
- **Conventional Commits**: https://www.conventionalcommits.org/
- **GitHub Docs**: https://docs.github.com/

### Team Communication

- Create `#git-help` channel in Slack/Discord
- Weekly sync on branching strategy
- Monthly review of this guide
- Onboarding checklist for new developers

---

**Document Version:** 1.0.0  
**Last Updated:** January 2024  
**Maintained By:** Engineering Team

**Questions?** Contact: dev-team@shelfscanner.com
