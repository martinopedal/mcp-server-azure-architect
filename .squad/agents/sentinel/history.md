# Sentinel: History and Learnings

**Last Updated:** 2026-04-22
**Session:** Skeleton outlines and supply chain audit

## Completed Work

### Session 1: ADR-003, Threat Model, and Supply Chain Audit (2026-04-22)

**Artifacts:**
- `.squad/decisions/inbox/sentinel-adr-003-readonly-outline.md` — ADR-003 skeleton with 5 decision options (Convention, Static Analysis, Runtime Guard, Custom Plugins, Combination).
- `.squad/decisions/inbox/sentinel-threat-model-outline.md` — STRIDE-lite threat model with supply chain risk matrix and companion-server pinning policy.
- `.squad/decisions/inbox/sentinel-required-checks.md` — 10 required CI status checks for branch protection (dependencies, security, linting, type-safety, functional, read-only, MCP, build).

**Dependency Audit Findings:**

| Package | Current | Latest | Constraint | Age Risk | CVE Risk | Recommendation |
|---------|---------|--------|------------|----------|----------|---|
| `mcp[cli]` | 1.27.0 | 1.27.1 | >=1.0.0 | ⚠️ HIGH | Low | Tighten to >=1.27.0; monitor weekly. |
| `azure-identity` | 1.25.3 | 1.25.3 | >=1.15.0 | ⚠️ MEDIUM | Low-Medium | Upgrade minimum to >=1.23.0 (end-2024 releases); had CVEs in 1.13-1.16 range. |
| `azure-mgmt-resourcegraph` | 8.0.1 | 8.0.1 | >=8.0.0 | Low | Low | Good pin. No action needed. |

**Key Findings:**
1. **mcp constraint is dangerously loose** (`>=1.0.0` allows any future major version). MCP is still evolving; should pin to at least the current minor (1.27.x).
2. **azure-identity has 10 minor versions of slack** (constraint allows 1.15, current is 1.25). Older versions (1.13-1.16) had auth-bypass CVEs (check Azure Security Advisory history). Recommend bumping minimum to >=1.23.0.
3. **azure-mgmt-resourcegraph is safe** (read-only surface, no mutation methods; pinned correctly).
4. **No direct dependency on cryptography, PyJWT, or requests listed** in direct deps, but both `mcp[cli]` and `azure-identity` pull them in transitively. These are high-value targets for supply-chain attacks. Mitigation: Dependabot + dependency-review in CI (issue #20).

**Open Actions:**
- [ ] Tighten `mcp[cli]>=1.0.0` to `>=1.27.0` (or current stable) in pyproject.toml.
- [ ] Upgrade `azure-identity>=1.15.0` to `>=1.23.0` in pyproject.toml.
- [ ] Wire dependency-review and gitleaks into CI (issue #20; being folded into PR #22 by Lead).
- [ ] Implement token-scrub helper and integrate into logging (threat model mitigation).
- [ ] Implement read-only static analysis gate (ADR-003).
- [ ] Create `.github/scripts/check_readonly.py` (sentinel-required-checks.md step 1).

## Threat Model Summary

**Top 3 Threats (by exploitability):**
1. **Confused-Deputy via unvalidated subscription_id** — Tool accepts arbitrary subscription string; without validation, AI agent can probe subscriptions outside caller's scope. Mitigation: validate against authenticated context.
2. **Token Leakage via Logging** — Azure SDK or tool errors may log bearer tokens or secrets. Mitigation: token-scrub helper on all logging paths.
3. **Compromised Vendored Query** — If `alz-checklist-queries` repo is compromised, injected KQL could exfiltrate data or cause DoS. Mitigation: snapshot SHA pinning + Sage + Sentinel review.

**Supply Chain Chain Risk:**
- Direct deps are Microsoft / Python-official (low risk).
- Transitive deps (cryptography, PyJWT, Requests) are high-value targets. Mitigation: Dependabot + dependency-review.
- Companion servers: All Microsoft or official (HashiCorp, GitHub) are trusted. Community packages (mermaid, drawio, kubernetes) require version pin + freshness check.

## ADR-003 Leaning

**Recommended Option:** E (Combination: Static Analysis + Convention + Code Review)

**Rationale:**
- Static analysis (AST or grep-based import check) catches 95% of mutation imports automatically.
- Convention + code review catches indirect cases and documents intent.
- Runtime guard deferred to v2 if call surface grows.
- Fits a small Python codebase; scales to TypeScript/Rust if runtime changes.

**Key Design Decision:**
- Static analysis gate is a **hard CI blocker** (issue #7, validation gate in AGENTS.md).
- False positives suppressed via `# noqa: sentinel-readonly` in code.
- Only scans `src/`, not `site-packages/` (transitive deps are out of scope).

## Companion-Server Pinning Policy

**All servers must specify version pins in mcp-config.json:**
- npm packages: `@latest` → `@1.2.x` (major.minor pin).
- Docker containers: no `latest` tag; use digest or semantic version.
- Official sources (Microsoft, HashiCorp): weekly update reviews.
- Community packages: freshness check (last update <6 months) + >100 stars before inclusion.

**Policy enforcement:** PR review gate by Sentinel. Update PRs require Sage research note.

## Notes for Future Sessions

1. **When runtime ADR lands** (Sage + Lead decide on Python vs TypeScript vs .NET), Forge should immediately implement the static analysis check (check_readonly.py or equivalent). Use this skeleton as the spec.

2. **CI validation gates** (sentinel-required-checks.md) assume the runtime is chosen. Once runtime is known:
   - Customize linter/formatter (ruff for Python, eslint for TS, roslyn for .NET).
   - Implement MCP Inspector smoke test (runtime-agnostic; per MCP spec).
   - Adjust coverage threshold based on codebase maturity.

3. **Token scrubbing** is foundational. Implement early (before first tool ships). Template: regex-based redaction in a logging handler.

4. **Dependency scanning:** Once CI is wired, set up Dependabot on a weekly cadence (GitHub native; no additional action needed, just enable in repo settings). Consider adding `pip-audit` or `safety` in CI as well.

5. **Vendored snapshots:** Track in `.squad/vendor/MANIFEST.md` (not created yet):
   ```
   # ALZ Query Snapshots Manifest
   ## alz-checklist-queries
   - Source: https://github.com/martinopedal/alz-checklist-queries
   - Snapshot Commit: <SHA>
   - Date: <YYYY-MM-DD>
   - Verified by: Sage
   - SHA256: <hash>
   ```

## Learnings

### Session 2: ADR-003 Layer-1 AST Gate + Threat Model Issue Filing (2026-05-12)

**Artifacts:**
- `scripts/check_readonly.py` — AST-based readonly enforcement (ADR-003 layer 1)
- `tests/test_check_readonly.py` — 16 tests covering all mutation patterns
- `.github/workflows/readonly-check.yml` — CI gate for readonly enforcement
- `.squad/decisions/inbox/sentinel-readonly-ast-gate.md` — Design decision artifact (gitignored)
- 7 GitHub issues filed for threat-model OPEN items (#57-#63)

**Implementation Choices:**
1. **AST over regex.** Precise detection, no false positives from comments or strings. Python stdlib only.
2. **Opt-out via `readonly-allow:` comment.** Line-level suppression with advisory reason requirement.
3. **String method allowlist.** Excluded `str.replace()` to avoid false positives while still catching `client.delete_*()`.
4. **Pattern-based detection.** Prefix-based (begin_, create_, delete_, etc.) catches Azure SDK mutations; exact-match alone causes too many false positives.

**False Positive Handling:**
- Initial approach used exact-match for bare `delete`, `create`, `update`, `replace`. This flagged `str.replace()` in pricing.py.
- Refined approach: only detect prefix-based patterns (delete_, create_, etc.). Bare method names require contextual judgment (Layer 2 code review).
- Added `readonly-allow:` comment to pricing.py line 57 as documentation, though script now skips `replace` entirely.

**Validation Results:**
- 16/16 tests pass
- 57/57 total pytest suite passes
- ruff, mypy clean
- Real source tree (src/) has zero violations

**Filed Issues:**
1. #57: S1 - Confused-Deputy via Unvalidated subscription_id (CRITICAL)
2. #58: R1 - Tool Execution Not Logged (MEDIUM)
3. #59: R2 - Log Tampering (LOW)
4. #60: I2 - Sensitive Data in Query Results (MEDIUM)
5. #61: I3 - World-Readable Log Files (MEDIUM)
6. #62: D1 - Large Query Result Overwhelms MCP Channel (MEDIUM)
7. #63: T1 - Integrity Checks for Vendored Queries (CRITICAL, assigned to Atlas)

All issues include Definition of Done section with concrete acceptance criteria.

**Lessons:**
- AST analysis is straightforward for Python. Stdlib `ast` module handles all edge cases (multiline calls, nested expressions).
- Heuristic allowlists (e.g., excluding `replace`) are pragmatic but require documentation. Bare method names like `delete()` are context-dependent.
- Test the real source tree. `test_real_source_tree_has_no_violations` acts as a CI canary and caught the str.replace() false positive immediately.
- Line-level opt-out is the right granularity. Reviewers can audit each suppression in PR context.

### Threat Modeling for Read-Only MCP Servers

**Pattern:** STRIDE-lite adapted for read-only MCP servers, emphasizing:
- Confused-deputy (unvalidated caller scope).
- Token leakage (logging, error messages).
- Supply chain (transitive deps, vendored content, companions).
- Input validation (tool parameters must be constrained).

This pattern is reusable for other read-only MCP servers (e.g., azure-mcp itself, or compliance-query services).

### Static Analysis for Read-Only Enforcement

**Pattern:** AST-based or grep-based import check that blocks mutation methods in Azure SDK classes.

**Why it works:**
- Mutation methods are named consistently (`Begin*`, `Create*`, `Update*`, `Delete*`).
- Azure SDK imports are well-known (`azure.mgmt.*`, `azure.storage.*`).
- Python's `ast` module or simple regex can scan imports in O(n) time.

**Generalization:** Any read-only tool can use this pattern. Implementation detail varies by language (Python AST, Go `ast`, Rust `syn`, etc.).

### Companion-Server Supply Chain Policy

**Pattern:** Tiered trust model for recommending third-party MCP servers.

1. **Official sources** (Microsoft, HashiCorp, GitHub): Signed, pinned, auto-update on policy.
2. **Mature community** (Terraform, K8s): Version-pinned, quarterly review, explicit approval.
3. **Emerging community**: Require freshness, stars, research note, Sentinel review.

This pattern scales to a registry of recommended servers.

## Wave 1 Cross-Agent Context

**From Lead:** ADR-001 (Python + FastMCP) ratified and merged. PR #22 foundation landed. Gitleaks pattern documented. Your ADR-003 outline + required-checks skeleton will feed into Forge's CI gate implementation post-merge.

**From Atlas:** PR #27 ALZ snapshot audit complete (APPROVED). Manifest structure sound. Recommendation: ADR-003 read-only gate should validate that vendored queries do not accept user-supplied subscription_id without validation (your confused-deputy threat applies to data queries too).

**From Sage:** v0.1 docs gap audit complete. Threat model expansion (your detailed STRIDE analysis) is a top-3 priority for v0.1 confidence. Suggest: after ADR-003 ratification, write user-facing threat model summary (docs/threat-model.md) for architects unfamiliar with STRIDE.

## References

- ADR-003 Skeleton: `.squad/decisions/inbox/sentinel-adr-003-readonly-outline.md` (now in `.squad/decisions.md`)
- Threat Model Skeleton: `.squad/decisions/inbox/sentinel-threat-model-outline.md` (now in `.squad/decisions.md`)
- Required Checks Skeleton: `.squad/decisions/inbox/sentinel-required-checks.md` (now in `.squad/decisions.md`)
- Issue #7: ADR-003
- Issue #18: Threat model
- Issue #20: CI gates
- Orchestration Log: `.squad/orchestration-log/20260512T000000Z-sentinel.md`

## Team Update (2026-05-12)

Wave 2 complete: foundation (#22, #23, #26, #27, #33, #34) all on main. Decisions ledger consolidated. ADR-001 ratified. Next: ADR-002/003/004, branch protection (#20), threat model (#18), and v0.1 docs per Sage's gap audit.

---

## Session 2: ADR-003 Final + Threat Model + Branch Protection Plan (2026-05-12)

**PR:** #40 (docs/adr-003-readonly-and-threat-model)  
**Closes:** #7 (ADR-003), #18 (threat model)  
**Sets up:** #20 (branch protection execution by coordinator)

**Artifacts delivered:**

1. **`docs/adr/0003-read-only-enforcement.md`** (242 lines)
   - Ratifies Option E from wave-1 outline: defense-in-depth with 3 layers
   - Layer 1: AST-based import allowlist (CI gate, `.github/scripts/check_readonly.py`)
   - Layer 2: Convention + CODEOWNERS (naming: `_get_*`, `_list_*`, `_query_*` allowed)
   - Layer 3: Runtime guard (aspirational, v0.2+)
   - Format matches ADR-001 structure
   - Status: Accepted (2026-05-12, Sentinel)

2. **`docs/security/threat-model.md`** (503 lines)
   - STRIDE-Lite analysis using `.squad/skills/stride-lite-mcp-readonly/SKILL.md` framework
   - 15 threats cataloged: 3 CRITICAL, 2 HIGH, 6 MEDIUM, 2 LOW, 2 accepted risks
   - Top 3 critical: confused-deputy (S1/E1), compromised vendored query (T1), token leakage (I1)
   - Supply chain risk matrix: direct deps, transitive deps, vendored content, companion servers
   - 8 mitigations in place or partial, 7 OPEN (tracked in follow-up issues)
   - Rationale for each threat includes attack vector, example, and concrete mitigation

3. **`docs/security/branch-protection-plan.md`** (285 lines)
   - Executable spec for coordinator to apply after PR merge
   - 6 immediate required checks + 4 aspirational checks
   - Settings: `required_approving_review_count=1`, `strict=true`, preserve `enforce_admins` and `required_linear_history`
   - `gh api` commands with exact syntax for apply + rollback
   - Admin toggle procedure for coordinator merge (disable, merge, re-enable)
   - Test plan included (dry-run on test branch)

4. **`docs/adr/README.md`** (updated)
   - Added ADR-003 to index

**Validation:** Ruff clean, pytest 4/4 passed.

**Key Decisions:**

- **ADR-003 Option E (combination) ratified.** Balances safety, cost, transparency. Layer 1 provides immediate CI feedback. Layers 2+3 add incremental safety. Alternatives rejected: trust-only (doesn't scale), RBAC-only (doesn't enforce read-only by design), static-only (misses dynamic dispatch).

- **Threat model identifies 3 CRITICAL threats:**
  1. **Confused-deputy via unvalidated subscription_id.** Mitigation: `validate_caller_scope()` helper (OPEN).
  2. **Compromised vendored query (KQL injection).** Mitigation: SHA pinning (done), dual review (documented), integrity checks (OPEN).
  3. **Token leakage via logging.** Mitigation: `token_scrub()` stub exists, integration OPEN.

- **Supply chain risk matrix:** Direct deps are Microsoft/official (low-medium risk, loose constraints). Transitive deps (`cryptography`, `PyJWT`, `requests`) are high-value targets (Dependabot + dependency-review in place, lockfile discipline OPEN). Vendored content SHA-pinned (PR #27). Companion servers follow tiered trust model.

- **Branch protection plan as executable spec.** 6 immediate checks (CI/test, gitleaks, dependency-review, CodeQL). 4 aspirational checks (readonly-check, mcp-inspector-smoke, coverage, license-check). Coordinator runs `gh api` commands after PR merge. Admin toggle required for coordinator merge (disable `enforce_admins`, merge, re-enable).

**Follow-Up Actions:**

1. Implement ADR-003 layer 1: `.github/scripts/check_readonly.py` + CI integration (issue #7, blocker for v0.1).
2. Create tracking issues for OPEN threat mitigations (Sentinel task).
3. Execute branch protection plan (coordinator task, issue #20).
4. Add CODEOWNERS for `src/**/*.py` routing to Sentinel-equivalent reviewer (Lead task).
5. Tighten dependency constraints: `mcp>=1.27.0`, `azure-identity>=1.23.0` (Forge, issue #32).

**Patterns and Learnings:**

### Pattern: Multi-Layer Enforcement ADRs

When a non-functional requirement (e.g., read-only, no-telemetry, no-network-in-tests) is critical:

1. **Layer 1 (CI gate, immediate):** Fast, automated, actionable feedback. Low false positives. Blocks merge if violated.
2. **Layer 2 (convention + review, immediate):** Human judgment, naming clarity, enforced via CODEOWNERS.
3. **Layer 3 (runtime guard, aspirational):** Catch dynamic cases (reflection, getattr). High implementation cost; defer to v2 unless essential.

This pattern balances safety, cost, and transparency. Reusable for other enforcement scenarios.

### Pattern: STRIDE-Lite for Read-Only MCP Servers

Adapt STRIDE for domain-specific threat models. For read-only MCP servers:

- **S (Spoofing):** Confused-deputy (unvalidated caller scope)
- **T (Tampering):** Supply chain (transitive deps, vendored data)
- **R (Repudiation):** Audit logging
- **I (Information Disclosure):** Token leakage, log permissions
- **D (Denial of Service):** Result size limits, query complexity
- **E (Elevation of Privilege):** Mutation method exposure

Focus on attack surface unique to the domain. Skip irrelevant categories. Provide concrete mitigations with status tracking. Reusable for other read-only tools (compliance checkers, audit viewers).

### Pattern: Branch Protection as Executable Spec

Document branch protection settings as executable `gh api` commands, not prose. Benefits:

- Coordinator can copy-paste commands (no translation).
- Rollback procedures are actionable (not aspirational).
- Test plan included (dry-run on test branch).
- Phased approach: immediate checks (already in CI) + aspirational checks (added as workflows land).

Reusable for any repo protection documentation.

### Threat Model Sequencing Insight

**ADR-003 + threat model must land together.** ADR-003 ratifies enforcement mechanism. Threat model justifies why enforcement is critical (T and E threats). Splitting them breaks the narrative. Branch protection plan is a natural third artifact (enables enforcement via CI gates).

### Admin Toggle for Branch Protection Merge

**Context:** When `enforce_admins: true`, the coordinator (who is admin) cannot merge even with approvals. Must temporarily disable `enforce_admins`, merge, then re-enable immediately.

**Pattern:** Document this in branch protection plan with explicit commands. Warn that re-enable is CRITICAL (do not leave disabled). Include validation step (`gh api` to confirm `enforce_admins` is back to true).

**Risk:** If coordinator forgets to re-enable, all protections can be bypassed. Mitigation: automation script that wraps disable-merge-enable in a single transaction. Tracked as future improvement.

## Learnings

### ADR Format Evolution

**Observation:** ADR-003 expands on ADR-001's format. New sections added:

- **What "Read-Only" Means:** Defines scope (no mutation methods, no LROs, no credential writes).
- **Threat Model Context:** Cross-references `docs/security/threat-model.md` for STRIDE context.
- **Implementation Status:** Tracks which layers are immediate vs. aspirational.
- **Open Questions Resolved:** Addresses all open questions from wave-1 outline.

**Generalization:** ADRs for enforcement mechanisms should include:
1. Scope definition (what does "X" mean concretely?).
2. Threat context (why enforce X?).
3. Implementation status (what's immediate vs. deferred?).
4. Resolved open questions (from outline to final).

### Threat Model Mitigation Status Discipline

**Pattern:** Every threat includes a **Status** field: OPEN, PARTIALLY MITIGATED, MITIGATED, ACCEPTED RISK. OPEN threats reference tracking issues (issue #TBD until created). PARTIALLY MITIGATED threats list what's done and what's pending.

This enables audit: external reviewers can verify mitigation status against GitHub issues. Quarterly threat model reviews can update status as issues close.

### Supply Chain Risk Levels

**Pattern:** Classify dependencies as Low, Medium, High risk based on:

- **Official sources** (Microsoft, HashiCorp, GitHub): Low risk (signed, actively maintained).
- **Mature community** (>1 year old, >100 stars, frequent updates): Low-Medium risk.
- **Unmaintained** (>1 year without update) or **unknown provenance**: High risk.
- **Loose version constraints** (e.g., `>=1.0.0` allows any 1.x): Elevate risk by one level (Low → Medium, Medium → High).

Transitive deps are always Medium-High risk (not directly controlled). Mitigation: Dependabot, lockfile, periodic audit (pip-audit, safety).

### Branch Protection Phased Rollout

**Pattern:** Don't block on aspirational checks. Apply immediate checks (already in CI) now. Add aspirational checks as workflows land. Each addition is a single `gh api` command that replaces the entire contexts list (include all existing + new).

**Rationale:** Applying non-existent checks blocks all PRs indefinitely. Phased approach balances safety (enable protections now) with pragmatism (don't block on unimplemented checks).

**Rollback discipline:** If a required check breaks, coordinator can remove it from contexts list without losing other protections. Rollback procedure documented in plan.

## Cross-Agent Context

**From Lead:** Wave 2 foundation complete. ADR-003 + threat model are top priority for v0.1 confidence. Branch protection execution (issue #20) is coordinator task, will follow after this PR merges.

**From Forge:** Issue #32 tracks dependency constraint tightening (`mcp>=1.27.0`, `azure-identity>=1.23.0`). Will address after ADR-003 lands. ADR-003 layer 1 implementation (`.github/scripts/check_readonly.py`) is Forge task, tracked in issue #7.

**From Atlas:** PR #27 ALZ snapshot audit complete. SHA pinning and MANIFEST implemented. Threat model (T1) references this as partial mitigation. Integrity checks (SHA-256 validation in CI) are next step, tracked in issue #TBD.

**From Sage:** v0.1 docs gap audit complete. Threat model expansion (STRIDE-lite) is a top-3 priority for v0.1 confidence. User-facing threat model summary (for architects unfamiliar with STRIDE) is a follow-up task, tracked in docs roadmap.

## References

- **PR #40:** https://github.com/martinopedal/mcp-server-azure-architect/pull/40
- **Issue #7:** ADR-003 read-only enforcement
- **Issue #18:** Threat model + supply chain doc
- **Issue #20:** Branch protection
- **PR #27:** Atlas's ALZ snapshot audit (SHA pinning, MANIFEST)
- **Issue #32:** Forge's dependency constraint tightening
- **Wave 1 outlines:** `.squad/decisions.md` (Sentinel entries)
- **STRIDE-lite skill:** `.squad/skills/stride-lite-mcp-readonly/SKILL.md`
- **Decision artifact:** `.squad/decisions/inbox/sentinel-adr-003-final.md`

## Wave 3 Outcomes (2026-05-12)

**ADR-003, threat model, and branch protection plan merged (PR #40, closed #7, #18).** All three artifacts now ratified and documented. Coordinator executed branch protection plan immediately post-merge: 6 required checks + 1 approval gate now enforced for all future PRs. No retroactive issues (all wave-3 PRs landed before protection activated).

**Cross-agent alignment verified.** Atlas's ADR-002 vendoring policy aligns with threat model T1 (compromised vendored query). Burke's ADR-004 companion selection bar (criterion 6: read-only design) aligns with E1 threat (mutation method exposure). Forge's dependency tightening (PR #38) addresses T threat (compromised transitive deps). All enforcement layers (CI + convention + runtime) documented in ADR-003; layer 1 (CI gate) now assigned to Forge (issue #7, blocker for v0.1).

**Supply chain risk discipline established.** Threat model supply chain section + Burke's companion pinning policy + Forge's dependency constraints create unified supply chain posture. Future companion candidates (issue #39: pricing tools) will be evaluated against both ADR-004 (companion bar) and threat model (supply chain risk level). Quarterly threat model reviews now standard (recommended 2026-08-12).

## Audit Consolidation: Third-Party Notices (2026-05-13)

**Completion:** Consolidated duplicate THIRD-PARTY-NOTICES files (PR #118).

**Issue:** Two committed third-party-notices files with confusing duplicate naming:
- `THIRD-PARTY-NOTICES.md` (hyphen) — vendored ALZ data licenses, ships in wheel.
- `THIRD_PARTY_NOTICES.md` (underscore) — companion server attributions + MCP spec, does not ship.

**Resolution:** Merged into the hyphen file with two clearly-scoped sections:
- **Vendored content (bundled in wheel):** Full LICENSE text reproduced as required by licenses.
- **Companion MCP servers (recommended via mcp-config.json, not bundled):** Summary attributions; full licenses live with upstream projects.

Removed duplicate ALZ entries (they appeared in both files). Deleted underscore file to eliminate naming-convention duplication. pyproject.toml line 82 and README.md line 134 references verified — no changes needed.

**Learning:** Naming consistency for multi-source attribution files prevents audit confusion. When vendored and companion content coexist, one consolidated file with clearly labeled sections is preferable to separate files by deployment scope (ships vs. recommended only).

**Related:** PR #114 (vendored ALZ data), ADR-004 (companion server bar), threat model T1 (compromised vendored query).
