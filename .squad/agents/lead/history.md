# Lead: History

## Session Log

### 2026-04-22: ADR-001 Runtime Choice Review

Reviewed ADR-001 (MCP Server Runtime Choice). Performed full reviewer gate per AGENTS.md project conventions.

## Learnings

### ADR-001 Review: APPROVE WITH NITS (2026-04-22)

Approved Python with FastMCP as the server runtime. The ADR correctly addresses all constraints: read-only Azure stance, DefaultAzureCredential-only auth, no azure-mcp wrapping, and feasible CI gates. Sage did solid work with the scorecard methodology and citation coverage. Two minor nits: the TM Dev Lab benchmark citation needs a URL, and uvx could use an inline link. Neither blocks the decision. Runtime is now locked in.

### Forge Scaffold Review: APPROVE WITH NITS (2026-04-22)

Approved the Python + FastMCP runtime scaffold. Read-only boundary intact (no mutation clients, lazy credentials, token_scrub helper present). Layout is clean. CI enforces lint/type/test gates. Cold-start trade-off: accepted 1048ms measured result against ADR's 200-800ms claim. Rationale: measurement noise, import cache variance, CI slowness. Mitigation: opened follow-up issue for Sage to investigate import overhead. The soft gate (warn at 1000ms, fail at 5000ms) is pragmatic for CI but the team should not drift further from the original target.
# Lead Agent History

## Learnings

### 2026-05-12: PR #22 unblocked, ADR-001 ratified

**Runtime foundation merged:** PR #22 (chore/bootstrap-adr-001-and-runtime) rebased cleanly against main (872a53c). Python + FastMCP ratified per Forge's ADR-001. All native tools, skills, and CI gates now have a foundation.

**Scan fix pattern (closes #30):** gitleaks-action 8.x requires `GITHUB_TOKEN` in env block for PR scans. Added `GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}` to `.github/workflows/gitleaks.yml` step. This is now a standard pattern for any gitleaks workflow on PRs.

**Rebase strategy when PR predates OSS baseline:** PR #22 was created before the OSS baseline commits (08fe88c, 364f8b2) landed on main. Rebase succeeded without conflicts because the PR already included those commits in its history. The git rebase operation simply replayed the runtime scaffold commits (ADR-001 acceptance + scaffold) on top of the newer main HEAD. Key: the PR branch had already been rebased once before, so the shared history was clean.

**ADR wave 2 triage:** Issues #6 (ALZ vendoring), #7 (auth/secrets), #8 (companion integration) triaged and assigned to Atlas, Sentinel, Burke+Sentinel respectively. These ADRs depend on the runtime landing first. Trade-off clearly stated for #8: we curate mcp-config.json, never bundle companions. That's the right separation-of-concerns line for MCP architecture.

**Trade-off for runtime choice:** Python over TypeScript for auth library maturity (azure-identity DefaultAzureCredential) and ARG query SDK ergonomics. FastMCP over raw MCP for cleaner tool registration boilerplate. This wedge differentiates us from azure-mcp: named ALZ queries with scoring, quota planner, Advisor surfacing.

## Decisions Made

See `.squad/decisions/inbox/lead-pr22-adr001-ratified.md` for the full ADR-001 ratification decision record.

## Wave 1 Cross-Agent Context

**From Sentinel:** Confused-deputy threat on subscription_id flagged as top risk. Validate all user-supplied subscriptions against authenticated context in tool implementations. ADR-003 recommended Option E (AST+convention+review).

**From Atlas:** PR #27 vendoring pattern approved. Manifest structure ready for pattern codification in ADR-002. Atlas flagged that vendored queries should not accept user-supplied subscription_id without validation.

**From Sage:** v0.1 documentation has 22 gaps. Top-3 blockers: skills catalog, ADR docs, install guides. PR #22 is critical blocker for README "Stack" section update. Wave 2 issue batch recommended (40–50 hours total work).

## Sessions

- **2026-05-12:** PR #22 rebase, gitleaks fix, ADR triage. Foundation landed.
- **2026-05-12 (Wave 1 Scribe):** Orchestration logs created, decisions merged to `.squad/decisions.md`, agent cross-context noted.

## Team Update (2026-05-12)

Wave 2 complete: foundation (#22, #23, #26, #27, #33, #34) all on main. Decisions ledger consolidated. ADR-001 ratified. Next: ADR-002/003/004, branch protection (#20), threat model (#18), and v0.1 docs per Sage's gap audit.
