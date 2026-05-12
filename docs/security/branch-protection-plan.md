# Branch Protection Plan: main

**Version:** 1.0  
**Date:** 2026-05-12  
**Owner:** Lead (Coordinator)  
**Related Issue:** #20

## Overview

This document defines the branch protection settings for the `main` branch in `martinopedal/mcp-server-azure-architect`. It serves as the executable specification for the coordinator to apply after this PR (ADR-003 + threat model) lands.

**Context:** Issue #20 tracks branch protection enablement. This PR (closes #7, #18) prepares the documentation. The coordinator will execute the `gh api` commands in this plan after merge.

## Current Status

As of 2026-05-12, the following protections are **already enabled** on `main`:

- `enforce_admins: true` (admins cannot bypass)
- `required_linear_history: true` (no merge commits; squash or rebase only)

These settings were enabled during wave 1 foundation work. The coordinator must preserve them when updating other settings.

## Required Status Checks

The following CI checks must pass before a PR can merge to `main`. These are categorized as **immediate** (already in CI) or **aspirational** (to be added in future PRs).

### Immediate Checks (Already in CI)

These checks are already defined in `.github/workflows/` and should be added to the required list now:

1. **`CI / test (ubuntu-latest, 3.11)`** — Test suite on Python 3.11 (Ubuntu)
2. **`CI / test (ubuntu-latest, 3.12)`** — Test suite on Python 3.12 (Ubuntu)
3. **`gitleaks / scan`** — Secret scanning with gitleaks
4. **`dependency-review / review`** — Dependency vulnerability scanning
5. **`CodeQL / Analyze (actions)`** — CodeQL security analysis (GitHub Actions)
6. **`CodeQL / Analyze (python)`** — CodeQL security analysis (Python)

**Total immediate checks:** 6

### Aspirational Checks (To Be Added in Follow-Up PRs)

These checks are planned but not yet implemented. They should be added to the required list once their workflows land:

7. **`readonly-check`** — ADR-003 layer 1 enforcement (`.github/scripts/check_readonly.py`). Tracked in issue #7.
8. **`mcp-inspector-smoke`** — MCP Inspector validation (all tools list with valid JSON Schema). Tracked in issue #19.
9. **`coverage`** — Code coverage gate (threshold TBD, likely 80%). Tracked in issue #TBD.
10. **`license-check`** — License compliance check (all deps have acceptable licenses). Tracked in issue #TBD.

**Total aspirational checks:** 4

**Combined total:** 10 required status checks (6 immediate + 4 aspirational)

## Required Pull Request Reviews

**Setting:** `required_approving_review_count = 1`

**Current value:** 0 (no reviews required)

**Rationale:** AGENTS.md and project conventions require at least one non-author reviewer. This setting enforces it at the GitHub level.

**Exception:** Bots (e.g., Dependabot) PRs should be exempted from review requirement if they pass all CI checks. This can be configured via GitHub branch protection UI (allow specific actors to bypass).

## Branch Protection Settings Summary

| Setting | Current Value | Target Value | Notes |
|---------|---------------|--------------|-------|
| `required_status_checks.strict` | false | **true** | Require branches up-to-date before merge |
| `required_status_checks.contexts` | [] (none) | **[6 immediate checks]** | See list above; add aspirational checks as they land |
| `required_pull_request_reviews.required_approving_review_count` | 0 | **1** | At least one non-author reviewer |
| `required_pull_request_reviews.dismiss_stale_reviews` | false | **false** | Allow stale reviews (low friction for fast iteration) |
| `required_pull_request_reviews.require_code_owner_reviews` | false | **false** | CODEOWNERS review is advisory, not blocking (v0.1) |
| `required_pull_request_reviews.require_last_push_approval` | false | **false** | Allow self-push after approval (low friction) |
| `enforce_admins` | true | **true** | PRESERVE. Admins cannot bypass (critical for audit story) |
| `required_linear_history` | true | **true** | PRESERVE. No merge commits (squash or rebase only) |
| `allow_force_pushes` | false | **false** | PRESERVE. No force-push to main |
| `allow_deletions` | false | **false** | PRESERVE. Cannot delete main branch |
| `required_signatures` | false | **false** | Out of scope for v0.1 (commit signing not required) |
| `restrictions` | null | **null** | No push restrictions; all merges via PR |

## Execution Plan

### Prerequisites

1. **This PR must be merged first.** Coordinator cannot apply required checks that don't exist in CI yet.
2. **Confirm current state.** Before running commands, verify existing settings:
   ```bash
   gh api repos/martinopedal/mcp-server-azure-architect/branches/main/protection
   ```
   Save output to `branch-protection-before.json` for rollback reference.

### Step 1: Enable Required Status Checks (Immediate)

This command sets the 6 immediate checks as required and enables `strict` mode (branches must be up-to-date):

```bash
gh api -X PUT repos/martinopedal/mcp-server-azure-architect/branches/main/protection/required_status_checks \
  -f strict=true \
  -f 'contexts[]=CI / test (ubuntu-latest, 3.11)' \
  -f 'contexts[]=CI / test (ubuntu-latest, 3.12)' \
  -f 'contexts[]=gitleaks / scan' \
  -f 'contexts[]=dependency-review / review' \
  -f 'contexts[]=CodeQL / Analyze (actions)' \
  -f 'contexts[]=CodeQL / Analyze (python)'
```

**Expected result:** All 6 checks become required. PRs cannot merge until they pass.

**Validation:**
```bash
gh api repos/martinopedal/mcp-server-azure-architect/branches/main/protection/required_status_checks
```
Output should include `"strict": true` and all 6 contexts.

### Step 2: Enable Required Pull Request Reviews

This command requires 1 approving review before merge:

```bash
gh api -X PATCH repos/martinopedal/mcp-server-azure-architect/branches/main/protection/required_pull_request_reviews \
  -f required_approving_review_count=1 \
  -f dismiss_stale_reviews=false \
  -f require_code_owner_reviews=false \
  -f require_last_push_approval=false
```

**Expected result:** PRs require 1 approval. Stale reviews are not dismissed (low friction).

**Validation:**
```bash
gh api repos/martinopedal/mcp-server-azure-architect/branches/main/protection/required_pull_request_reviews
```
Output should include `"required_approving_review_count": 1`.

### Step 3: Verify Other Settings (Preserve Existing)

These settings should already be enabled. Verify, do not change:

```bash
gh api repos/martinopedal/mcp-server-azure-architect/branches/main/protection | jq '{enforce_admins, required_linear_history, allow_force_pushes, allow_deletions}'
```

**Expected output:**
```json
{
  "enforce_admins": true,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
```

If any value is incorrect, file issue and do not proceed. These are critical settings.

### Step 4: Add Aspirational Checks (As They Land)

When each aspirational check's workflow is merged to `main`, the coordinator updates the required checks list.

**Example:** After issue #7 (readonly-check) lands, run:

```bash
gh api -X PUT repos/martinopedal/mcp-server-azure-architect/branches/main/protection/required_status_checks \
  -f strict=true \
  -f 'contexts[]=CI / test (ubuntu-latest, 3.11)' \
  -f 'contexts[]=CI / test (ubuntu-latest, 3.12)' \
  -f 'contexts[]=gitleaks / scan' \
  -f 'contexts[]=dependency-review / review' \
  -f 'contexts[]=CodeQL / Analyze (actions)' \
  -f 'contexts[]=CodeQL / Analyze (python)' \
  -f 'contexts[]=readonly-check'
```

**Note:** Each `gh api -X PUT` replaces the entire contexts list. Always include all existing checks plus the new one.

### Step 5: Admin Toggle for Coordinator Merge

**Context:** `enforce_admins: true` applies to the coordinator (who is an admin). To merge this PR after approval, the coordinator must temporarily disable `enforce_admins`, merge, then re-enable.

**Commands:**

1. **Before merge:**
   ```bash
   gh api -X DELETE repos/martinopedal/mcp-server-azure-architect/branches/main/protection/enforce_admins
   ```

2. **Merge PR via GitHub UI or:**
   ```bash
   gh pr merge <PR_NUMBER> --squash --delete-branch
   ```

3. **After merge (immediate):**
   ```bash
   gh api -X POST repos/martinopedal/mcp-server-azure-architect/branches/main/protection/enforce_admins
   ```

**CRITICAL:** Re-enable `enforce_admins` immediately after merge. Do not leave it disabled.

**Validation:**
```bash
gh api repos/martinopedal/mcp-server-azure-architect/branches/main/protection | jq .enforce_admins
```
Output should be `{"enabled": true}`.

## Rollback Plan

If a required check breaks CI or causes merge blockages, the coordinator can temporarily remove it without losing other protections.

### Rollback Step 1: Identify the Broken Check

Example: `readonly-check` fails spuriously and blocks all PRs.

### Rollback Step 2: Remove the Broken Check

Re-run the `required_status_checks` command with the broken check removed:

```bash
gh api -X PUT repos/martinopedal/mcp-server-azure-architect/branches/main/protection/required_status_checks \
  -f strict=true \
  -f 'contexts[]=CI / test (ubuntu-latest, 3.11)' \
  -f 'contexts[]=CI / test (ubuntu-latest, 3.12)' \
  -f 'contexts[]=gitleaks / scan' \
  -f 'contexts[]=dependency-review / review' \
  -f 'contexts[]=CodeQL / Analyze (actions)' \
  -f 'contexts[]=CodeQL / Analyze (python)'
  # Note: 'readonly-check' is removed from this list
```

### Rollback Step 3: File Issue and Fix

File a bug issue for the broken check. Assign to the check owner (per AGENTS.md). Re-add the check once fixed.

### Rollback Step 4: Full Rollback (Nuclear Option)

If all protections are broken and PRs cannot merge, restore from `branch-protection-before.json`:

```bash
gh api -X PUT repos/martinopedal/mcp-server-azure-architect/branches/main/protection \
  --input branch-protection-before.json
```

**WARNING:** This restores ALL settings, including potentially broken ones. Use only as a last resort.

## Testing Plan (Before Production Execution)

### Test 1: Dry-Run on a Test Branch

1. Create a test branch (e.g., `test-branch-protection`) in the repo.
2. Apply all protection settings to the test branch using the commands above (replace `main` with `test-branch-protection`).
3. Open a test PR against the test branch. Verify:
   - PR cannot merge without 1 approval.
   - PR cannot merge if any required check fails.
   - PR cannot merge if branch is out-of-date (must rebase or merge main).
4. If tests pass, apply to `main`. If tests fail, debug before proceeding.

### Test 2: Validate Check Names

Before applying to `main`, verify that all check names match CI workflow job names **exactly**. Mismatched names will cause PRs to block indefinitely.

**Validation command:**
```bash
gh api repos/martinopedal/mcp-server-azure-architect/commits/main/check-runs --jq '.check_runs[].name'
```

Compare output against the contexts list in Step 1. Names must match exactly (case-sensitive, spacing-sensitive).

## Success Criteria

Branch protection is successfully applied when:

1. All 6 immediate required checks are enforced on `main`.
2. PRs require 1 approval before merge.
3. PRs must be up-to-date with `main` before merge (`strict: true`).
4. `enforce_admins: true` is preserved (admins cannot bypass).
5. `required_linear_history: true` is preserved (no merge commits).
6. Coordinator can verify all settings via:
   ```bash
   gh api repos/martinopedal/mcp-server-azure-architect/branches/main/protection | jq .
   ```
7. A test PR can be opened, approved, and merged successfully (proving the protection settings work).

## References

1. **GitHub REST API, Branch Protection:**  
   [docs.github.com/rest/branches/branch-protection](https://docs.github.com/rest/branches/branch-protection)

2. **GitHub CLI (`gh api`):**  
   [cli.github.com/manual/gh_api](https://cli.github.com/manual/gh_api)

3. **Issue #20:** Branch protection tracking issue (sets-up)

4. **Issue #7:** ADR-003 read-only enforcement (readonly-check workflow)

5. **Issue #19:** MCP Inspector smoke test (mcp-inspector-smoke workflow)

6. **AGENTS.md, Validation Gates:**  
   "PRs require at least one non-author reviewer and clean CI."

7. **ADR-003: Read-Only Enforcement Mechanism:**  
   `docs/adr/0003-read-only-enforcement.md` (created in this PR)

8. **Threat Model:**  
   `docs/security/threat-model.md` (created in this PR)

## Coordinator Checklist

Before executing:

- [ ] This PR (#TBD) is merged to `main`.
- [ ] Current branch protection settings saved to `branch-protection-before.json`.
- [ ] Check names validated against CI workflow output (names match exactly).
- [ ] Test branch protection applied and tested successfully (optional but recommended).

Execute:

- [ ] Step 1: Enable required status checks (6 immediate checks).
- [ ] Step 2: Enable required pull request reviews (1 approval).
- [ ] Step 3: Verify other settings (`enforce_admins`, `required_linear_history` preserved).
- [ ] Step 5: Admin toggle to merge this PR (disable, merge, re-enable immediately).

Post-execution:

- [ ] Validate all settings applied correctly (success criteria met).
- [ ] Open test PR to confirm protections work end-to-end.
- [ ] Comment on issue #20: "Branch protection applied per `docs/security/branch-protection-plan.md`."
- [ ] Close issue #20.

## Notes for Future Updates

- **Adding new required checks:** Always include all existing checks in the `contexts[]` array. GitHub replaces the entire list on each `PUT`.
- **Removing checks:** Omit the check from the `contexts[]` array and re-run the `PUT` command.
- **Changing review count:** Adjust `required_approving_review_count` value and re-run Step 2.
- **Quarterly review:** Sentinel and Lead review this document quarterly. Update if CI structure changes (new workflows, renamed jobs, etc.).

---

**Prepared by:** Sentinel  
**Reviewed by:** TBD (Lead will review in PR)  
**Executed by:** Lead (Coordinator) after PR merge
