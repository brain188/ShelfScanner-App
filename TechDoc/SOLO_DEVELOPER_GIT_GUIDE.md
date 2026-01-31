# ShelfScanner - Solo Developer Git Workflow

**Simplified Git & GitHub Guide for One Developer**

Version: 1.0.0 (Solo Edition)  
Last Updated: January 2024

---

## Table of Contents

1. [Quick Overview](#1-quick-overview)
2. [Initial Setup](#2-initial-setup)
3. [Daily Workflow](#3-daily-workflow)
4. [Branch Management](#4-branch-management)
5. [Merging Between Branches](#5-merging-between-branches)
6. [Release Process](#6-release-process)
7. [Quick Commands Reference](#7-quick-commands-reference)

---

# 1. Quick Overview

## Your 3-Branch Strategy (Simplified)

```
develop     → Daily work, all features go here first
   ↓
staging     → Testing before production
   ↓
main        → Production-ready code only
```

**Key Difference for Solo Dev:**
- ✅ Skip Pull Requests (you're approving yourself!)
- ✅ Direct merges are OK
- ✅ Simplified workflow
- ❌ Still use branches (keeps things organized)

---

# 2. Initial Setup

## 2.1 Create Repository and Branches

```bash
# 1. Create repository on GitHub (or clone if exists)
git clone https://github.com/yourusername/shelfscanner.git
cd shelfscanner

# 2. Create all three branches
git checkout -b develop
git push -u origin develop

git checkout -b staging
git push -u origin staging

git checkout -b main
git push -u origin main

# 3. Set develop as default working branch
git checkout develop
```

## 2.2 Set GitHub Default Branch

1. Go to GitHub → Your Repository
2. Click **Settings** → **Branches**
3. Change default branch to `develop`
4. Click **Update**

This makes `develop` the landing page and starting point for new clones.

## 2.3 Optional: Add Branch Protection (Recommended)

Even as solo dev, this prevents accidental mistakes:

**Settings → Branches → Add Rule:**

For `main` branch:
```yaml
Branch name pattern: main
✅ Require status checks to pass (if you have CI/CD)
✅ Do not allow bypassing the above settings
```

This forces you to merge through proper channels (not directly push to main).

---

# 3. Daily Workflow

## 3.1 The Simple Daily Routine

```bash
# MORNING: Start your day
git checkout develop
git pull origin develop

# CREATE FEATURE BRANCH (Optional but recommended)
git checkout -b feature/book-scanning

# WORK: Make changes
# Edit files...
code app/api/v1/scan.py

# COMMIT: Save your work frequently
git add app/api/v1/scan.py
git commit -m "feat(scan): add book scanning endpoint"

# PUSH: Backup to GitHub
git push origin feature/book-scanning

# MERGE TO DEVELOP: When feature is done
git checkout develop
git merge feature/book-scanning
git push origin develop

# CLEANUP: Delete feature branch
git branch -d feature/book-scanning
git push origin --delete feature/book-scanning
```

## 3.2 Even Simpler (Work Directly on Develop)

If features are small, you can skip feature branches:

```bash
# Morning
git checkout develop
git pull origin develop

# Work and commit throughout the day
git add .
git commit -m "feat(books): add search functionality"
git push origin develop

# Repeat as needed
```

**When to use feature branches:**
- ✅ Experimental features (might not work)
- ✅ Large changes (take multiple days)
- ✅ Want to try something without breaking develop

**When to skip feature branches:**
- ✅ Small bug fixes
- ✅ Quick features (< 1 hour)
- ✅ Documentation updates

---

# 4. Branch Management

## 4.1 Working with Feature Branches

### Create a Feature Branch

```bash
# Always branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/ai-recommendations

# Now work on your feature...
```

### Commit Your Work

```bash
# Check what changed
git status

# Stage files
git add app/services/recommendation_engine.py
git add tests/test_recommendations.py

# Commit with good message
git commit -m "feat(recommendations): add AI-powered book recommendations"

# Push to GitHub (backup)
git push origin feature/ai-recommendations
```

### Merge Back to Develop

```bash
# Switch to develop
git checkout develop

# Pull latest (in case you worked on another machine)
git pull origin develop

# Merge your feature
git merge feature/ai-recommendations

# Push to GitHub
git push origin develop

# Delete feature branch (cleanup)
git branch -d feature/ai-recommendations
git push origin --delete feature/ai-recommendations
```

## 4.2 Quick Workflow (No Feature Branch)

```bash
# Work directly on develop
git checkout develop
git pull origin develop

# Make changes
# ... edit files ...

# Commit
git add .
git commit -m "fix(ocr): improve image preprocessing"

# Push
git push origin develop
```

---

# 5. Merging Between Branches

This is the key process: moving code from develop → staging → main

## 5.1 Develop → Staging (Weekly or When Ready)

**When to do this:** 
- You've completed several features
- Want to test in a staging environment
- Ready to prepare for release

```bash
# 1. Make sure develop is clean and pushed
git checkout develop
git status  # Should be clean
git push origin develop

# 2. Switch to staging
git checkout staging
git pull origin staging

# 3. Merge develop into staging
git merge develop

# 4. Push to GitHub and deploy
git push origin staging

# Staging server automatically deploys (if CI/CD setup)
# Or manually deploy to staging server
```

### If Conflicts Occur

```bash
# During merge, if conflicts:
git merge develop
# CONFLICT in app/api/v1/books.py

# 1. Open conflicted file
code app/api/v1/books.py

# 2. Look for conflict markers:
# <<<<<<< HEAD (staging)
# ... staging version ...
# =======
# ... develop version ...
# >>>>>>> develop

# 3. Choose which version to keep (or combine them)
# Remove markers (<<<<<<, =======, >>>>>>>)

# 4. Stage resolved file
git add app/api/v1/books.py

# 5. Complete the merge
git commit -m "merge: develop into staging"

# 6. Push
git push origin staging
```

## 5.2 Staging → Main (Production Release)

**When to do this:**
- Staging has been tested thoroughly
- No bugs found
- Ready for production

```bash
# 1. Switch to main
git checkout main
git pull origin main

# 2. Merge staging into main
git merge staging

# 3. Tag the release
git tag -a v1.2.0 -m "Release v1.2.0 - Book Recommendations"

# 4. Push code and tag
git push origin main
git push origin v1.2.0

# Production server deploys automatically (if CI/CD)
# Or manually deploy to production
```

## 5.3 Visual Workflow Example

Here's a complete week's workflow:

```bash
# MONDAY: Start new features
git checkout develop
git checkout -b feature/book-export
# ... work ...
git commit -m "feat(books): add CSV export"
git push origin feature/book-export
git checkout develop
git merge feature/book-export
git push origin develop

# TUESDAY-THURSDAY: More features
git checkout -b feature/reading-stats
# ... work ...
git commit -m "feat(stats): add reading statistics"
git push origin feature/reading-stats
git checkout develop
git merge feature/reading-stats
git push origin develop

# FRIDAY: Release to staging
git checkout staging
git merge develop
git push origin staging
# Test on staging server

# NEXT MONDAY: Release to production
git checkout main
git merge staging
git tag v1.3.0
git push origin main
git push origin v1.3.0
```

---

# 6. Release Process

## 6.1 Simple Release Checklist

```markdown
## Before Release
- [ ] All features merged to develop
- [ ] Tests passing locally (pytest)
- [ ] No console errors
- [ ] Updated CHANGELOG.md

## Deploy to Staging
- [ ] Merge develop → staging
- [ ] Test on staging server
- [ ] Verify all features work

## Deploy to Production  
- [ ] Merge staging → main
- [ ] Create version tag (v1.x.x)
- [ ] Push to GitHub
- [ ] Monitor production for 30 minutes
```

## 6.2 Creating Releases

### Step 1: Update Version Numbers

```python
# app/__init__.py
__version__ = "1.3.0"
```

```bash
git add app/__init__.py
git commit -m "chore: bump version to v1.3.0"
git push origin develop
```

### Step 2: Update CHANGELOG.md

```markdown
# Changelog

## [1.3.0] - 2024-02-15

### Added
- Book CSV export functionality
- Reading statistics dashboard
- AI-powered recommendations

### Fixed
- OCR timeout on large images
- Authentication token refresh issue

### Changed
- Improved database query performance
```

```bash
git add CHANGELOG.md
git commit -m "docs: update changelog for v1.3.0"
git push origin develop
```

### Step 3: Merge to Staging and Test

```bash
git checkout staging
git merge develop
git push origin staging

# Test thoroughly on staging
```

### Step 4: Release to Production

```bash
# Merge to main
git checkout main
git merge staging
git push origin main

# Create and push tag
git tag -a v1.3.0 -m "Release v1.3.0 - Statistics & Export"
git push origin v1.3.0
```

### Step 5: Create GitHub Release (Optional)

```bash
# Using GitHub CLI
gh release create v1.3.0 --title "v1.3.0 - Statistics & Export" --notes "See CHANGELOG.md"

# Or manually on GitHub:
# 1. Go to Releases
# 2. Click "Draft a new release"
# 3. Choose tag v1.3.0
# 4. Add release notes
# 5. Publish
```

---

# 7. Quick Commands Reference

## 7.1 Daily Commands

```bash
# Start working
git checkout develop
git pull origin develop

# Create feature (optional)
git checkout -b feature/my-feature

# Save work
git add .
git commit -m "feat: description"
git push origin develop

# Merge feature to develop
git checkout develop
git merge feature/my-feature
git push origin develop

# Delete feature branch
git branch -d feature/my-feature
```

## 7.2 Release Commands

```bash
# To Staging
git checkout staging
git merge develop
git push origin staging

# To Production
git checkout main
git merge staging
git tag v1.x.x
git push origin main
git push origin v1.x.x
```

## 7.3 Useful Commands

```bash
# See current branch
git branch

# See commit history
git log --oneline --graph

# See what changed
git status
git diff

# Undo changes (before commit)
git restore filename.py

# Undo last commit (keep changes)
git reset HEAD~1

# Stash changes temporarily
git stash
git stash pop
```

---

# 8. Simplified Decision Tree

## When Should I...?

### Commit?
- ✅ After completing a logical piece of work
- ✅ Before switching tasks
- ✅ At end of work session
- ✅ Frequently (every 30-60 minutes)

### Push?
- ✅ After every commit (backup to GitHub)
- ✅ At least daily
- ✅ Before closing laptop

### Merge to Staging?
- ✅ After completing a feature
- ✅ Before testing
- ✅ Weekly or bi-weekly
- ✅ When ready to prepare release

### Merge to Main?
- ✅ After staging tests pass
- ✅ When ready for production
- ✅ Monthly or per milestone
- ✅ For important releases

---

# 9. Solo Developer Shortcuts

Since you're working alone, you can skip some complexity:

## 9.1 What You CAN Skip

❌ **Pull Requests** - You're approving yourself
❌ **Code Reviews** - No one to review  
❌ **Multiple Approvals** - Just you
❌ **Complex Branch Protection** - Simple is fine
❌ **Elaborate Commit Messages** - Keep it clear but simple

## 9.2 What You SHOULD Keep

✅ **3 Branches** - Keeps production safe
✅ **Good Commit Messages** - Future you will thank you
✅ **Frequent Commits** - Don't lose work
✅ **Version Tags** - Track releases
✅ **CHANGELOG** - Remember what you built
✅ **Backup (Push to GitHub)** - Daily minimum

## 9.3 Ultra-Simple Workflow (If Needed)

If even the 3-branch system feels too complex, here's minimal viable:

```bash
# Just use 2 branches: develop + main

# Daily work on develop
git checkout develop
# ... work, commit, push ...

# When ready for production
git checkout main
git merge develop
git tag v1.x.x
git push origin main --tags
```

---

# 10. Common Scenarios (Solo Dev)

## Scenario 1: Daily Feature Development

```bash
# Morning
git checkout develop
git pull

# Work and commit
code app/
git add .
git commit -m "feat(books): add filtering"
git push

# Repeat throughout day
```

## Scenario 2: Ready to Test (Deploy to Staging)

```bash
# Merge to staging
git checkout staging
git merge develop
git push

# Deploy to staging server (manual or auto)
# Test everything

# If bugs found:
git checkout develop
# Fix bugs
git commit -m "fix(books): resolve filter bug"
git push

# Merge fixes to staging
git checkout staging
git merge develop
git push
```

## Scenario 3: Production Release

```bash
# After staging is stable
git checkout main
git merge staging

# Tag release
git tag v1.2.0
git push origin main
git push origin v1.2.0

# Deploy to production
```

## Scenario 4: Emergency Hotfix

```bash
# Critical bug in production!

# Create hotfix from main
git checkout main
git checkout -b hotfix/critical-bug

# Fix the bug
git commit -m "fix: critical authentication bug"

# Merge to main
git checkout main
git merge hotfix/critical-bug
git tag v1.2.1
git push origin main
git push origin v1.2.1

# Backport to other branches
git checkout staging
git merge hotfix/critical-bug
git push

git checkout develop  
git merge hotfix/critical-bug
git push

# Delete hotfix branch
git branch -d hotfix/critical-bug
```

## Scenario 5: Experimenting with Ideas

```bash
# Create experimental branch
git checkout develop
git checkout -b experiment/new-ui

# Try things out
# ... experiment ...

# If you like it:
git checkout develop
git merge experiment/new-ui
git push

# If you don't like it:
git checkout develop
git branch -D experiment/new-ui  # Delete without merging
```

---

# 11. Git Aliases for Speed

Add these to `~/.gitconfig` for faster commands:

```ini
[alias]
    # Shortcuts
    co = checkout
    ci = commit
    st = status
    br = branch
    
    # Quick operations
    save = !git add -A && git commit -m 'SAVEPOINT'
    wip = !git add -A && git commit -m 'WIP'
    undo = reset HEAD~1
    
    # Logs
    lg = log --oneline --graph --decorate
    
    # Branch management
    cleanup = !git branch --merged | grep -v '\\*\\|main\\|develop\\|staging' | xargs -n 1 git branch -d
```

Usage:
```bash
git save          # Quick save point
git wip          # Work in progress commit
git undo         # Undo last commit
git lg           # Pretty log
git cleanup      # Delete merged branches
```

---

# 12. Your Weekly Workflow Template

Here's a suggested weekly rhythm:

## Monday
```bash
git checkout develop
git pull
# Start new features
```

## Tuesday-Thursday
```bash
# Daily development
git commit frequently
git push daily
```

## Friday
```bash
# Wrap up features
# Merge to staging
git checkout staging
git merge develop
git push
# Test over weekend
```

## Next Monday
```bash
# If staging is good, release
git checkout main
git merge staging
git tag v1.x.x
git push --tags
```

---

# 13. Final Tips for Solo Developers

## ✅ Do This

1. **Commit frequently** - At least 3-5 times per day
2. **Push daily** - Even if feature isn't done
3. **Use descriptive commit messages** - `feat(books): add search` not `update`
4. **Test on staging** - Don't skip this step
5. **Tag releases** - Easy to rollback if needed
6. **Keep CHANGELOG** - Remember what you built

## ❌ Avoid This

1. **Don't commit directly to main** - Always go through develop → staging → main
2. **Don't skip testing** - Use staging branch
3. **Don't use vague messages** - "fix stuff" is bad
4. **Don't let branches diverge too much** - Merge to staging weekly
5. **Don't forget to push** - Backup to GitHub regularly

## 🎯 Golden Rule

**"Develop daily, stage weekly, release monthly"**

This keeps a good rhythm and prevents overwhelming releases.

---

# 14. Troubleshooting

## "I made a mistake, how do I undo?"

```bash
# Before committing
git restore filename.py

# After committing (local only)
git reset HEAD~1

# After pushing (be careful!)
git revert <commit-hash>
```

## "I committed to the wrong branch"

```bash
# Save the commit
git log  # Copy commit hash

# Undo commit
git reset HEAD~1

# Switch to correct branch
git checkout correct-branch

# Apply commit
git cherry-pick <commit-hash>
```

## "I have merge conflicts"

```bash
# During merge
git merge develop
# CONFLICT appears

# Open file, find:
# <<<<<<< HEAD
# ... your code ...
# =======  
# ... their code ...
# >>>>>>> develop

# Choose what to keep, remove markers
# Save file

git add conflicted-file.py
git commit -m "merge: resolve conflicts"
```

---

# Quick Start Checklist

For your first day with this workflow:

```markdown
## Setup (One Time)
- [ ] Create repository on GitHub
- [ ] Clone to local machine
- [ ] Create develop, staging, main branches
- [ ] Set develop as default branch
- [ ] Push all branches to GitHub

## Daily Routine
- [ ] git checkout develop
- [ ] git pull
- [ ] Work and commit frequently
- [ ] git push at end of day

## Weekly (Friday)
- [ ] Merge develop to staging
- [ ] Test on staging server

## Monthly (or when ready)
- [ ] Merge staging to main
- [ ] Create version tag
- [ ] Deploy to production
```

---

**You're all set!** 🚀

Start simple, and as you get comfortable, you can add more sophistication. The key is:
- **develop** = your workspace
- **staging** = your testing ground  
- **main** = production (sacred!)

Good luck with ShelfScanner! 📚
