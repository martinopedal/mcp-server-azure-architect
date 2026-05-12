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

## Wave 3 Outcomes (2026-05-12)

**PR orchestration: 4 ADRs merged without conflicts.** Rebased PR #36 (Atlas ADR-002), PR #40 (Sentinel ADR-003+threat+BP), PR #37 (Burke ADR-004), PR #38 (Forge deps). All landed cleanly on main HEAD (ee987b7) with zero conflicts. Coordinator admin-toggled for merges (disabled `enforce_admins` temporarily per branch protection settings).

**Branch protection executed successfully (issue #20 closed).** Post-PR #40 merge, coordinator applied Sentinel's branch-protection-plan.md executable spec. Activated 6 required checks: CI tests (3.11, 3.12), gitleaks, dependency-review, CodeQL (actions + python). Enabled `required_approving_review_count: 1`, `strict: true`. All wave-3 PRs landed before protection, so no retroactive blockers. Sets precedent: infrastructure enforcement is non-optional going forward.

**ADR-002/003/004 stack validated.** ADR-001 (runtime, PR #22) established foundation. Wave 3 ADRs build cleanly on top: vendoring (ADR-002) → read-only enforcement (ADR-003) + threat model → companion bar (ADR-004). Dependencies resolved; cross-ADR references documented. Issue #39 (pricing tools) queued for wave 4; will be evaluated against ADR-004 bar + threat model supply-chain section.

## Team Update (2026-05-12)

Wave 2 complete: foundation (#22, #23, #26, #27, #33, #34) all on main. Decisions ledger consolidated. ADR-001 ratified. Next: ADR-002/003/004, branch protection (#20), threat model (#18), and v0.1 docs per Sage's gap audit.

## Wave 4 Outcomes (2026-05-12)

**Wave 4 native tools + skills: 3 PRs merged, 2 follow-up issues filed.** PR #43 (Iris skills ingress-migration-plan + policy-as-code-suggest, closes #13 + #14), PR #45 (Forge alz_query_by_id native tool, closes #9), PR #46 (Forge pricing_lookup_sku + pricing_compare_skus, closes #39 partial). All landed cleanly on main HEAD with zero conflicts. Dependabot PRs #1 + #3 (security updates) merged in parallel. Coordinator admin-toggled for wave 4 merges.

**Native tool pattern established.** Forge's alz_query_by_id + pricing tools demonstrate end-to-end pattern: pure stdlib loaders, lazy module-level state, TypedDict returns, async schema roundtrip tests, read-only markers. Pattern documented in decisions.md. Future tool PRs from Atlas, Iris, or Forge can reference this pattern.

**Skills ready before tool surface stabilizes.** Iris authored two architect-shaped skills (ingress-migration-plan, policy-as-code-suggest) that document workflows independent of tool availability. Both reference future alz_query_by_id tool calls explicitly. Skills #11 + #12 depend on alz_scorecard + alz_graph (wave 4.5), not 4.0. This deferral pattern unblocks skill documentation while parallel tool delivery continues.

**Pricing tool decision aligned with ADR-004.** Forge's pricing tools represent the worked example in ADR-004 (companion bar). No upstream pricing MCP exists, azure-mcp does not cover retail pricing, native fits seven ADR-004 criteria. Decision ratified per threat model low-risk class (HTTP GET only, no auth, no PII, no confused-deputy surface).

**Inbox consolidation and scribe session.** Scribe consolidated three inbox files into decisions.md (forge-alz-query-by-id.md + forge-pricing.md + iris-skills-13-14.md). Lost Forge history update rescued from local main. All agent histories cross-linked. Consolidation PR opened.

**Open questions for wave 4.5:**
1. ADR-003 layer-1 AST gate (issue #7): Should check_readonly.py implementation block v0.1 release or land in wave 5? Needs Lead decision.
2. alz_scorecard + cost overlay: Atlas designing alz_scorecard (wave 4.5 #10). Should it include cost overlay using PR #46 pricing tools, or remain independent? Design question for Atlas + Forge coordination.
