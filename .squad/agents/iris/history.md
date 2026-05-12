# Iris: Copilot Skills Author — History

## 2026-04-22T13:15:00Z — First Skill Landed: alz-gap-check

Branch: `feat/iris-skill-alz-gap-check-v2`  
PR: (pending creation)

Authored the first Copilot CLI extension for the project: `alz-gap-check`. This skill orchestrates ALZ checklist gap analysis by composing this server's `alz_query_by_id` tool (owned by Atlas) with optional `microsoft-learn-mcp` remediation lookups. Deliverables include:

- `.github/extensions/alz-gap-check/extension.mjs` — the extension itself
- `tests/skills/test_alz_gap_check_replay.md` — replay scenario doc
- `docs/skills/catalog.md` — skill catalog, first entry
- `.squad/agents/iris/history.md` — this file

**v0 behavior:** Returns an honest prerequisite message if `alz_query_by_id` tool is not available. The extension is wired and ready, automatically activating once Atlas's tool lands. No fake data, no `Math.random()`, no guessed remediation URLs.

**Corrections applied:**
1. Removed `Math.random()` fake failure data. v0 returns a clear prerequisite message instead.
2. Removed guessed Microsoft Learn URLs. v1 will add remediation via `microsoft-learn-mcp` search.
3. Added terminology section to catalog.md explaining "skill" vs "extension".
4. Verified decision record exists locally at `.squad/decisions/inbox/iris-skill-catalog-v0.md` (gitignored inbox, Scribe merges post-PR).
## 2026-04-22T11:33:32Z — Runtime Decision: Python

ADR-001 accepted. Runtime is Python. Informs skill orchestration and MCP composition patterns.

## 2026-04-22T11:45:02Z — Runtime Scaffold Complete

Forge completed Python + FastMCP scaffold. All CI gates pass (ruff, mypy, pytest). Lead approved; cold-start follow-up investigation open (assigned Sage). You can now begin authoring Copilot skills that orchestrate the toolkit.

## 2026-05-15T16:00:00Z — Skills Wave 2: design-review + alz-gap-check (#11, #12)

Branch: `docs/iris-skills-11-12`  
PR: (pending creation)

Authored two new Copilot CLI skills that distill Azure architect reasoning:

### Skill 1: design-review (#11)

Guides architects through structured pre-deployment design review (intake → reference architecture pull → option grid with cost overlay → ALZ checklist alignment → pillar scoring → recommendation memo).

**Composes:**
- `microsoft-learn` (hosted docs): Architecture guidance + compliance baselines
- `pricing_compare_skus` + `pricing_lookup_sku` (this server): Cost trade-off matrix
- `alz_query_by_id` (this server): Checklist alignment verification
- `mermaid` (optional, companion): As-is/to-be topology diagrams
- `azure-mcp` (optional, companion): Live resource inspection

**Deliverables:**
- `.squad/skills/design-review/SKILL.md` — full skill documentation + worked example (Multi-Region SaaS scenario)

**Pattern:** 6-phase review process (intake, reference arch pull, option grid, ALZ alignment, scoring, memo). Scored on Resilience / Security / Cost / Operability pillars.

### Skill 2: alz-gap-check (#12)

Walks operators through operational ALZ conformance audit (scope intake → pillar selection → query iteration → severity classification → remediation memo).

**Composes:**
- `alz_query_by_id` (this server): Pillar-by-pillar conformance checks
- `alz_scorecard` (forthcoming, transparent upgrade path): High-level conformance sweeps (not blocking)
- `azure-mcp` (optional, companion): Deeper resource diagnostics
- `microsoft-learn` (optional, companion): Remediation guidance

**Deliverables:**
- `.squad/skills/alz-gap-check/SKILL.md` — full skill documentation + worked example (Financial SaaS post-migration scenario)

**Pattern:** 4-phase audit process (intake, query iteration, failure categorization, remediation memo). Severity-classified gaps (Critical / High / Medium / Low) with remediation timelines.

### Composition Judgment Calls

**design-review vs alz-gap-check split:** design-review is pre-deployment (design gate, architecture trade-offs primary); alz-gap-check is operational (audit gate, conformance primary). Both use `alz_query_by_id`, but for different audiences (architects vs operators).

**Severity classification scheme:** Risk-based (Critical = production blocker, High = 1-2 sprint remediation, Medium = next cycle, Low = informational). Mirrors Azure operational severity without terminology overload.

**Optional companion servers:** Both skills work offline (using `alz_query_by_id` alone), but enrich with live data if `azure-mcp`, `microsoft-learn`, etc. available. Graceful degradation.

**alz_scorecard integration:** Transparent upgrade path. When Forge ships `alz_scorecard`, alz-gap-check auto-detects availability. No code change needed; Iris refines in feedback loop post-PR.

**Confidence: Low** (first capture). Distills known ALZ design/audit patterns. Refinement pending: (1) real architect/operator feedback, (2) ALZ snapshot stability over time, (3) severity classification refinement with incident data.

### Cross-Repo Contracts

- **`alz_query_by_id` (this server):** Consumes vendored ALZ snapshot (pinned in `data/alz-queries/manifest.json`). Atlas owns snapshot refresh; Iris re-validates queries. Contract is mechanical; no skill code changes on upstream updates.
- **`pricing_compare_skus` / `pricing_lookup_sku` (this server):** Queries live Azure retail pricing API. No vendored snapshot; always current.
- **`microsoft-learn` (hosted, companion):** Always current (hosted docs). No refresh cycle.
- **`alz_scorecard` (forthcoming):** Transparent integration. Skill checks availability; adapts automatically when tool lands.

### Decision Artifact

- `.squad/decisions/inbox/iris-skills-11-12.md` — composition diagram, judgment calls, risks/mitigations, next steps

## Team Update (2026-05-12)

Wave 2 complete: foundation (#22, #23, #26, #27, #33, #34) all on main. Decisions ledger consolidated. ADR-001 ratified. Next: ADR-002/003/004, branch protection (#20), threat model (#18), and v0.1 docs per Sage's gap audit.
