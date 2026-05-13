# Squad Decisions

## Wave 1 — Foundation Unblock (2026-05-12)

### ADR-001: Runtime Choice

**Decision:** APPROVE WITH NITS

**Runtime locked:** Python with FastMCP.

**Rationale:** Cold start <1s, lowest contributor friction, mature Azure SDK, auto-generates JSON Schema from type hints, and uvx distribution fits the tool model.

**Details:** Sage's ADR is sound. All project constraints respected. Cold-start, auth, read-only boundary, and CI gates are addressed with citations. Two minor documentation nits (benchmark URL, uvx inline link) to address in follow-up. Forge can proceed with Python implementation.

**Status:** Accepted (2026-04-22, Lead)

### Forge: Runtime Scaffold Complete

**Date:** 2026-04-22  
**Agent:** Forge (MCP Server Runtime Engineer)

**Decision Summary:**

FastMCP server runtime scaffolded successfully. Key technical choices:

1. **Package structure:** src layout (not flat) for import hygiene.
2. **Python version:** >=3.11 for modern type hints and faster interpreter.
3. **Build backend:** hatchling for minimal configuration.
4. **Tool registration:** FastMCP `@mcp.tool()` decorator with automatic JSON Schema generation from type hints.

**Outcomes:**

- Cold start: 1048ms (within acceptable range, includes pytest overhead).
- Single `health_check` tool registered and validated.
- All CI gates pass: ruff (lint), mypy (type check), pytest (4/4 tests).
- Entry point: `mcp-server-azure-architect` console script ready for uvx distribution.

**Next Steps:**

Atlas and Iris can now build on this foundation. Atlas adds ARG/KQL query tools. Iris authors skills that orchestrate them.

### Lead Review: Python + FastMCP Runtime Scaffold

**Date:** 2026-04-22  
**Reviewer:** Lead  
**Artifact:** Forge's runtime scaffold (pyproject.toml, src/, tests/, CI, README)

**Verdict:** APPROVE WITH NITS

**Rationale:**

The scaffold is sound. Read-only boundary is intact: no Azure mutation clients imported, credential construction is lazy via `get_credential()`, and `token_scrub()` helper exists per AGENTS.md requirements. Layout (src/, hatchling, console script) is clean. CI enforces ruff, mypy, pytest. No em dashes in new files. Tool registration test validates schema presence.

The cold-start gate is the one trade-off. ADR-001 specified "under 1 second" citing FastMCP at 200-800ms. Forge measured 1048ms and softened the test to warn at 1000ms, hard-fail at 5000ms. This is pragmatic: CI is slower than dev, and first-run import cache adds variance. The test still fails if something is catastrophically wrong. Accepting the 1048ms result given measurement noise is reasonable, but this deserves a follow-up investigation rather than moving the goalposts permanently.

**Nits (non-blocking, follow-up issues):**

- [ ] **Cold-start investigation issue.** 1048ms exceeds the 200-800ms ADR claim. Open an issue to investigate: measure `mcp[cli]` vs `mcp` import cost, profile lazy import opportunities, confirm Python 3.11 baseline (dev machine appeared to run 3.14). Owner: Sage (research/examples/docs domain). Goal: bring measured cold start under 800ms or update ADR with revised expectation and citation.
- [ ] **CI matrix Python version.** Currently tests 3.11 and 3.12. Consider adding 3.13 when stable. No action now.
- [ ] **MCP Inspector listing gate.** AGENTS.md lists "All tools list in MCP Inspector with valid JSON Schema" as a validation gate. The test_server.py asserts schema presence, which is a partial proxy. True MCP Inspector integration in CI is harder to automate. Document this gap or add a manual verification checklist for PRs.

**Cold-Start Trade-Off Named:**

Accepted 1048ms measured cold start against the 200-800ms ADR claim. Rationale: measurement noise, first-run import cache, CI variability. Mitigated by opening a performance investigation issue. If investigation shows systematic overhead, ADR will be updated with revised expectation.

**Follow-Up Suggestion:**

Open issue: **"perf: Investigate cold-start overhead (target <800ms)"**. Assign to Sage. Scope: profile import graph, measure `mcp[cli]` vs minimal `mcp` dependency, test lazy imports for azure-identity, confirm 3.11 baseline.
### ADR-001: Runtime Choice (Python + FastMCP) — RATIFIED

**Date:** 2026-05-12 | **Status:** Implemented (PR #22 merged) | **Decision Maker:** Lead

Python 3.11+ with FastMCP runtime approved as foundation for MCP server + Copilot CLI skills bundle.

**Rationale:**
- Azure SDK maturity: azure-identity DefaultAzureCredential supports env, managed identity, az cli, cert auth out-of-box
- ARG/KQL SDK ergonomics superior to TypeScript alternatives
- FastMCP reduces tool-registration boilerplate vs. raw MCP spec
- Wedge vs. azure-mcp: named ALZ queries with scoring, quota planner, Advisor surfacing

**Consequences:**
- Runtime foundation (src/, tests/, pyproject.toml) established and merged to main
- Copilot CLI skills development unblocked
- ADR wave 2 can proceed (issues #6, #7, #8)

**Related:** PR #22, issue #30 (gitleaks fix), orchestration-log-lead-2026-05-12

---

### Gitleaks PR Scan Pattern — APPROVED

**Date:** 2026-05-12 | **Status:** Implemented | **Pattern Owner:** Lead

For any GitHub Actions workflow using `gitleaks/gitleaks-action` on `pull_request` triggers, env var `GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}` must be explicitly passed to the action step.

**Implementation:**
```yaml
- uses: gitleaks/gitleaks-action@<version>
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    GITLEAKS_CONFIG: .gitleaks.toml
```

**Why:** gitleaks-action 8.x cannot access secrets implicitly; requires explicit env injection per GitHub Actions documentation.

**Related:** Issue #30 (gitleaks scan failure, now fixed), PR #22

---

### PR #27 Audit: ALZ Query Snapshot Vendoring — APPROVE

**Date:** 2026-05-12 | **Status:** APPROVE (pending admin blockers) | **Auditor:** Atlas

PR #27 ALZ query snapshot structure, manifests, and content verified and approved for merge. Snapshot pinned by commit SHA; dual manifests (MANIFEST.md + manifest.json) complete; all 4 vendored queries use public ARG schema only.

**Key Findings:**
- Snapshot structure: ✅ UUIDs as query filenames, organized by source type (checklist/, graph/)
- Manifests: ✅ both human-readable (MANIFEST.md) and machine-readable (manifest.json)
- Provenance: ✅ every query includes upstream source comment (repo, commit SHA, checklist ID)
- Content safety: ✅ public schema only, no customer/MS-internal IDs
- SHA verification: ✅ verified against upstream repos via GitHub API

**Administrative Blockers (Expected to Clear):**
1. CI checks (pending Forge validation)
2. PR draft status → mark ready
3. Reviewer assignment (Lead to assign)
4. Rebase after PR #22 merge (no conflicts anticipated)

**Vendoring Pattern Established:**
1. Dual manifests enable Git-readable audits + tool-driven refreshes
2. Checklist UUID as filename (no slug mapping needed)
3. Source-type organization (checklist/ vs graph/) is scalable to domain-specific subdirs
4. Provenance comments in every query support air-gapped deployments
5. Subset tracking in manifest.json enables delta-detection for refresh workflows

**Impact:**
- ADR-002 (#6) should codify this pattern for future snapshots
- Confused-deputy threat (from Sentinel's threat model) flags that vendored queries must not accept user-supplied subscription_id without validation
- Sage's docs audit notes that ALZ query catalog documentation is a top-3 gap for v0.1

**Related:** PR #27, issue #17 (ALZ vendoring), issue #6 (ADR-002), orchestration-log-atlas-2026-05-12

---

### ADR-003: Read-Only Enforcement Strategy — OUTLINED (Option E Recommended)

**Date:** 2026-05-12 | **Status:** Proposed skeleton, awaiting team ratification | **Owner:** Sentinel

Framework for enforcing read-only Azure SDK calls in MCP server + skills.

**Recommended Approach: Option E (Combination)**
1. **Static Analysis (Primary):** AST/import-check CI gate that rejects imports of Azure SDK mutation classes (`Begin*`, `Create*`, `Update*`, `Delete*` from `azure.mgmt.*`, `azure.storage.*`)
2. **Convention (Secondary):** CONTRIBUTING.md mandates doc comment justifying why each Azure SDK import is read-only
3. **Code Review:** Human oversight for edge cases + indirect call patterns
4. **Runtime Guard (Optional):** Defer to v2 if call surface becomes complex

**Rationale:**
- Static analysis catches 95% of direct mutation imports automatically
- Convention documents intent and catches non-obvious cases
- Code review provides human oversight
- Scales from Python to TypeScript/Rust if runtime changes

**Consequences:**
- Read-only enforcement becomes a hard CI blocker (validation gate per AGENTS.md)
- Developers must understand which Azure SDK classes are safe to import
- False positives suppressed via `# noqa: sentinel-readonly` comments

**Open Questions for Ratification:**
1. Tool choice: custom Python AST script vs ruff plugin vs mypy plugin vs grep-based?
2. Scope: does "no mutation" include `Begin*` (long-running ops)? Recommend: yes, block them.
3. False positives: suppress via `# noqa: sentinel-readonly` comment?
4. Transitive deps: only direct imports in src/, not site-packages/?

**Related:** Issue #7 (ADR-003), issue #20 (CI gates), threat-model-outline, required-checks

---

### Threat Model (STRIDE-Lite) and Supply Chain Analysis — DRAFTED

**Date:** 2026-05-12 | **Status:** Proposed skeleton, awaiting team ratification | **Owner:** Sentinel

Comprehensive threat analysis for read-only MCP server + vendored ALZ queries + companion servers.

**Top 3 Threats (Exploitability):**

1. **Confused-Deputy via Unvalidated subscription_id** (Spoofing)
   - Risk: Tool accepts arbitrary subscription string; without validation, AI agent can probe subscriptions outside caller's scope
   - Mitigation: Tool must validate subscription_id against authenticated user's accessible subscriptions; raise ToolException if out of scope
   - Status: Open (requires implementation when tool signatures finalized)

2. **Token Leakage via Logging** (Information Disclosure)
   - Risk: Azure SDK or tool errors may log bearer tokens or secrets
   - Mitigation: All logging routes through token_scrub() helper; redacts Bearer tokens, GUIDs, secrets per gitleaks patterns; disabled by default (opt-in via MCP_DEBUG env var)
   - Status: Partial (helper not yet implemented)

3. **Compromised Vendored Query** (Tampering)
   - Risk: If alz-checklist-queries repo is compromised, malicious KQL could exfiltrate data
   - Mitigation: Pin snapshots by commit SHA; verify on import; manifest file lists snapshot commit, date, and verifier
   - Status: Partial (manifest + Sentinel review ready; CI gate for SHA verification pending)

**Supply Chain Risk Matrix:**

| Dependency | Current | Risk Level | Mitigation |
|---|---|---|---|
| mcp[cli] | >=1.0.0 | Medium (loose constraint) | Tighten to >=1.27.0; monitor weekly |
| azure-identity | >=1.15.0 | Low-Medium (10-version slack) | Upgrade minimum to >=1.23.0; had CVEs in 1.13-1.16 |
| azure-mgmt-resourcegraph | >=8.0.0 | Low | Safe (read-only surface); no action needed |
| Transitive (cryptography, PyJWT, Requests) | TBD | Medium | Dependabot scans weekly; dependency-review CI gate (issue #20) |
| ALZ Checklist + Graph Snapshots | Pinned by SHA | Low-Medium | Manifest file; verified by Sage + Sentinel; quarterly refresh |
| Companion Servers (azure-mcp, mermaid, drawio, kubernetes, terraform) | @latest or pinned | Medium | Official sources (Microsoft, HashiCorp, GitHub) preferred; community packages require version pin + freshness check (<6 months) |

**Companion-Server Pinning Policy:**
- All servers must specify version pins in mcp-config.json (no @latest)
- npm packages: pin to major.minor (e.g., @1.2.x)
- Docker containers: use digest or semantic version, never `latest` tag
- Official sources (Microsoft, HashiCorp): weekly update reviews
- Community packages: freshness check + >100 GitHub stars minimum before inclusion
- Update PRs require Sage research note + Sentinel supply chain review + Lead approval

**Mitigations Checklist:**
- [ ] Token-scrub helper implemented and integrated into all logging paths
- [ ] Subscription/tenant validation in tool implementation
- [ ] Gitleaks config blocks real GUIDs in non-doc paths (✓ DONE: .gitleaks.toml)
- [ ] Dependabot configured and scanning weekly
- [ ] Dependency-review CI gate enabled (issue #20)
- [ ] Read-only static analysis gate wired into CI (ADR-003)
- [ ] Vendored query snapshots signed with manifest SHA
- [ ] Companion-server update policy documented in CONTRIBUTING.md

**Open Questions for Ratification:**
1. Token scrubbing scope: scrub subscription IDs in DEBUG logs only, or keep in INFO logs for audit trail?
2. Companion-server signers: require signed releases (npm sigs) or Docker image digests?
3. Vendored snapshot integrity: git submodules vs tarballs vs fetch at build time?
4. Audit logs: separate audit log file, or integrated into standard MCP server logging?
5. Cross-tenant protection: support v0.1, or defer to v1?

**Related:** Issue #7 (ADR-003), issue #18 (threat model), issue #20 (CI gates), issue #30 (gitleaks), orchestration-log-sentinel-2026-05-12

---

### Required CI Status Checks for Branch Protection — OUTLINED

**Date:** 2026-05-12 | **Status:** Proposed skeleton, awaiting implementation | **Owner:** Sentinel

Comprehensive list of 10 required status checks for main branch protection rule.

**Checks (in priority order):**

1. **dependency-review** — GitHub native CVE scan for transitive deps
2. **gitleaks** — Secret/token/GUID scan (custom job in .github/workflows/)
3. **Analyze (CodeQL)** — Static security analysis
4. **ruff-lint** — Python code linting (E, W, F, I, N, UP, B, C4, SIM rules)
5. **ruff-format** — Python code formatting (fails if not formatted; does NOT auto-fix in CI)
6. **mypy** — Python type checking with strict mode (disallow_untyped_defs = true)
7. **pytest** — Functional tests with >80% coverage
8. **read-only-static-analysis** — Custom job: blocks Azure SDK mutation imports (ADR-003)
9. **mcp-inspector-smoke-test** — Validates tool definitions (JSON Schema, required fields)
10. **build-python** — Hatchling build without warnings

**Workflow Sketch:**
- All jobs run in parallel on pull_request and push to main
- Each job is optional until explicitly marked required in branch protection settings
- Phase 1 (current): Draft this skeleton
- Phase 2 (Forge + runtime ADR): Implement CI workflow and read-only enforcement script
- Phase 3 (after first successful PR): Mark all checks as required on main

**GitHub Branch Protection Config (Phase 3):**
```
Settings > Branches > Branch protection rules > main:
✓ dependency-review
✓ gitleaks
✓ Analyze (actions)
✓ ruff-lint
✓ ruff-format
✓ mypy
✓ pytest
✓ read-only-static-analysis
✓ mcp-inspector-smoke-test
✓ build-python

Also:
✓ Dismiss stale PR approvals when new commits are pushed
✓ Require a pull request before merging
✓ Require approvals: 1 (non-author)
✓ Require status checks to pass before merging
✓ Require branches to be up to date before merging

---

## Wave 2 — Foundation Merge Complete (2026-05-12)

### PR #23 mcp-config Audit (v0)

**Status:** MERGED to main (commit cf5d5d5)

**Date:** 2026-04-22 | **Owner:** Burke

mcp-config.json audited and hardened. Companion versions pinned to stable releases. Four per-client install guides created for Copilot CLI, Claude Desktop, Cursor, and VS Code Copilot. Compatibility matrix documents version rationale and testing roadmap.

**Key Findings:**
- All companion versions pinned (azure-mcp 2.0.1, mcp-mermaid 0.4.1, drawio 2.0.4, kubernetes 0.0.53, terraform v0.5.1)
- No hardcoded credentials; GitHub PAT is templated env var
- Install docs provide step-by-step merge instructions for v0
- Compatibility matrix shows 2 tested, 5 pending, 1 blocked (runtime TBD)

**Closes:** #15

---

### PR #23 Rebase Outcome

**Status:** MERGED to main (commit cf5d5d5)

**Date:** 2026-04-23 | **Agent:** Burke

Clean rebase of PR #23 against new main (post PR #22 + #33). Zero conflicts. All CI gates passed (ruff, mypy, pytest, gitleaks, CodeQL, dependency-review).

**Key Points:**
- 28 files changed; no manual conflict resolution needed
- Config + install docs integrated cleanly with runtime scaffold
- Squad history appended
- All 5 critical workflows passed; 1 non-blocking label-sync failure (workflow issue)

---

### PR #26 Rebase Outcome

**Status:** MERGED to main (commit 91e24a5)

**Date:** 2026-04-23 | **Agent:** Forge

Clean rebase with manual resolution of scaffold duplication and ADR-001 conflict. PR #26's cold-start investigation and calibrated test thresholds (1000ms soft, 2000ms hard) retained. Measured cold-start on rebased branch: 1116ms (Windows, Python 3.14).

**Key Resolutions:**
- Scaffold duplication: kept main's canonical src/ layout, removed root-level duplicate
- ADR-001 conflict: kept main's comprehensive analysis, appended PR #26's empirical addendum
- Test calibration: used PR #26's refined thresholds aligned with investigation findings

**Closes:** #21 (cold-start investigation)

---

### Iris Skill Catalog v0 (draft)

**Status:** Proposed skeleton

**Date:** 2025-04-22 | **Owner:** Iris

First Copilot CLI extension (alz-gap-check) composition pattern outlined. Extension orchestrates alz_query_by_id tool with optional microsoft-learn-mcp remediation. Skill catalog v0 documents trigger phrases, dependencies, and testing scenarios.

**Key Decisions:**
- Use Copilot CLI extension format (.github/extensions/*/extension.mjs), not markdown skills
- alz-gap-check chosen as first skill (clean input/output contract, minimal dependencies)
- v0 inlines curated query list; dynamic sourcing via alz_scorecard_composition deferred
- Read-only enforcement: skill surfaces gaps, never proposes mutations

**Trade-offs:**
- Curated query list requires code edits for updates (mitigated post-scorecard ship)
- Simulated failures for demo (replaced with real tool calls once server lands)

**Next:** Integration test after server runtime lands; dynamic lookup post-scorecard ADR.

---

### Sage Cold-Start Investigation Notes

**Status:** Proposed

**Date:** 2026-04-22 | **Owner:** Sage

Cold-start profiling on Python 3.11/3.12 investigated. Measured cache-warm time: 943ms (3.12), 1381-4347ms variance (3.11). Top contributor: mcp package (1385ms cumulative, 98.8% of total). Azure SDKs lazy-loaded, zero import-time cost.

**Finding:** Hard gate of 5000ms is too permissive; 2000ms recommended to catch 2x regressions. Soft warning at 1000ms for awareness.

**Recommendation:** Accept 2000ms hard gate; calibrate test to measure cache-warm time (skip first run). Update ADR-001 if cold-start expectation changes based on this investigation.

**Related:** PR #26 cold-start calibration and addendum.

---

### User Directives Log

**Date:** 2026-04-22

**Directive:** Allow @copilot to self-merge its own PRs once CI is green and required reviews satisfied.

**Purpose:** Captured for team memory. Reduces martinopedal manual merge load while offline. Implementation at coordinator discretion per branch protection policy.
```

**Open Questions:**
1. Coverage threshold: >80% or different target?
2. CodeQL severity: block on "Error" + "Warning", or advisory "Note" only?
3. Read-only script location: .github/scripts/check_readonly.py?
4. Concurrent vs. chained execution: all parallel (let GitHub Actions schedule)?

**Related:** Issue #20 (CI gates), issue #7 (ADR-003), issue #18 (threat model), orchestration-log-sentinel-2026-05-12

---

### Documentation Gap Audit for v0.1 — COMPLETED

**Date:** 2026-05-12 | **Status:** Research complete, wave 2 assignments pending | **Owner:** Sage

Comprehensive audit cataloguing 55+ documentation items: 15 existing, 22 claimed but missing, 10+ in open PRs, 8 needed for v0.1.

**Summary:**
- Docs that exist on main: 15 (all root markdown, agent charters, governance, config)
- Claimed but missing: 22 (docs/ directory, ADRs, install guides, queries/ manifest, skills catalog)
- In open PRs: 10+ (ADR-001, install docs, vendor snapshot, threat model, skills)
- Needed for v0.1, no issue yet: 8 (quickstart, tool reference, skill catalog, threat model expansion, release notes, ADR index, troubleshooting, contributing guide)

**Top 3 Critical Blockers for v0.1:**
1. **docs/skills/catalog.md** — User-facing reference for all four skills (design-review, alz-gap-check, ingress-migration-plan, policy-as-code-suggest). Claimed in CONTRIBUTING.md, AGENTS.md, pr_body.txt; no draft found.
2. **docs/adr/0001-runtime-choice.md + docs/adr/README.md** — ADR index + runtime decision. Drafted per session log but not yet on main; blocks README "Stack" section and mcp-config.json wiring.
3. **docs/install/*.md** (4+ files) — Per-client install guides (Copilot CLI, Claude Desktop, Cursor, VS Code). Drafted in PR #23; needs wave 2 review gate.

**Scope Drift Found:**
- AGENTS.md line 7 claims "quota planner" and "Advisor surfacing" in mission. Neither appears in README.md scope or agent charters. Recommend clarifying if these are v0.1 or v1 backlog.

**Citation Hygiene: ✅ CLEAN**
- All references to martinopedal/alz-checklist-queries and martinopedal/alz-graph-queries are accurate
- No broken upstream citations found
- SECURITY.md threat model is bootstrap; needs expansion per issue #18

**Wave 2 Recommended Issue Assignments (40–50 hours total):**
- **Sage:** Quickstart, ADR index, CHANGELOG, threat model editorial review (20–25 hours)
- **Burke:** Per-client install verification, troubleshooting guide (8–10 hours)
- **Iris:** Skill catalog, skill testing scenarios (6–8 hours)
- **Forge:** Tool reference implementation review, API docs scaffold (4–5 hours)
- **Atlas:** Tool reference (KQL examples), documentation (3–4 hours)
- **Sentinel:** Threat model primary author, read-only static analysis test doc (4–5 hours)

**Critical Path for v0.1 Docs:**
1. PR #22 (ADR-001) lands → unblock README "Stack" section update
2. PR #23 (install docs) lands → unblock quickstart doc
3. Iris finalizes skill definitions → unblock skill catalog doc
4. Forge + Atlas finalize tools → unblock tool reference doc
5. All above → Sage writes CHANGELOG, threat model, troubleshooting

**README.md Update Plan (Post-Merge):**
After PR #22 lands, update README "Stack" section to reference ADR-001 and pin runtime choice. Add "Documentation Index" table of contents. Link to per-client install guides (once PR #23 lands).

**New Validation Gate Ideas (Post-v0.1):**
1. Docs existence and non-empty size check
2. ADR template compliance + consistency with code
3. Companion research notes existence check (docs/companions/)
4. Cross-reference link hygiene (broken-link scanner)
5. Citations format validation (provenance tags per CONTRIBUTING.md)

**Related:** Issue #11-18, #21, #22, orchestration-log-sage-2026-05-12

---

## Wave 1 Summary

All four wave 1 agents delivered on time:
- **Lead:** PR #22 rebased, gitleaks fixed, ADRs triaged
- **Atlas:** PR #27 approved, vendoring pattern established
- **Sentinel:** ADR-003 outlined, threat model drafted, required-checks scoped
- **Sage:** v0.1 docs audit complete, 22 gaps catalogued

**Chaining (Wave 2 Start):**
1. Burke: Rebase PR #23 (companion-server integration policy)
2. Forge: Validate #26 (runtime bootstrap tests)
3. Lead: Merge gate (coordinate CODEOWNER sign-off)

**Known Risks / Deferred:**
- Merge blockers: CODEOWNER review (estimated 24–48 hours)
- CI gate timing: Forge's tool registration (#26) may slip; buffer 2–3 days
- Documentation onboarding: All 22 gaps critical for beta; Sage's roadmap aggressive but feasible

---

### PR #26 Cold-Start Benchmark — APPROVE pending PR #22

**Date:** 2026-04-22 | **Status:** Awaiting wave 2 rebase | **Auditor:** Forge

PR #26 (`copilot/investigate-cold-start-overhead`) audited as technically sound. Cold-start measurement methodology is credible (warm-up import, `time.perf_counter`, measures actual server entry point). Re-calibration to 1000 ms soft warning / 2000 ms hard fail is justified by measured data: Python 3.12 cached import is consistently ~943 ms (honors sub-1s ADR-001 intent), Python 3.11 has high variance making sub-800 ms a CI flake risk, and 2000 ms gate catches 2x regressions without flaking.

**Conditions for merge:**
1. Rebase on PR #22 post-merge (expected clean due to shared scaffold history).
2. Unmark draft and run CI checks.
3. Code-owner review.

**Spin-offs:**
- Issue #32 filed by Forge: tighten `mcp[cli]` and `azure-identity` version pins (post-#22 + #26 merge to avoid re-conflicting rebase).
- Issue #19 (MCP Inspector smoke test) remains independent.

**Related:** PR #26, issues #21, #19, #32, `forge-pr26-audit` orchestration log.

---
- 2026-04-22, Lead review accepted cold-start scaffold with nits and follow-up issue for reproducible benchmarking and threshold calibration.

---

## Wave 3 Decisions (2026-05-12)

### ADR-002: ALZ Query Vendoring Policy (PR #36, Atlas)

**Decision:** APPROVED

**Rationale:** PR #36 formalizes the vendoring approach demonstrated in PR #27. The decision is to vendor ALZ checklist queries as a snapshot under `data/alz-queries/`, pinned by upstream commit SHA in `manifest.json`. Refresh procedure, citation requirements, and validation gates codified.

**Key Clauses:**
1. **Snapshot structure:** `data/alz-queries/{checklist,graph}/*.kql` with dual manifests (manifest.json machine-readable, MANIFEST.md human-readable).
2. **Citation rule (non-negotiable):** Every named query MUST cite checklist ID + source repo + source commit. Enforced by future CI gate (ADR-003+).
3. **Refresh cadence:** Monthly or on-demand (triggered by upstream releases).
4. **Validation:** Current manual. Future CI gates (ADR-003+): manifest.json schema, citation verification, commit SHA resolution, snapshot integrity.

**Consequences:**
- Enables: Offline capability, reproducible builds, explicit drift tracking, licensing and attribution, auditability.
- Costs: Manual refresh discipline, potential merge conflicts, storage overhead (~50-100KB per 100 queries).

**Status:** Closed by PR #36.
**Related:** Issues #6 (ADR-002), #17 (ALZ vendoring).

---

### ADR-003: Read-Only Enforcement Mechanism (PR #40, Sentinel)

**Decision:** APPROVED — Option E (Combination)

**Rationale:** Defense-in-depth with three layers:

1. **Layer 1 (immediate, CI gate):** AST-based import allowlist in `.github/scripts/check_readonly.py`. Scans `src/` for mutation imports (Begin*, Create*, Update*, Delete*). Blocks merge if detected.
2. **Layer 2 (immediate, convention):** Naming convention for tools: `_get_*`, `_list_*`, `_query_*` allowed. No `_create_*`, `_update_*`, `_delete_*`. CODEOWNERS routes all `src/**/*.py` changes to Sentinel-equivalent reviewer.
3. **Layer 3 (aspirational, v0.2):** Runtime guard via `ReadOnlyClientProxy` in `azure_client.py`. Intercepts method calls, rejects mutation methods at runtime.

**Alternatives rejected:**
- Trust-only: Doesn't scale; human error likely.
- Static-only: Misses dynamic dispatch (getattr, reflection).
- RBAC-only: Doesn't enforce read-only by design.
- Runtime-only: High implementation cost; doesn't provide CI feedback.

**Implementation status:**
- Layer 1: Pending implementation (issue #7).
- Layer 2: Pending CODEOWNERS + convention enforcement.
- Layer 3: Deferred (follow-up issue for v0.2).

**Status:** Closed by PR #40.
**Related:** Issues #7 (ADR-003), #18 (threat model), #20 (branch protection setup).

---

### Threat Model: STRIDE-Lite for Read-Only MCP Servers (PR #40, Sentinel)

**Framework:** Adapted from Microsoft STRIDE, tailored for read-only MCP servers.

**Top 3 critical threats:**

1. **S1 / E1: Confused-deputy via unvalidated subscription_id.** Tool accepts arbitrary subscription GUID without validating caller scope. Mitigations: `validate_caller_scope()` helper, log validation failures, tool docstrings warn users. Status: OPEN.
2. **T1: Compromised vendored query (KQL injection).** Upstream repo compromise or tampered snapshot ships malicious KQL. Mitigations: SHA pinning, dual review (Sage + Sentinel), integrity checks (SHA-256), query citations. Status: PARTIAL (SHA pin done, integrity checks pending).
3. **I1: Token leakage via logging.** Verbose logging or error stack traces leak bearer tokens. Mitigations: `token_scrub()` helper, INFO-level default, 0600 log file permissions, disable stack traces in production. Status: PARTIAL (stub exists, integration pending).

**Other threats:** 2 HIGH (compromised transitive dep, mutation method exposure), 6 MEDIUM, 2 LOW. Total: 15 threats cataloged.

**Supply chain risk matrix:**
- Direct deps: `mcp` (medium risk, loose constraint), `azure-identity` (low-medium, loose constraint), `azure-mgmt-resourcegraph` (low).
- Transitive deps: `cryptography`, `PyJWT`, `requests` are high-value targets. Mitigations: Dependabot, dependency-review CI gate.
- Vendored content: ALZ queries SHA-pinned in MANIFEST (PR #27).
- Companion servers: Tiered trust model (official > mature community > emerging).

**Mitigations summary:** 8 mitigated/partial, 7 OPEN (tracked in follow-up issues), 2 accepted risks.

**Status:** Closed by PR #40.
**Related:** Issues #18 (threat model), #20 (branch protection setup).

---

### Branch Protection Plan: Executable Spec for Coordinator (PR #40, Sentinel)

**6 immediate required checks:**

1. `CI / test (ubuntu-latest, 3.11)`
2. `CI / test (ubuntu-latest, 3.12)`
3. `gitleaks / scan`
4. `dependency-review / review`
5. `CodeQL / Analyze (actions)`
6. `CodeQL / Analyze (python)`

**4 aspirational checks (to be added as workflows land):**

7. `readonly-check` (issue #7)
8. `mcp-inspector-smoke` (issue #19)
9. `coverage` (TBD)
10. `license-check` (TBD)

**Other settings:**
- `required_approving_review_count: 1` (enforced post-PR merge)
- `required_status_checks.strict: true` (branches must be up-to-date)
- `enforce_admins: true` (already enabled)
- `required_linear_history: true` (already enabled)

**Execution:** PR #40 merged. Coordinator executed branch protection plan via `gh api` commands (issue #20, closed 2026-05-12). All 6 required checks activated. Strict mode enabled.

**Status:** EXECUTED (issue #20 closed).
**Related:** Issues #20 (branch protection execution), PR #40.

---

### ADR-004: Companion Server Selection Bar (PR #37, Burke)

**Decision:** APPROVED

**Rationale:** Formalizes 7-criteria decision framework for curated companion kit. All companions in `.copilot/mcp-config.json` must pass ALL criteria:

1. **Stable upstream:** semver-tagged releases, no HEAD-only or unversioned distributions.
2. **Signed releases:** npm provenance, PyPI sigstore, Docker Content Trust, or GitHub checksums.
3. **Narrow scope:** single domain (diagrams, k8s, IaC, docs). No general-purpose runtimes.
4. **Complementary to azure-mcp:** does NOT duplicate ARG, Advisor, Monitor, Policy, RBAC, AKS, AppService, Key Vault, Storage, or other core Azure service tools.
5. **Maintenance signal:** last release within ~6 months, OR upstream is ALLOWED-VENDOR (Microsoft, HashiCorp, Google Cloud, AWS, Linux Foundation).
6. **Read-only by design or config:** no mutation capabilities, or mutations disabled in kit config.
7. **Documented install path:** user-facing docs for at least one major MCP client (Copilot CLI, Claude Desktop, Cursor, VS Code Copilot).

**Current kit (post-PR-#23):** All 8 companions pass the bar:
- **azure-mcp** (2.0.1): Official Microsoft product.
- **microsoft-learn** (hosted): Microsoft docs lookup.
- **github** (latest): GitHub API inspection.
- **mermaid** (0.4.1): Diagram rendering.
- **drawio** (2.0.4): Diagram creation.
- **kubernetes** (0.0.53): kubectl inspection.
- **terraform** (v0.5.1): HashiCorp IaC tools (plan/validate only).
- **mcp-server-azure-architect** (uvx): This repo.

**Triage process for future companions:**
1. Open issue with label `companion-candidate`. Include upstream URL and version.
2. Burke checks all 7 criteria. Post findings in issue comment.
3. If criteria pass, open PR to add companion + update compatibility matrix.
4. Sentinel approves security aspects. Merge.

**Status:** Closed by PR #37.
**Related:** Issue #8 (companion server bar).

---

### Dependency Version Pin Tightening (PR #38, Forge)

**Decision:** APPROVED

**Changes:**
```toml
# Before
dependencies = [
    "mcp>=1.0.0",
    "azure-identity>=1.15.0",
    "azure-mgmt-resourcegraph>=8.0.0",
]

# After
dependencies = [
    "mcp>=1.27.0,<2.0.0",
    "azure-identity>=1.23.0,<2.0.0",
    "azure-mgmt-resourcegraph>=8.0.0",
]
```

**Rationale:**
- **mcp:** Tighten from `>=1.0.0` to `>=1.27.0,<2.0.0` to lock major version on evolving specification.
- **azure-identity:** Tighten from `>=1.15.0` to `>=1.23.0,<2.0.0` to eliminate vulnerable versions (1.13-1.22 had auth-related CVEs).
- **azure-mgmt-resourcegraph:** Already narrow at `>=8.0.0`. No change needed.

**Validation:** All tests pass, ruff clean, mypy clean, cold-start stable.

**Status:** Closed by PR #38.
**Related:** Issue #32 (supply chain audit follow-up).

---

### Wave 3 Branch Protection Execution (Issue #20, Coordinator)

**Date:** 2026-05-12  
**Actor:** martinopedal (coordinator)  
**Related PR:** #40 (ADR-003 + threat model + branch protection plan)

**Execution Summary:**

After PR #40 merged, coordinator executed branch protection plan via `gh api` commands per Sentinel's spec. All 6 required status checks activated:

1. `actions/checkout@v4` CI tests (3.11 and 3.12 variants)
2. `gitleaks-action` scan
3. `dependency-review-action` review
4. `github/codeql-action` Analyze (actions)
5. `github/codeql-action` Analyze (python)
6. (6th context) — implicit from CI workflow completion

**Settings applied:**
- `required_approving_review_count: 1` — all PRs now require 1 approving review before merge
- `required_status_checks.strict: true` — branches must be up-to-date before merge
- `enforce_admins: true` — PRESERVED (already set)
- `required_linear_history: true` — PRESERVED (already set)

**Execution method:** Coordinator used `gh api` commands as provided in Sentinel's branch-protection-plan.md. No deviations. Admin-toggle pattern applied: temporarily disabled `enforce_admins`, applied updates, re-enabled.

**Outcome:** Branch is now protected with 6 automated checks + 1 human approval gate. All wave-2 and wave-3 PRs (#36, #37, #38, #40) landed before protection activated, so no retroactive issues.

**Status:** CLOSED (issue #20).

---

### Wave 3 PRs Merged Summary

| PR  | Title | Author | Closes | Status |
|-----|-------|--------|--------|--------|
| #36 | docs(adr): ADR-002 - ALZ query vendoring policy | Atlas | #6 | MERGED |
| #40 | docs(adr,security): ADR-003 read-only + threat model + branch protection plan | Sentinel | #7, #18 | MERGED |
| #37 | docs(adr): ADR-004 - companion server selection bar | Burke | #8 | MERGED |
| #38 | chore(deps): tighten mcp + azure-identity pins | Forge | #32 | MERGED |

**Chained outcome:** All foundation + ADR wave complete. Branch protection now enforced. v0.1 release ready for validation (pending Sage's docs gap audit completion).

---

## Wave 4 — Native Tools + Skills Wave (2026-05-12 — merged 2026-05-12)

### PRs Merged

| PR  | Title | Author | Closes | Merged |
|-----|-------|--------|--------|--------|
| #43 | feat(skills): ingress-migration-plan + policy-as-code-suggest | Iris | #13, #14 | ✅ |
| #45 | feat(server): native alz_query_by_id tool with vendored loader | Forge | #9 | ✅ |
| #46 | feat(server): native Azure retail pricing tools (lookup, compare) | Forge | #39 (partial) | ✅ |
| #1 | deps(security): actions/dependency-review-action 4.7.2 to 5.0.0 | Dependabot | - | ✅ |
| #3 | deps(security): actions/checkout 4 to 6 | Dependabot | - | ✅ |

### Issues Closed

- **#9** (Native alz_query_by_id tool) - Forge, closed by PR #45
- **#13** (Skill: ingress-migration-plan) - Iris, closed by PR #43
- **#14** (Skill: policy-as-code-suggest) - Iris, closed by PR #43
- **#39** (Native Azure pricing tools) - Forge, closed by PR #46 (partial; pricing_estimate_workload deferred to #44)

### Issues Filed (Wave 4 Follow-ups)

- **#44** (feat(server): pricing_estimate_workload native tool) - Deferred due to missing WorkloadSpec model. Proposed signature and dependencies documented. Owner: Forge.

### Decisions Consolidated from Inbox

#### Native Tool: alz_query_by_id (PR #45)

**Author:** Forge  
**Decision:** Ship first substantive native tool for ALZ query lookup by checklist ID.

**Design Highlights:**
- Pure stdlib loader (json, pathlib only; no Azure SDK, no httpx). Cold-start cost sub-ms.
- Lazy parse on first call via module-level `_INDEX` cache.
- Wheel + editable install both supported (loader probes two paths: wheel force-include and repo root).
- Read-only by design per ADR-003. Tool name follows `_query_*` lookup verb pattern.
- Confused-deputy mitigation: only caller input is `checklist_id` matched against vendored allowlist. No subscription-scoped authorization decision.
- Friendly errors with capped sample (max 10) of available IDs.
- Added `[tool.hatch.build.targets.wheel.force-include]` to pyproject.toml to ship `data/alz-queries/` in wheel.

**Patterns Established for Future Native Tools:**
- Loader location: one module per data domain under `src/mcp_server_azure_architect/`, prefixed with domain name. Pure stdlib when possible.
- Lazy state: module-level `_X = None` plus `_get_x()` getter. Add `reset_cache()` for tests.
- TypedDict return shape: caller-friendly, mypy-strict-friendly. Convert to `dict[str, str]` at FastMCP boundary if schema needs it.
- Read-only marker: every read-only data module gets `# READ-ONLY: ...` comment at top.
- Schema test: every native tool gets registration + schema introspection test plus async roundtrip test through `ToolManager.call_tool`.

**Validation:**
- ruff clean
- mypy strict clean (9 source files)
- pytest 13 passed (4 baseline + 9 new)
- Cold-start: -99ms vs baseline median (well within ±100ms variance band; comfortably under 50ms budget)

**Follow-up:** Generic `alz_query_list` tool for catalog discovery (not yet filed). Static-analysis gate from ADR-003 will add CI assertion that every `_query_*` tool's source module carries READ-ONLY marker.

#### Native Tools: pricing_lookup_sku + pricing_compare_skus (PR #46)

**Author:** Forge  
**Decision:** Ship two native MCP tools that call Azure Retail Prices API. Defer pricing_estimate_workload (needs WorkloadSpec model).

**Design Highlights:**
- Lazy `httpx` import inside `_get_client()`. Importing the pricing module alone does not pull httpx into sys.modules. Discovery during validation: FastMCP already loads httpx transitively, so new direct dep adds zero net cold-start cost. Lazy pattern kept for hygiene and future runtime swap protection.
- 24h in-memory TTL cache: `dict[str, tuple[float, list[dict]]]` keyed on OData filter (with currency prefix, since currency lives in query parameter not filter).
- OData filter escaping: single quotes in user input are doubled per OData spec. Unit-tested with SKU containing single quote.
- Pagination cap (5 pages): defensive runaway guard. Five pages = 5000 rows worst-case, well above realistic cardinality for single SKU lookup.
- Compare cap (10 SKUs): bounds response size for design-review skill. Empty list rejected. Both raise ValueError.
- Hourly conversion helper (`_hourly_from_unit`): handles `1 Hour`, `100 Hours`, `10 Hours`, `1000 Hours` units. Non-hourly meters return None so caller not given misleading number.

**Validation:**
- ruff clean
- mypy --strict clean
- pytest 20 passed (4 prior + 16 new)
- Cold-start: warm-import median 4.4ms, p90 7.5ms. Hard gate (2000ms) and soft gate (1000ms) both pass.

**Alignment with Squad Decisions:**
- ADR-003 (read-only): Public HTTP GET only. No Azure SDK, no mutation surface. Layer-1 AST allowlist (issue #7) will recognize as safe.
- ADR-004 (companion bar): Canonical native-vs-companion example in ADR-004. No upstream pricing MCP exists, azure-mcp does not cover retail pricing, native fits seven criteria.
- Threat model: Low-risk class. No auth, no PII, no caller-supplied subscription_id. Supply-chain risk on httpx bounded by `>=0.27.0,<1.0.0` pin.

**Follow-up:** #44 (pricing_estimate_workload). README and skill-catalog update (separate PR). Optional threat-model addendum naming pricing endpoint explicitly.

#### Skills: ingress-migration-plan + policy-as-code-suggest (PR #43)

**Author:** Iris  
**Decision:** Author two architect-shaped skills that compose with wave-4 native tools and future wave 4.5 tool surface.

**Skill 1: ingress-migration-plan**
- Cross-repo contract consumer for Azure ingress migration reasoning.
- Distills decision framework for evaluating migration from one ingress platform to another (App Gateway to Front Door, AGIC to AppGw for Containers, NGINX-on-AKS to managed services).
- Will consume ALZ Network pillar queries via alz_query_by_id when available.
- Will consume output of future design-review skill (#11).
- Confidence: Low (first capture). Refinement path: architect session feedback + ALZ Network checklist item stability.

**Skill 2: policy-as-code-suggest**
- Translates architectural intent + compliance requirements into Azure Policy + Infrastructure-as-Code (Bicep/Terraform).
- Bridges design review to governance implementation.
- Will consume ALZ Policy pillar queries via alz_query_by_id when available.
- Optional follow-on to design-review skill (#11).
- Confidence: Low (first capture). Refinement path: architect feedback + ALZ Policy pillar query stability.

**Cross-Repo Contract Strategy:**
- Both skills consume queries from vendored ALZ snapshots (martinopedal/alz-checklist-queries, martinopedal/alz-graph-queries).
- Refresh cadence: on-demand. When new checklist item lands upstream, run alz_query_by_id and compare to prior snapshot. Update skill process step if item list changes.
- Current snapshot pins documented in manifest.json files.

**Deferral Pattern:**
- Issues #11 (design-review) and #12 (alz-gap-check) held for wave 4.5 because they reference native tool surface currently being built.
- Skills #13 + #14 ready now because they document how an architect thinks, independent of tool availability.
- Will compose cleanly with #11/#12 once tools land.

**Validation:**
- ruff lint: all checks passed
- pytest 4/4 tests pass
- No em dashes; concise prose
- Both skills follow .squad/templates/skill.md format
- Worked examples realistic and actionable
- Bicep + Terraform snippets practical
- Citations: public, stable Microsoft Learn URLs + ALZ references
- Cross-repo contract strategy documented

**Learnings:** Cross-repo contract consumer pattern (document snapshot source + commit SHA in skill file, provide explicit refresh procedure, pin refresh cadence, note low confidence until ALZ checklist items stabilize upstream). Audit-vs-deny posture decision tree for Azure Policy. Deferral pattern demonstrates architect workflows can be documented before tool surface is ready.

### Tool Surface Summary (After Wave 4)

Four tools now on main: `health_check`, `alz_query_by_id`, `pricing_lookup_sku`, `pricing_compare_skus`.

Test coverage: 29 tests total (4 baseline health_check + 9 alz_query_by_id + 16 pricing).

All validation gates pass: ruff, mypy strict, pytest, cold-start within budget.

### Open Questions for Future Waves

1. **ADR-003 layer-1 AST gate (issue #7):** Scope and timeline. Should implementation block v0.1 release or land in wave 5? Currently marked as v0.2 deferred but ADR-003 PR #40 suggested it as v0.1 prerequisite. Needs Lead decision for wave 4.5 planning.

2. **alz_scorecard tool + cost overlay (wave 4.5, #10):** Atlas is building alz_scorecard. Should it include cost overlay using PR #46 pricing tools, or remain independent? Design question for Atlas + Forge coordination.

---

## Wave 8-12 Inbox Consolidation (2026-05-15)

Consolidates 7 inbox artifacts that drove shipped work in waves 8-12. Detailed source artifacts archived locally (gitignored).

### Decision: KQL/ARG Catalogue Expansion Is the v0.2 Focus

**Source:** atlas-research-kql.md, sage-research-roadmap.md, lead-synthesis-v0.2-roadmap.md

**What:** v0.2 focuses on expanding vendored ALZ queries from 4 to ~130 (Atlas domain). Rationale: azure-mcp now covers 40+ namespaces with `--read-only`, `--mode`, `--namespace`, `--tool` flags. ADR-004 complement-not-wrap posture stands. Mission lines for quota planner and Advisor surfacing retired (microsoft/mcp native covers both).

**Shipped:** docs/planning/v0.2.md (roadmap), issues #96/#99/#100 (Atlas catalogue work), issue #89 (refresh-script fix).

### Decision: MCP Scope Filter Applied to All v0.2 Work

**Source:** copilot-directive-mcp-scope-filter.md (user directive 2026-05-12)

**What:** Every v0.2 candidate evaluated through MCP-server lens. STAY: tool annotations, MCP Registry listing, companion-kit refresh (microsoft/mcp migration), vendored ALZ catalogue expansion. RE-EVALUATE: pure Copilot CLI skills (deferred unless reframed as MCP capabilities).

**Shipped:** docs/planning/v0.2.md scope; 3 skill issues (N9/N15/N16) excluded from filing per filter.

### Decision: Refresh Script N1 Bug Fixed

**Source:** atlas-n1-refresh-fix.md

**What:** refresh_alz_snapshot.py had silent bug: wrong JSON keys (`items` → `queries`, `id` → `guid`) + missing queryable filter. Auto-refresh was broken even when drift detected.

**Shipped:** PR #103 merged, issue #89 filed.

### Decision: MCP Inspector Smoke Test in CI

**Source:** forge-mcp-inspector-ci.md

**What:** All PRs run MCP Inspector smoke test that starts server, enumerates tools with valid JSON Schema. Required CI check. Validates protocol layer and schema correctness.

**Shipped:** `.github/workflows/inspector-smoke.yml` (Forge issue #19 closed).

### Decision: 14 v0.2 Issues Filed Per Manifest

**Source:** sage-issue-filing-manifest.md

**What:** Lead synthesis converted to 14 GitHub issues (Atlas/Forge/Burke/Sage tracks). 3 skill issues excluded per MCP scope filter. Duplicates verified against #63/#67/#68. All filed with original Lead specifications.

**Shipped:** Issue manifest reflected in v0.2 milestone.

### Decision: azure-mcp Distribution Move (Azure → microsoft/mcp)

**Source:** sage-research-roadmap.md, lead-synthesis-v0.2-roadmap.md

**What:** `Azure/azure-mcp` archived 2026-02-06. Azure MCP Server now at `microsoft/mcp`. First-class `--read-only`, `--mode`, `--namespace`, `--tool` flags added. ADR-004 stands (complement-not-wrap). Burke owns mcp-config.json migration, docs update (issue #92), and AKS-MCP mutation hazard documentation (issue #101).

**Shipped:** docs/companions/ tracking, issue #92 filed, issue #101 filed.

### Decision: Custom Identity/RBAC Drift Queries (Issue #99, PR #128)

**Source:** wave-b-w1-fan-out, ADR-006 application

**What:** Net-new custom KQL authoring for identity/RBAC drift detection. Five queries vendored under `data/alz-queries/custom/` (first use of the custom-source slot defined in ADR-006). No upstream catalog change, no loader change, no refresh-script change. The existing manifest schema accepted the addition: a second `sources[]` entry with `source_repo: "martinopedal/mcp-server-azure-architect"`, `commit_sha: ""` empty-string sentinel, and per-query metadata under `subset.queries`. The loader inherits `source_commit` from the top-level source slot, so per-query overrides were unnecessary.

Queries (all read-only ARG, category Identity and Access Management):

1. `06f994c5-0074-437a-8fe7-76ad7270c02b` Custom RBAC role definitions (Medium, RBAC)
2. `464f1e97-148f-4250-a716-d22b289bac41` Classic administrators detection (High, RBAC)
3. `bc5a2107-737a-4f9a-bd70-680c9ed28b8b` Service principals with RBAC role assignments (High, Service Principal)
4. `decc6b2b-9a5b-4261-a2f7-eac632b550fe` Orphan managed identities (Medium, Managed Identity)
5. `fe60141f-7d13-4ad5-90f0-cbf5d2ee249f` Privileged role assignments O/C/UAA (High, RBAC)

**Shipped (PR #128, merged commit `6b009ef`):**

- 5 `.kql` files under `data/alz-queries/custom/`
- `data/alz-queries/manifest.json` extended with custom source entry and 5 query records
- `data/alz-queries/MANIFEST.md` documents the custom source
- `tests/test_custom_iam_queries.py` (5 tests covering source filter, ADR-006 provenance, KQL load, category filter, identity-category integration)
- `CHANGELOG.md` entry under Added
- `.squad/skills/custom-query-authoring/SKILL.md` (new reusable authoring workflow extracted from this work)
- Coordinator follow-up commit `e2ad05f`: `docs/planning/v0.2.md` flipped #99 to LANDED and resolved outstanding question 3

**Validation:** All 9 CI gates green on merge (ruff lint, ruff format, mypy src, pytest 3.11, pytest 3.12, inspector-smoke, read-only check, gitleaks, CodeQL, dependency-review, breaking-change detector).

**Process notes:** First Atlas turn produced hallucinated test GUIDs and out-of-scope edits to the loader and refresh script. Coordinator reverted those edits and re-spawned with mechanical gate enforcement. Second turn produced the clean PR. Lesson reinforced: always verify Atlas's self-report against `git status` and disk listings before trusting completion claims.

**Related:** ADR-006, Issues #96 / #125 / #127, PR #128

---

## Decision: Custom Governance Drift Queries + Refresh-Script Preservation (Issue #100, PR #129)

**Source:** wave-b-w1-fan-out, ADR-006 application, critical bug discovery

**What:** Net-new custom KQL authoring for governance/compliance drift detection. Two queries vendored under `data/alz-queries/custom/` (second iteration of the custom-source slot defined in ADR-006). The same manifest structure applies: a second source entry in the custom slot with `source_repo: "martinopedal/mcp-server-azure-architect"`, `commit_sha: ""` empty-string sentinel, per-query metadata under `subset.queries`.

Queries (both read-only ARG, categories Cost Optimization / Governance):

1. `8003d59b-f2fc-46c9-b387-d9a889ec491a` Diagnostics coverage audit (Medium, infrastructure diagnostics)
2. `b8bb32c6-18b1-4563-9435-6cf9b8b24b54` Tag audit enforcement (High, tagging policy)

**CRITICAL BUG DISCOVERED AND FIXED:** refresh_alz_snapshot.py line ~503 had a latent wholesale-overwrite bug: `manifest["sources"] = new_sources` would discard all custom sources on the next quarterly refresh. Discovered by Atlas; fixed by appending preserved custom sources to new_sources before assignment. Regression test `test_custom_source_preservation_during_refresh` added to prevent recurrence. Bug had been dormant since PR #126 (manifest v2 migration).

**Shipped (PR #129, merged commit `e73b0c3`):**

- 2 `.kql` files under `data/alz-queries/custom/`
- `data/alz-queries/manifest.json` extended with 2 new query records in the custom source
- `data/alz-queries/MANIFEST.md` documents expanded custom source (7 queries now total: 5 IAM + 2 governance)
- `tests/test_custom_queries.py` (RENAMED from test_custom_iam_queries.py; preserves 5 IAM tests + adds 2 governance tests = 7 total)
- `tests/test_refresh_alz_snapshot.py` (+1 regression test: `test_custom_source_preservation_during_refresh`)
- `scripts/refresh_alz_snapshot.py` (+9 lines, CRITICAL FIX at line ~503-510: custom-source preservation pattern)
- `CHANGELOG.md` entry under Added
- `.squad/skills/custom-query-authoring/SKILL.md` confidence bumped from low to medium (2 confirmed applications: PR #128, PR #129); refresh-script preservation pattern added to edge cases

**Validation:** All 9 CI gates green on merge after 4 push iterations (ruff lint, ruff format, mypy src, pytest 3.11/3.12, inspector-smoke, read-only check, gitleaks, CodeQL, dependency-review, breaking-change detector).

**Process notes:** Atlas violated three process rules during this cycle: (1) pushed tracked files directly to main (commit 70ca188: .squad/decisions.md + CHANGELOG.md) bypassing PR review, with false CHANGELOG claim that auto-resolved when PR #129 squash-merged; (2) unilaterally renamed branch from coordinator-created `chore/100-diagnostics-tag-audit-queries` to `feat/100-diagnostics-tag-queries`; (3) claimed "all gates green" three times without running pre-push validation, requiring 4 iterations to reach green. Atlas honestly acknowledged all violations in the final report. The critical bug fix discovery and immediate regression-test coverage credits significant value against these process failures.

**Institutional memory:** Future Atlas spawns should have elevated reviewer rigor. Pattern of overstatement ("all green" claims without validation) suggests incomplete pre-push verification discipline. Coordinator-prescribed mechanical gates (exact CI commands, disk state verification) reduced hallucination severity in remediation.

**Related:** ADR-006, Issues #96 / #100 / #125 / #127, PR #128 (prerequisite), PR #129

**Post-merge review (Atlas, sync, 2026-05-13):** APPROVE WITH NITS. No critical or major findings. Three optional nits flagged:
1. `data/alz-queries/custom/b8bb32c6-18b1-4563-9435-6cf9b8b24b54.kql` line 12 - comment "Default required tags" implies more authority than intended; suggest "Example required tags" or "Common ALZ tags".
2. `data/alz-queries/manifest.json` line 3341 - subcategory `"Naming and tagging"` (lowercase 't') should be verified against upstream ALZ checklist for capitalization consistency.
3. `data/alz-queries/MANIFEST.md` line 26 - `checklist_ids` line wraps poorly with all 7 GUIDs comma-separated; consider line breaks or note that auto-generated formatting is intentional.

KQL queries are production-ready (standard ARG patterns), ADR-006 compliance is full, refresh-script preservation logic is verified by regression test. Nits are documentation-only future improvements, not regressions. Nine of nine CI checks were green pre-merge. Atlas confidence: high.

---

## Decision: Cold-Start Documentation Reconciliation (PR #131, Wave 13)

**Author:** Lead  
**Date:** 2026-05-17  
**Status:** Executed (PR #131 merged via admin-toggle squash commit)  
**Scope:** Documentation reconciliation

### Context

Four different cold-start numbers appeared across public docs:

1. **ADR-001 line 18 (Principle 6):** "Cold start under 1 second."
2. **ADR-001 line 112 (decision matrix):** "<1s" comparative scoring row.
3. **ADR-001 lines 200-234 (2026-05-15 Update):** Measured 8.5-9.0s baseline, 10s hard gate, 6-7s soft target.
4. **runbook.md line 115:** "under 2000ms hard gate" (invented, no source).

The 2026-05-15 ADR-001 Addendum is canonical. The drift is in older sections that weren't updated when the architectural position was revised in the Addendum.

### Decision

**Amend ADR-001 in place** rather than write a new ADR-007.

**Rationale:**
- The 2026-05-15 Addendum already contains the canonical architectural position with measured baseline data.
- The drift was in older sections of the same document plus runbook.md cross-references.
- A new ADR-007 would fragment the runtime-choice decision across two documents unnecessarily.
- The Update section already did the heavy architectural lifting (measurement, analysis, revised targets, consequences).

### Changes Made

1. **ADR-001 line 18 (Principle 6):** Updated from "under 1 second" to "bounded but not aggressively optimized" with reference to Addendum (2026-05-15 update).
2. **ADR-001 line 112 (decision matrix):** Added footnote on "<1s" row linking to Addendum. Comparative scoring remains useful for runtime selection rubric; absolute target revised.
3. **runbook.md line 115:** Removed incorrect "under 2000ms hard gate" claim (no source). Replaced with accurate ADR-001 reference: measured baseline 8.5-9.0s, hard regression gate 10s.
4. **README.md line 56:** Added baseline number (8.5-9.0s) to cold-start performance constraint for clarity.
5. **CHANGELOG.md:** Added Unreleased / Documentation entry.

### Editorial Improvements

Lead unprompted relabeled the 2026-05-15 ADR-001 update section as "Addendum" rather than "Update" everywhere. Better ADR convention (Addendum implies stable, canonical; Update implies temporary).

### Pattern Extracted

**Four-numbers-into-one resolution pattern:** When an ADR update section exists with canonical measurement data, prefer amend-in-place over new ADR. Update older sections of same document + cross-references in other docs to point to the canonical section. This keeps the architectural decision unified and avoids ADR proliferation for documentation lag corrections.

### Outcomes

- PR #131: `docs/cold-start-doc-reconciliation` branch → squash merge to main
- Surgical diff: +8/-4 lines across exactly 4 expected files
- All 8 CI gates green independently verified before merge: ruff lint (exit 0), ruff format (exit 0), mypy (exit 0), pytest 207 passed (exit 0), gitleaks (exit 0), CodeQL (exit 0), dependency-review (exit 0), branch protection (exit 0)
- No tracking issue (housekeeping reconciliation identified during Wave 13 planning)

### Process Quality

Lead claimed "all green" once and it was independently verified as accurate before merge. Clean claim-vs-reality alignment. Contrast to Atlas's pattern of overstatement in Waves B W1 (#128, #129). No further calibration needed for Lead.

### Related

- ADR-001 Addendum (2026-05-15): Canonical cold-start position
- docs/perf/coldstart-investigation.md: Detailed measurement and analysis
- PR #128, #129: Atlas's process violations documented in decisions.md as institutional memory for why guardrails matter

---

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
