# Skill: CI Gate Addition (Avoiding Branch Protection Updates)

**Owner:** Sentinel  
**Domain:** CI infrastructure, validation gates  
**Last Updated:** 2025-01-20

## Summary

Pattern for adding new required CI validation gates without needing branch protection updates. Applies to GitHub Actions workflows where a new check must be required for all PRs.

## Problem

When a new validation gate (lint, format, security scan) needs to become a required check:
- Adding a NEW JOB creates a new status check that must be added to branch protection settings
- Branch protection updates require admin permissions
- Creates coordination overhead between implementation PR and branch protection update
- Risk of forgetting to add the new check to branch protection

## Solution

**Add the new gate as a STEP inside an existing required job**, not as a new job.

This approach:
- Inherits the existing job's required status check
- No branch protection update needed
- New gate runs on every PR immediately after PR merge
- Simpler workflow structure

## Implementation Pattern

### Before (creates new required check)

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: pytest

  new-gate:  # ❌ New job = new required check
    runs-on: ubuntu-latest
    steps:
      - name: Run new validation
        run: new-tool --check
```

**Required action:** Admin must add `new-gate` to branch protection required checks.

### After (reuses existing required check)

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Run tests
        run: pytest
      
      - name: Run new validation  # ✅ New step in existing job
        run: new-tool --check
```

**Required action:** None. The new step runs as part of the existing `test` check.

## When to Use This Pattern

Use this pattern when:
- The new gate is related to an existing job (e.g., format check next to lint check)
- The new gate has no special runner requirements (same OS, same Python version)
- The new gate is fast (<2 minutes)
- The new gate doesn't benefit from parallelism with other jobs

## When NOT to Use This Pattern

Use a separate job when:
- The new gate needs a different matrix (different OS, different runtime version)
- The new gate needs special setup (different language, different tools)
- The new gate is slow (>5 minutes) and would benefit from running in parallel
- The new gate is logically separate (e.g., a deployment step, not a validation step)

In these cases, accept the branch protection update overhead and document it clearly in the PR body.

## Documentation Requirements

When adding a CI gate using this pattern:

1. **PR body must state the placement choice:**
   ```markdown
   ## CI Placement Choice
   
   Added as a NEW STEP inside the existing `test` job.
   
   ## Branch Protection Update Needed Post-Merge
   
   **NO** — the gate is embedded in the existing required `test` job.
   ```

2. **Update CONTRIBUTING.md validation gates section** to include the new gate in the local validation commands.

3. **Update CHANGELOG.md** with an entry under appropriate section (typically `Automation` or `Repository Infrastructure`).

## Example: Adding ruff format check

**Context:** Codebase has ruff lint (`ruff check`) in CI. Need to add format check (`ruff format --check`).

**Implementation:** (PR #123, issue #117)

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest]
        python-version: ["3.11", "3.12"]
    steps:
      # ... setup steps ...
      
      - name: Run ruff check
        run: ruff check .
      
      - name: Run ruff format check  # ✅ Added here
        run: ruff format --check .
      
      - name: Run mypy
        run: mypy src
```

**Outcome:** No branch protection update needed. Format check runs on every PR as part of the existing `CI/test (ubuntu-latest, 3.x)` required check.

## Related

- Issue #117 (ruff format gate)
- PR #123 (implementation)
- `.squad/agents/sentinel/history.md` (learnings section)
- AGENTS.md (validation gates section)

## Anti-Patterns

### Anti-Pattern 1: Adding gate as a new job for "clean separation"

```yaml
jobs:
  lint:
    steps:
      - run: ruff check .
  
  format:  # ❌ New job for "clean separation"
    steps:
      - run: ruff format --check .
```

**Why avoid:** Creates branch protection update overhead with no benefit. Format check is logically related to lint check and has the same requirements. Group them together.

### Anti-Pattern 2: Using job-level conditionals to "group" unrelated checks

```yaml
jobs:
  all-checks:
    steps:
      - run: ruff check .
      - run: ruff format --check .
      - run: deploy-to-production  # ❌ Unrelated step
```

**Why avoid:** Deployment is not a validation gate and should not be in the test job. Keep validation gates together, but don't abuse this pattern to avoid creating appropriate separate jobs.

## Pattern Evolution

This pattern emerged during issue #117 (ruff format gate addition). Key insight: branch protection coordination is a frequent source of friction. Prefer in-job steps when possible to minimize coordination overhead.

If this pattern is used 3+ times across the repo, consider documenting it in CONTRIBUTING.md as a team convention.
