# Sage: Research and Documentation History

## Learnings

### 2026-04-22: ADR-001 Runtime Choice

**Decision:** Recommended Python with FastMCP for the MCP server runtime.

**Key Citations:**
- MCP Specification, Tool Definition Schema: [modelcontextprotocol.io/specification/tools#tool-definition-schema](https://modelcontextprotocol.io/specification/tools#tool-definition-schema)
- MCP SDKs Overview: [modelcontextprotocol.io/docs/sdk](https://modelcontextprotocol.io/docs/sdk)
- All three candidate runtimes (Python, TypeScript, .NET) are Tier 1 MCP SDKs with official support from Linux Foundation (Python, TS) or Microsoft (.NET).
- Cold start benchmarks: Python FastMCP 200-800ms, TypeScript 300-700ms, .NET 300-1500ms (optimized <500ms with AOT).
- Azure SDK quality: .NET is gold standard (10/10), Python is mature (8/10), TypeScript is solid (7/10).

**Gotchas Discovered:**
1. **Cold start is measurable but not always documented.** FastMCP does not publish official cold start metrics. Had to infer from multi-language benchmarks and typical Python import times.
2. **MCP Inspector compatibility is a CI gate.** All three SDKs pass, but this is non-negotiable. Must validate in CI on every PR.
3. **JSON Schema generation varies by runtime.** FastMCP auto-generates from type hints (easiest). TypeScript requires `typescript-json-schema` (predictable). .NET uses reflection with `NJsonSchema` (enterprise-friendly).
4. **Distribution story matters.** uvx (Python), npx (TypeScript), dotnet tool (.NET) all work, but uvx and npx are ephemeral-first, while dotnet tool requires explicit install. For a tool, ephemeral is better.
5. **Contributor friction is not just language familiarity.** Build steps, type system strictness, and ecosystem norms all factor in. Python wins on no-build-step, TypeScript loses on tsc requirement, .NET loses on enterprise-heavy perception.

**Weighted Decision Criteria:**
- Scored on 8 criteria: MCP SDK maturity, Azure SDK quality, cold start, install/distribution, JSON Schema tooling, ecosystem fit, contributor friction, MCP Inspector compatibility.
- Python: 247, TypeScript: 229, .NET: 222.
- Cold start (weight 5) and contributor friction (weight 4) tipped the scale toward Python.

**Skill Extraction Candidate:**
- MCP SDK comparison rubric (8 criteria, weights, scoring guide). Could be generalized for any MCP server runtime decision. Will write `.squad/skills/mcp-runtime-evaluation/SKILL.md` if pattern reuse is needed.

---

### 2026-04-22: Cold-Start Performance Investigation (Incoming)

**Incoming issue:** "perf: Investigate cold-start overhead (target <800ms)" — assigned squad:sage.

Forge measured 1048ms on cold start (48ms over ADR-001 target). Lead approved with nits and opened this investigation for you. Scope: profile `mcp[cli]` import cost vs minimal `mcp` dependency, test lazy imports for azure-identity, confirm Python 3.11 baseline (dev machine appeared to be running 3.14). Goal: bring measured cold start under 800ms or update ADR with revised expectation and citation.
# Sage: Session History

## 2026-04-22 — Documentation Gap Audit for v0.1

**Deliverable:** `.squad/decisions/inbox/sage-docs-gap-audit.md`

### Task Executed

Performed a comprehensive documentation gap audit for the v0.1 release. Cross-referenced what's claimed in README.md, CONTRIBUTING.md, AGENTS.md, .github/copilot-instructions.md, and open issues against what actually exists on main.

### Key Findings

**Docs that exist on main (15):**
- All 7 root markdown files (README, CONTRIBUTING, SECURITY, AI_GOVERNANCE, AGENTS, THIRD_PARTY_NOTICES, LICENSE)
- All 9 agent charters in .squad/agents/*/charter.md
- All 29 training skills in .copilot/skills/*/SKILL.md (governance, not user-facing)
- Configuration files (.github/copilot-instructions.md, .copilot/mcp-config.json)
- .squad/ governance docs (team, routing, decisions, identity, ceremonies)
- tests/skills/test_alz_gap_check_replay.md (exists on main, referenced in pr_body.txt)

**Claimed but missing (22):**
- `docs/` directory (doesn't exist)
- `docs/adr/` directory and all ADRs (ADR-001 drafted per session log but not on main)
- `docs/install/` directory and per-client guides (drafted in PR #23 but not on main)
- `docs/skills/catalog.md` (referenced in CONTRIBUTING, AGENTS, pr_body.txt; no draft found)
- `docs/companions/` directory (referenced in CONTRIBUTING)
- `docs/perf/` directory (referenced in issue #21; cold-start investigation in progress)
- `queries/MANIFEST.md` (referenced in CONTRIBUTING and THIRD_PARTY_NOTICES; planned in issue #17)
- `queries/` directory itself (doesn't exist)
- `scripts/` directory and installer scripts (referenced in issue #16)
- `.github/extensions/` directory (referenced in pr_body.txt but no extension on main)

**In open PRs (10+):**
- PR #22: ADR-001 runtime choice (critical blocker for README "Stack" section)
- PR #23: Per-client install docs (4+ files)
- Issue #17 (planned PR): queries/MANIFEST.md
- Issue #7, #8 (planned PRs): ADR-003 and ADR-004
- Issue #11, #21 (planned PRs): alz-gap-check extension and cold-start docs
- Issue #18 (planned PR): SECURITY.md threat model expansion

**Needed for v0.1, no issue yet (8):**
1. docs/quickstart.md (5-min walkthrough)
2. docs/tools/reference.md (API docs for alz_query_by_id, alz_scorecard)
3. docs/skills/catalog.md (complete, all four skills)
4. docs/threat-model.md (expanded from SECURITY.md bootstrap)
5. docs/troubleshooting.md
6. CHANGELOG.md or docs/releases/v0.1.md
7. docs/adr/README.md (ADR index and process)
8. docs/CONTRIBUTING-with-Squad.md (internal, low priority)

### Scope Drift Found

- **AGENTS.md line 7** claims "quota planner" and "Advisor surfacing" in the mission. Neither appears in README.md scope or any agent charter. Recommendation: clarify if these are v0.1 or v1 backlog.

### Citation Hygiene Check

- ✓ AI_GOVERNANCE.md, AGENTS.md, CONTRIBUTING.md, .github/copilot-instructions.md all correctly cite martinopedal/alz-checklist-queries and martinopedal/alz-graph-queries
- ✓ No broken upstream citations found
- ✓ SECURITY.md threat model is bootstrap; needs expansion per issue #18

### Recommendations for Wave 2

1. **Route 8 new doc issues to Sage/Burke/Iris/Forge/Atlas/Sentinel** per the audit's suggested assignments (40-50 hours total work)
2. **Critical path:** PR #22 (ADR-001) must land first to unblock README "Stack" section
3. **Parallel work:** PR #23 (install docs), Iris skill finalization, Forge/Atlas tool finalization can proceed in parallel
4. **Validation gate addition:** Once v0.1 is shipped, add CI gates for doc existence, ADR integrity, broken link detection

### Files Produced

- `.squad/decisions/inbox/sage-docs-gap-audit.md` (19,979 bytes)
  - **What exists:** 15 docs, with exact file paths and coverage
  - **Claimed but missing:** 22 docs, with claim source and responsible agent
  - **In open PRs:** 10+ docs with PR number and status
  - **Needed for v0.1:** 8 docs with suggested owners and effort estimates
  - **Recommended issue creation list:** Issue skeletons for wave 2
  - **Citation hygiene check:** Cross-reference accuracy vs. upstream sources
  - **README.md update plan:** Changes needed once PRs land
  - **Validation gate implications:** Future CI enhancements

### How to Use This Audit

1. **Lead:** Review this audit and the inventory tables
2. **Lead:** Use "Recommended Issue Creation List" to create wave 2 issues
3. **Lead:** Tag each issue with the suggested owner's squad label
4. **Wave 2 agents:** Pick up your labeled issues from the squad inbox
5. **Scribe:** After PRs land, move this decision from inbox to active decisions

### Learnings for Future Documentation Audits

1. **Separate governance docs from user-facing docs early.** This repo mixes .squad/ governance (29 training skills, team charters) with user-facing docs (docs/, README). Makes the audit harder to follow.
2. **Document doc requirements in an ARCHITECTURE.md or DOCS.md early.** The audit had to infer from scattered claims in README, CONTRIBUTING, AGENTS.md, and issue bodies what "complete docs for v0.1" means.
3. **Create a DOCS_CHECKLIST.md that lists every promised doc and its status.** This would become a single source of truth instead of hunting through 5+ files.
4. **Track ADRs as a CLI checklist, not a scattered file listing.** The session logs mention "ADR-001 drafted," but it's not on main yet. A clear ADR rollout dashboard would prevent this.
5. **Distinguish "drafted in decision inbox" from "merged to main."** The audit found docs in `.squad/decisions/inbox/` that weren't yet on main. A "Decision Status" column helps triage.

### References

- CONTRIBUTING.md (companion inclusion bar, provenance rule, vendoring policy)
- AGENTS.md (agent charters, mission, what's in scope)
- .github/copilot-instructions.md (source-of-truth repos, architecture rules)
- README.md (project wedge, Stack section TBD)
- SECURITY.md (read-only scope, threat model bootstrap)
- Open issues #7, #8, #11, #13-18, #21
- Open PRs (estimated from GitHub JSON output)
- Session logs in .squad/log/ (ADR-001 drafted, runtime scaffold)
- Decision inbox files (iris-skill-catalog-v0.md, burke-mcp-config-audit-v0.md, sage-coldstart-investigation.md)

---

## Learnings

### Documentation structure of the OSS repo

This repo maintains a **two-layer doc system**:

1. **Governance layer** (.squad/, .copilot/skills/): Trains agents on project conventions, workflow, team roles. Not user-facing. Includes team charters, ceremonies, orchestration logs, identity, templates, and 29 training skills.

2. **User-facing layer** (README.md, CONTRIBUTING.md, docs/, scripts/): Teaches external users and contributors how to use the server, install it, understand its scope, and report security issues. This layer is sparse (only root markdown files exist so far).

### What's missing vs. claimed

The biggest doc debt areas are:
- **Critical:** ADR index (docs/adr/) — affects README "Stack" section and decision governance
- **Critical:** Skill catalog (docs/skills/catalog.md) — affects user adoption
- **Critical:** Tool reference (docs/tools/) — affects developer workflow
- **High:** Per-client install guides (docs/install/) — affects initial setup experience
- **High:** Threat model expansion (SECURITY.md) — affects security review confidence
- **Medium:** Release notes (CHANGELOG.md) — affects v0.1 communication

### Biggest doc debt areas for v0.1

1. **docs/ directory doesn't exist yet.** This is the v0.1 user-facing doc root. All docs/ paths in CONTRIBUTING, AGENTS, and README are forward-looking.
2. **ADRs are drafted in session logs but not on main.** ADR-001 is the critical blocker; PR #22 is rebasing in a worktree.
3. **No single "docs map" or checklist.** The audit had to cross-reference 7 different files to infer what docs are promised. A docs/README.md index would help.
4. **Skill definitions are in flux.** The skill catalog depends on Iris finalizing the skill definitions. Four skills are mentioned (design-review, alz-gap-check, ingress-migration-plan, policy-as-code-suggest) but no reference docs for them exist yet.
5. **Companion server wiring is incomplete.** mcp-config.json has `"command": "TBD"` for mcp-server-azure-architect pending the runtime ADR.

## Wave 1 Cross-Agent Context

**From Lead:** ADR-001 (Python + FastMCP) ratified. PR #22 foundation landed. Your docs gap audit is critical for v0.1 release confidence. Top-3 blockers (skills catalog, ADR docs, install guides) should be triaged as wave 2 issues immediately.

**From Atlas:** PR #27 ALZ snapshot audit approved. When creating docs/skills/catalog.md and docs/tools/reference.md, reference this snapshot structure and provenance pattern. Include example queries from the snapshot (with checklist IDs).

**From Sentinel:** ADR-003 and threat model outlined. Threat model expansion (SECURITY.md update) is a top-3 v0.1 priority. Suggest: you lead the SECURITY.md "Threat Model" section write-up (translate Sentinel's STRIDE analysis to architect audience); Sentinel can review.

## References

- Docs Gap Audit: `.squad/decisions/inbox/sage-docs-gap-audit.md` (now in `.squad/decisions.md`)
- Session Log: `.squad/log/20260512T000000Z-wave1-foundation-unblock.md`
- Orchestration Log: `.squad/orchestration-log/20260512T000000Z-sage.md`
- Critical Issues: #11 (skill catalog), #15 (install guides), #22 (ADR docs), #21 (perf/cold-start)
