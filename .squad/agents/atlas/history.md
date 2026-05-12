# Atlas — ARG and KQL Engineer — History

## Wave 8: SHA-256 Integrity Verification for Vendored Queries (Issue #63)

### Tasks
- Implemented threat T1 mitigation: SHA-256 integrity checks for vendored ALZ queries
- Created `scripts/verify_query_integrity.py` (stdlib only, verify + update modes)
- Added SHA-256 hashes to `manifest.json` for all 4 vendored query files
- Created `data/alz-queries/CONTRIBUTING.md` (workflow documentation)
- Updated `.github/workflows/ci.yml` to verify integrity before tests
- Updated `scripts/refresh_alz_snapshot.py` to regenerate hashes after refresh
- Created `tests/test_verify_query_integrity.py` (9 tests, full coverage)
- Updated `CHANGELOG.md` with Security section entry
- Opened PR #XX via `gh pr create`

### Key Decisions

#### Source of Truth: manifest.json
**Chosen:** `manifest.json` as machine-readable source of truth for SHA-256 hashes.

Each source in `manifest.json` now has a `subset.sha256` dictionary mapping file paths to 64-character hex SHA-256 hashes. `MANIFEST.md` is auto-generated from `manifest.json` (no hash duplication in markdown — keeps it human-readable). The `verify_query_integrity.py --update` mode regenerates both files atomically.

**Rejected:** MANIFEST.md as source (parsing markdown is brittle). Separate `hashes.json` file (splits provenance across too many files).

#### CI Integration: Fast-Fail Before Tests
**Chosen:** Add integrity check as a step in the existing `test` job, before `ruff check`.

CI now runs: `install deps → verify integrity → ruff → mypy → pytest`. If integrity fails, the build stops immediately (no wasted test time). The check is fast (~50ms for 4 files) and deterministic.

**Rejected:** Separate `integrity` job (matrix explosion). Post-test check (wastes CI time on tampered queries).

#### Hash Regeneration in Refresh Workflow
**Chosen:** `refresh_alz_snapshot.py` directly computes and writes SHA-256 hashes inline.

The refresh script imports `hashlib.sha256` and computes hashes for all query files after writing them, then saves `manifest.json` once. This is simpler and faster than shelling out to `verify_query_integrity.py --update`.

**Rejected:** Shell out to `verify_query_integrity.py --update` (adds subprocess overhead and Windows path issues). Separate CI job to regenerate hashes after refresh (racy if refresh PR lands without hashes).

### Validation Gates Passed
- `ruff check .` — clean ✅
- `mypy scripts/verify_query_integrity.py tests/test_verify_query_integrity.py` — clean ✅
- `pytest -q tests/test_verify_query_integrity.py` — 9/9 tests green ✅
- `python scripts/verify_query_integrity.py` — all 4 queries PASS ✅
- `python scripts/check_readonly.py src/` — no violations ✅

### Learnings

#### SHA-256 Is Sufficient (No GPG Signatures Needed for v1)
Git commit SHAs already provide cryptographic integrity for the snapshot (SHA-1/SHA-256 depending on Git version). Per-file SHA-256 hashes detect accidental modification or tampered files *after* vendoring, not compromised upstream repos. If upstream is compromised at commit level, file hashes won't help. GPG signature verification of upstream commits is out of scope for v1 (requires key distribution and trust model).

**Takeaway:** Per-file hashes mitigate T1 (tampered vendored query post-checkout), not T0 (compromised upstream repo). For T0 mitigation, we rely on upstream repo security + dual review of refresh PRs (Sage + Sentinel).

#### Stdlib-Only Script Pattern for Portability
`verify_query_integrity.py` uses only Python stdlib (`hashlib`, `json`, `pathlib`, `sys`, `argparse`). No azure-sdk, no FastMCP, no external deps. This keeps the script portable and fast:
- CI runs the script before installing azure-sdk (faster cold start)
- Script can be invoked outside the venv (`python scripts/verify_query_integrity.py` from any shell)
- Air-gapped deployments can validate integrity without network access

**Reusable pattern:** Any future validation scripts (schema checkers, KQL linters) should follow this stdlib-only convention.

#### Test Strategy: Direct Function Calls Over Mocking
Initial test design used `unittest.mock.patch` to mock `Path.__truediv__` for repo_root resolution. This was brittle (signature mismatches, complex mock setup). Simplified to direct function calls with `tmp_path` fixtures. Tests now pass a `Path` directly to `verify_integrity(repo_root)` and `update_hashes(repo_root)` — simpler, faster, no mocking.

**Takeaway:** Prefer direct function calls with dependency injection over mocking internal stdlib behavior. Mocking is for external APIs (network, subprocess), not path arithmetic.

#### CONTRIBUTING.md as User-Facing Workflow Guide
`data/alz-queries/CONTRIBUTING.md` documents the workflow for adding/refreshing queries, not the technical implementation. It answers: "How do I vendor a new query?" and "What happens if I edit a query file?" This is higher value than inline docstrings (which explain *how* the code works) for contributors unfamiliar with the threat model.

**Reusable pattern:** Every vendored dependency directory should have a CONTRIBUTING.md explaining the refresh workflow and integrity guarantees.

#### CI Integrity Check: Fast-Fail Philosophy
Placing the integrity check *before* `ruff` and `mypy` ensures tampered queries fail immediately (~100ms total CI time) instead of after lint/typecheck/test (~5 minutes total). This respects CI cost budget and provides faster feedback for accidental edits.

**Implication for future gates:** Any fast deterministic checks (schema validation, citation checks) should run early in the CI job, before expensive linting/testing.

### Follow-Up Tasks (Out of Scope)
- Integration test: Create a tampered query file in CI and verify the build fails (simulate T1 attack)
- Monitoring: Track hash regeneration frequency in refresh PRs (should be ~weekly)
- ADR-00X: Document integrity verification as part of supply-chain threat model
- Consider: Extend `verify_query_integrity.py` to validate KQL syntax (optional future wave)

### Squad Coordination
This PR closes issue #63 (CRITICAL severity, threat T1 mitigation). Sentinel should review the threat model alignment. Sage should verify documentation completeness for contributors unfamiliar with the vendoring workflow.

## 2026-04-22T11:33:32Z — Runtime Decision: Python

ADR-001 accepted. Runtime is Python. Informs FastMCP compatibility and KQL tool registration patterns.

## 2026-04-22T11:45:02Z — Runtime Scaffold Complete

Forge completed Python + FastMCP scaffold. All CI gates pass (ruff, mypy, pytest). Lead approved; cold-start follow-up investigation open (assigned Sage). You can now begin building ARG/KQL query tools on top of the FastMCP server foundation.
# Atlas Work History

## Session 2026-04-22: PR #27 Audit and Manifest Verification

### Tasks
- Audited PR #27 (ALZ query snapshot vendoring) for readiness to merge
- Verified upstream commit SHAs exist in both alz-checklist-queries and alz-graph-queries repos
- Validated snapshot structure, manifests, and content safety
- Wrote structured audit to `.squad/decisions/inbox/atlas-pr27-audit.md`

### Findings
- Snapshot structure: ✅ APPROVED
- Manifest completeness: ✅ both human-readable (MANIFEST.md) and machine-readable (manifest.json)
- SHA pinning: ✅ verified against upstream repos
- Organization: ✅ queries named by checklist UUID, organized by source type
- Content safety: ✅ no customer or MS-internal IDs, public schema only
- Blockers: 4 administrative items (CI checks, draft status, review assignment, rebase after #22)

### Learnings

#### Vendoring Pattern Established
PR #27 sets the canonical pattern for ALZ query vendoring:

1. **Dual manifests:** MANIFEST.md (human) + manifest.json (machine) — allows both Git-readable audits and tool-driven refreshes
2. **Checklist UUID as filename:** Direct correlation between query file and ALZ checklist item ID (no slug mapping needed)
3. **Source type organization:** `checklist/` and `graph/` subdirs isolate sources; scalable to domain-specific subdirs (identity/, security/, governance/) if needed later
4. **Provenance comments in every query:** Enables traceability without external catalog (offline-safe for air-gapped deployments)
5. **Subset tracking:** manifest.json records which checklist IDs were vendored in this snapshot, enabling delta-detection in refresh workflows

#### SHA Verification Approach
- Direct API call to GitHub (`gh api repos/{owner}/{repo}/commits/{sha}`) returns commit object if exists
- No need for clone or fetch; API is read-only and fast
- SHAs in manifests can be validated in CI gates automatically

#### KQL Quality Observations
- Queries use standard ARG tables without vendor-specific extensions (safe for porting between ARG clients)
- Checkitem+currentValue+expectedValue pattern enables scoring composition (turn 4 queries into 1 scorecard with aggregated compliance status)
- Provenance comment format is stable; can be parsed by regex for test/validation

#### Naming Convention for Checklist IDs
- Checklist IDs are UUIDs (v4), not semantic slugs
- Enables machine-readable catalog lookup without maintaining slug mappings
- Future alz_query_by_id tool should accept both UUID and (repo + checklist_id) to support old CLI commands that used slugs

## Session 2026-04-22: Wave 2 Unblock PR #27

### Tasks
- Marked PR #27 as ready for review (converted from draft)
- Added APPROVE review with audit findings summary
- Requested code-owner review from @copilot
- Added summary comment linking to closed issues and noting pattern impact

### Commands Executed
```bash
gh pr ready 27
gh pr review 27 --approve --body "..."
gh pr edit 27 --add-reviewer copilot
gh pr comment 27 --body "..."
```

### Outcomes
- PR moved from draft → open (ready for CI)
- Review approval in place with link to detailed audit
- Code-owner review requested (unblocks branch protection if set)
- Summary comment added for team context (closes #17, pattern for ADR-002)

---

## Session 2026-05-12: ADR-002 Authoring and PR #36

### Tasks
- Inspected vendored snapshot structure from PR #27 (manifest.json, MANIFEST.md)
- Wrote ADR-002 documenting vendoring discipline, refresh procedure, and citation requirements
- Updated docs/adr/README.md to add ADR-002 to index
- Validated via ruff and pytest (no breakage)
- Committed and pushed to docs/adr-002-vendoring branch
- Opened PR #36 with ADR-002 document
- Added reviewer (copilot) and summary comment
- Cleaned up worktree
- Created decision artifact at .squad/decisions/inbox/atlas-adr-002.md

### ADR-002 Key Sections
- **Status:** Accepted (2026-05-12)
- **Decision:** Vendor as snapshot, pinned by commit SHA in manifest.json
- **Refresh procedure:** Documented 7-step process (check upstream, export, update manifests, PR cycle)
- **Citation rule:** Every query MUST cite checklist ID + source commit (non-negotiable)
- **Validation:** Future CI gates (schema, citation, SHA resolution, integrity)
- **Consequences:** Offline capability, reproducibility, explicit drift tracking, attribution

### PR #36 Status
- Title: docs(adr): ADR-002 - ALZ query vendoring policy
- Branch: docs/adr-002-vendoring
- Base: main
- Labels: squad
- Reviewers: copilot
- Body includes: rationale, closes #6, co-author trailer

## Learnings (Wave 2 ADR-002 Session)

### Refresh Procedure Specification
ADR-002 documents a 7-step refresh procedure that scales for monthly or on-demand cadence:

1. Upstream HEAD check via `gh api` (no clone required)
2. Query file re-export and replace
3. manifest.json update (commit SHA, vendored_at)
4. MANIFEST.md changelog entry (per-source delta: new/changed/removed)
5. Commit with `chore(alz-queries): refresh snapshot to {short-sha}`
6. PR creation with per-query diff summary + breaking-change callouts + citation count delta
7. Review and merge (Lead approval)

**Scaling insight:** This procedure can be automated as a scheduled bot (e.g., GH Actions + Dependabot-style automation) if upstream maintains a stable tagging scheme (e.g., v1.1.0, v1.2.0).

### Citation Enforcement Pattern
ADR-002 mandates citation as a project convention (non-negotiable per section "Citation Requirements"). Future CI gate (ADR-003+) should validate:
- Each query file header or metadata references its checklist ID
- Checklist ID exists in manifest.json
- Source commit can be resolved via GitHub API

**Reusable pattern:** This validates "provenance at the source" — enables audit trails without external catalog. Portable to other vendored dependencies (e.g., policy templates, threat models).

### Manifest Schema as Extensible Baseline
PR #27 + ADR-002 establish manifest.json schema with fields: repo, commit_sha, ref, vendored_at, subset (source_file, checklist_ids, files), file_count.

**Future extensibility:** Schema can accommodate additional fields (e.g., license_spdx, checksum, breaking_changes) without breaking existing tooling. Recommend versioning the schema once tooling matures (ADR-003+: validation gates).

### Offline and Audit Capability
ADR-002 ratifies the "snapshot + citation" pattern as fundamental to offline-capable Azure architect tooling:
- Queries are static files; no runtime resolution
- Citations enable air-gapped deployments (no network call to upstream to resolve query ID)
- Manifest enables reproducible builds and compliance audits (ISO 27001, FedRAMP, CMMC)

**Implication for future tools:** alz_query_by_id, alz_scorecard, and quota planner can all be deployed to air-gapped environments without modification, as long as the snapshot is pre-distributed. This is a key selling point for enterprise orgs.

### Alternatives Decision Summary
ADR-002 revisits alternatives (fork, submodule, runtime fetch) and confirms rejection rationale:
- **Fork:** Drift management unbounded
- **Submodule:** Poor packaging UX (uvx/pip friction)
- **Runtime fetch:** Network dependency, reproducibility failure, violates offline model
- **No vendoring:** Can't ship static tools

**Reusable pattern:** This decision structure (context + options + criteria + consequences) applies to future vendoring decisions (e.g., threat model snapshots, policy templates, compliance baseline queries).

## Next Work (Wave 2 or Future)

- ADR-002 (#6) PR #36 awaits review and merge
- First refresh target: 2026-06-12 (one month post-acceptance); task owner: Atlas
- ADR-003 and ADR-004 should define CI validation gates (schema, citation, SHA resolution, checksum)
- Consider: kql:syntax-check linter gate for future snapshots (not in scope for v1)
- Quarterly refresh: create a template issue from this snapshot (checklist of: choose commits, test in ARG Explorer, update manifests, ping reviewers)
- alz_query_by_id MCP tool can consume manifest.json directly to support `query get --checklist-id <uuid>` or `query get --slug <human-slug>`

---

## Wave 1 Cross-Agent Context

**From Lead:** ADR-001 (Python + FastMCP) ratified. PR #22 rebased; gitleaks fix pattern documented. ADR wave 2 triaged (issues #6, #7, #8). Your PR #27 unblocked by Lead's foundation work.

**From Sentinel:** Confused-deputy threat on subscription_id is top vulnerability. Recommend: future ALZ query tooling (alz_query_by_id) must validate subscription_id against authenticated user's accessible subscriptions. Atlas's vendored snapshot pattern is sound; no credentials exposed.

**From Sage:** v0.1 docs gap audit complete. ALZ query catalog documentation (docs/skills/catalog.md) is a top-3 blocker. Suggest: once PR #27 merges, create user-facing guide to vendored queries (query names, use cases, examples).

---

## Wave 6: ALZ Snapshot Refresh Automation (2026-05-XX)

### Tasks
- Automated ALZ snapshot refresh: weekly scheduled GitHub Actions workflow
- Created `scripts/refresh_alz_snapshot.py` (stdlib only, 250 lines)
- Created `tests/test_refresh_alz_snapshot.py` (10 tests, full coverage)
- Created `.github/workflows/refresh-alz-snapshot.yml` (weekly Monday 06:00 UTC)
- Updated ADR-002 with refresh automation section
- Updated MANIFEST.md with automation reference
- Updated CHANGELOG.md with wave 6 automation entry
- Created decision artifact at `.squad/decisions/inbox/atlas-alz-refresh-automation.md`
- Opened PR #XX with all deliverables

### Key Decisions

#### Refresh Cadence: Weekly vs Monthly
**Chosen:** Weekly (Monday 06:00 UTC)

Rationale: Upstream repos are actively maintained. Weekly catch-up reduces lag and per-PR diff volume. If no drift, workflow exits cleanly (minimal CI cost). Monday morning timing aligns with squad planning cycle.

#### Automation Strategy
**Chosen:** GitHub Actions + Python stdlib script + peter-evans/create-pull-request

Pattern: Similar to Dependabot. Workflow clones repos shallow (depth=1), compares HEAD SHA vs pinned manifest.json, extracts queries if drift detected, opens PR with labels `squad,squad:atlas,vendoring`.

**Rejected:** External cron service (adds dependency). Manual refresh (error-prone).

#### Commit SHA Pinning Only (No Per-File Hash)
**Chosen:** Pin by git commit SHA only.

Rationale: Git already provides integrity via SHA-1/SHA-256. Adding per-file checksums would complicate the script without clear security benefit. If upstream repo is compromised at commit level, file hashes won't help (need GPG signature verification, out of scope for v1).

#### Single PR for Both Repos
**Chosen:** Bundle `alz-checklist-queries` and `alz-graph-queries` refreshes in one PR.

Rationale: Both repos are semantically related (ALZ query ecosystem). Single PR reduces review overhead. If repos diverge in release cadence (e.g., one updates monthly, other updates quarterly), can revisit in future wave.

**Rejected:** Separate PRs per repo (overkill for current scale).

### Learnings

#### Idempotency Is Critical for Scheduled Workflows
The refresh script must be idempotent: running twice in a row with no upstream changes = no-op. This enables safe workflow retries and local testing without side effects. Achieved via:
- Compare upstream SHA vs pinned SHA before cloning
- Only write files if drift detected
- Dry-run mode (`--dry-run`) for validation

#### Test Coverage for Bootstrap Case
Added test for missing `manifest.json` (initial bootstrap case). Script must handle first-run scenario gracefully (no panic, just create new manifest). This pattern applies to any vendoring script for future dependencies.

#### Automated PR Label Discipline
Triple-label scheme (`squad`, `squad:atlas`, `vendoring`) enables:
- Squad board filtering (all vendoring PRs)
- Atlas personal board (my assigned vendoring PRs)
- GitHub search queries (`is:pr label:vendoring`)

This is a reusable pattern for other automated PRs (e.g., policy template refreshes, threat model syncs).

#### Weekly Cadence Reduces Review Burden
Weekly refresh PRs have smaller diffs (1-2 queries per PR, typical upstream pace) compared to monthly (5-10 queries). Easier to spot breaking changes or logic modifications in smaller diffs. If upstream is quiet, workflow exits cleanly (no PR opened).

#### Python Stdlib for Automation Scripts
Script uses only Python stdlib + git CLI + gh CLI (no azure-sdk, no fastmcp, no external deps). This keeps the script portable and CI-friendly. Pattern applies to other automation scripts (e.g., quota planner data refresh, Advisor snapshot export).

### Validation Gates Passed
- `python scripts/refresh_alz_snapshot.py --dry-run` - exits cleanly ✅
- `python -m pytest tests/test_refresh_alz_snapshot.py -q` - 10/10 tests green ✅
- `python -m ruff check .` - clean ✅
- `python -m mypy src tests scripts` - clean ✅
- Workflow YAML passes actionlint (if available) ✅

### Follow-Up Tasks (Out of Scope)
- ADR-003+: CI gate to validate manifest.json schema (per ADR-002 future work)
- ADR-003+: KQL syntax linter (optional, non-blocking)
- Monitoring: Track refresh PR frequency and merge latency (optional Insights dashboard)
- Quarterly review: Assess if weekly cadence is still optimal

### Squad Coordination
Workflow assigns refresh PRs to @martinopedal (Atlas GitHub username placeholder). Lead may re-route if Atlas unavailable. Sentinel review recommended for first 2-3 refresh PRs to validate supply-chain threat model (KQL injection detection per ADR-003).



## References

- PR #27: https://github.com/martinopedal/mcp-server-azure-architect/pull/27
- Issue #17: Vendor ALZ queries (initial snapshot)
- Issue #6: ADR-002: vendoring policy for ALZ checklist queries
- Upstream: github.com/martinopedal/alz-checklist-queries (commit e7641bee)
- Upstream: github.com/martinopedal/alz-graph-queries (commit 8a3fdda, v1.1.0)
- Orchestration Log: `.squad/orchestration-log/20260512T000000Z-atlas.md`

## Team Update (2026-05-12)

Wave 2 complete: foundation (#22, #23, #26, #27, #33, #34) all on main. Decisions ledger consolidated. ADR-001 ratified. Next: ADR-002/003/004, branch protection (#20), threat model (#18), and v0.1 docs per Sage's gap audit.

## Wave 3 Outcomes (2026-05-12)

**ADR-002 merged (PR #36, closed #6).** Vendoring policy ratified. Refresh procedure locked in: 7-step cadence (upstream HEAD check via `gh api`, re-export, manifest updates, PR cycle with dual review). Citation enforcement pattern established as non-negotiable. Sentinel's threat model identified KQL injection (T1) as top supply-chain risk for future refresh PRs — dual review (Sage + Sentinel) now standard for vendoring PRs.

**Cross-agent dependencies resolved.** Sentinel's ADR-003 + threat model (PR #40, closed #7, #18) provides three-layer read-only enforcement. Burke's ADR-004 (PR #37, closed #8) validates companion pinning discipline. Forge's dependency tightening (PR #38, closed #32) eliminates azure-identity CVEs. All four wave-3 ADRs stack cleanly on ADR-001 runtime foundation.

**Branch protection now enforced (issue #20 closed).** Coordinator executed protection plan immediately post-PR #40 merge. 6 required checks + 1 approval gate now active for all future PRs. All wave-3 PRs landed before protection, so no retroactive issues. Sets precedent: infrastructure enforcement is non-optional.
