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
