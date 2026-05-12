# Atlas — ARG and KQL Engineer — History

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

## References

- PR #27: https://github.com/martinopedal/mcp-server-azure-architect/pull/27
- Issue #17: Vendor ALZ queries (initial snapshot)
- Issue #6: ADR-002: vendoring policy for ALZ checklist queries
- Upstream: github.com/martinopedal/alz-checklist-queries (commit e7641bee)
- Upstream: github.com/martinopedal/alz-graph-queries (commit 8a3fdda, v1.1.0)
- Orchestration Log: `.squad/orchestration-log/20260512T000000Z-atlas.md`

## Team Update (2026-05-12)

Wave 2 complete: foundation (#22, #23, #26, #27, #33, #34) all on main. Decisions ledger consolidated. ADR-001 ratified. Next: ADR-002/003/004, branch protection (#20), threat model (#18), and v0.1 docs per Sage's gap audit.
