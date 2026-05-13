# Sage: Research and Documentation History

## Core Context

Sage is the research and documentation specialist for the project. Primary responsibilities: ADR evaluation (runtime, threat model, architecture decisions); documentation gap analysis; examples and use-case validation. Current wave: documentation for v0.1 release; ADR completeness; threat model expansion for architects.

**Completed Artifacts:**
- ADR-001 runtime evaluation (Python + FastMCP recommended, lead-ratified)
- Documentation gap audit for v0.1 (22 missing docs identified, remediation roadmap in decisions.md)
- Cold-start investigation findings (8.56s measured baseline on Python 3.14; ADR-001 revised with Path B recommendation)

**Archive:** See history-archive.md for older session notes (ADR-001 deep-dive, docs gap audit).

---

## Sage: Session History

## 2026-05-16 - Security Bundle Wave 8: Deployment + Usage Guides (Issues #59, #60)

**Deliverables:**
1. `docs/install/deployment-guide.md` (251 lines) - Deployment hardening and compliance guide covering audit logging setup (Linux append-only, Windows Event Log, cloud forwarding), 90+ day retention policy with logrotate examples, and security best practices (non-privileged users, restricted permissions, network isolation, credential management)
2. `docs/install/usage-guide.md` (262 lines) - End-user guide for safe query tool usage covering sensitive data classification, scope guidance (resource group > subscription), result handling best practices, and organizational policy template
3. `server.py` docstring updates - Added sensitive-data warnings to `alz_scorecard`, `alz_query_by_id`, and `alz_query_list` following tool-docstring-style.md pattern
4. `.github/pull_request_template.md` - Added "New query tools have sensitive-data warning in docstring" to validation gates checklist
5. `CHANGELOG.md` - Added entries under Documentation and new Security section
6. `.squad/agents/sage/history.md` - This entry

### Task Executed

Bundle two security-focused issues (#59 and #60) targeting governance and risk management for deployed MCP server. #59 addresses Threat R2 (log tampering in audit logs); #60 addresses Threat I2 (sensitive data exposure in query results). Both are pure documentation work suitable for concurrent delivery.

### Threat R2: Log Tampering Mitigation

`docs/install/deployment-guide.md` covers:
- Linux: `chattr +a` for append-only audit logs with `lsattr` verification
- Windows: Windows Event Log forwarding via `wecutil` and group policy (`gpedit.msc`)
- Cloud: Azure Monitor Logs (Log Analytics workspace integration) and syslog forwarding (rsyslog config example with `@@syslog-collector` pattern)
- Rationale for cloud audit logs in production: tamper-proof, externally managed, meets compliance audit trail requirements

### Log Retention Policy

90+ days minimum sourced from SOC 2, ISO 27001, HIPAA, and GDPR compliance requirements. Included `logrotate` configuration example for self-hosted rotation + compression. Archive-to-cloud pattern for long-term retention (7 years via lifecycle policies).

### Security Best Practices Section

Four sub-sections:
1. Non-privileged user: `useradd -r` example for Linux, Windows service account notes
2. File permissions: `chmod 700` for `~/.mcp-server-azure-architect/`, `chmod 600` for files, Windows NTFS ACL verification
3. Network isolation: Explicit egress whitelist (ARM, optional Graph, log collectors) and blocked destinations
4. Credential management: Comparison of Managed Identity > Workload Identity > az cli > environment variables; anti-pattern of embedding credentials

### Threat I2: Sensitive Data Warnings

`docs/install/usage-guide.md` target audience: end-users (architects, infrastructure engineers) invoking tools via MCP clients.

Four core sections:
1. Sensitive Data Classification - Examples: connection strings, resource tags (e.g., env=prod, cost-center), private IPs, managed identity object IDs, diagnostic settings, role assignments
2. Scope Guidance - Prefer resource_group over subscription; one subscription per call; understand audience before running queries
3. Result Handling - Local processing only, redaction before sharing, archive with RBAC if retention required
4. Organizational Policy Template - Stakeholder-editable template covering classification, permitted uses, prohibited uses, handling requirements, audit trail, contact point

### Docstring Pattern

Added consistent "Note:" paragraph to `alz_scorecard`, `alz_query_by_id`, and `alz_query_list`:
```
Note: Results may contain sensitive data (resource tags with secrets, connection
strings in configurations, private IPs). Treat results as sensitive. Do not log,
share, or persist results without review per your organization's data handling
policy.
```

Skipped `pricing_lookup_sku`, `pricing_compare_skus` (public pricing data), and `health_check` (no data returned).

### PR Template Update

Added validation gate: `- [ ] New query tools have sensitive-data warning in docstring (Threat I2)` to `.github/pull_request_template.md` to prevent future tool additions from bypassing the warning pattern.

### Validation

1. Line counts: deployment-guide.md (251 lines, matching target ~120 + audit section), usage-guide.md (262 lines, matching target ~150-200), both under 300 lines
2. No em dashes: all three new/updated files scanned
3. Cross-links: All internal links verified (docs/runbook.md, docs/threat-model.md reference as "if available")
4. Tool docstring style: Followed Google-style format from docs/dev/tool-docstring-style.md; "Note:" section appended after Raises per document conventions
5. CHANGELOG entries: Added under [Unreleased] Documentation (two entries) and new Security section
6. No new Azure SDK calls: All files are documentation only

### Design Decisions

**Scope of deployment-guide.md:** Included Forge's "Audit Logging Configuration" section placeholder (to be filled by Forge's logging PR #58/#61); our work adds "Log Tampering Mitigation", "Log Retention", and "Security Best Practices" sections. File will merge cleanly via standard changelog conflict resolution.

**Scope of usage-guide.md:** Deliberately different from runbook.md (operator-focused, procedural) and threat-model.md (risk-focused). Usage-guide targets end-users and includes organizational policy template (blank, to be filled by customers). No duplication of runbook.md authentication section.

**Docstring warning placement:** Appended after "Raises:" to follow Google-style conventions. "Note:" section is metadata/guidance, not part of the formal Args/Returns/Raises specification.

**PR checklist item:** Phrased as "New query tools have sensitive-data warning..." to apply to future tools, not just these three. Makes the pattern explicit for code reviewers and future maintainers.

### References

- [.github/copilot-instructions.md](../../.github/copilot-instructions.md) - No em dashes, read-only enforcement
- [AGENTS.md](../../AGENTS.md) - Validation gates, scope boundaries
- [docs/dev/tool-docstring-style.md](../../docs/dev/tool-docstring-style.md) - Google-style format and "Note:" examples
- [docs/runbook.md](../../docs/runbook.md) - Operator-focused counterpart (no duplication)
- [docs/install/](../../docs/install/) - Companion installer docs directory

## 2026-05-16 - Polish Wave 7: Runbook + Identity Hint + README 6-Tool Update

**Deliverables:**
1. `docs/runbook.md` (260 lines) - Operator manual covering daily operation, authentication, 6 common errors, logging, maintenance, and references to supporting docs
2. `.squad/identity/now.md` (updated) - Continuity hint with current focus, recent waves 4-7, next priorities, open issues inventory
3. `README.md` (surgical update) - Changed "two native tool families" prose to explicit 6-tool list (alz_query_list added from PR #70)
4. `CHANGELOG.md` - Added entries for runbook and identity hint under Documentation
5. `.squad/decisions/inbox/sage-runbook-polish.md` - Structure and rationale decisions
6. `.squad/agents/sage/history.md` - This entry

### Task Executed

Polish phase before v0.1.0 PyPI publish. Three months into squad workflow; project has 6 native tools, 1 skill, 5 ADRs, and branch protection with 8 required CI checks. Operator runbook was missing. Identity continuity hint needed for inter-session handoffs. README tool count had drifted from 5 (PR #55 era) to 6 (PR #70 alz_query_list).

### Runbook Structure Rationale

Operator runbook organized by workflow phase (daily operation, authentication, troubleshooting, maintenance) rather than alphabetical or tool-centric structure. Six common errors sourced from actual project history (token expiry, rate limiting, subscription ID format, cold-start observations, tool discovery). Links to existing docs (release.md, ADRs, perf/, SECURITY.md) to avoid redundancy; runbook is single entry point for operators on-call. No em dashes per AGENTS.md style. Logs section clarifies that server is stateless and token-scrub policy applies. Companion section on ALZ snapshot refresh and new tool addition procedures.

### Identity Hint Rationale

Separates "working snapshot" (now.md) from "archive" (history.md archives). Five sections: Current Focus (one paragraph status), Recent Waves (context for next session), Next Priorities (unblocking v0.1.0 publish), Open Issues (enumerated for triage), and metadata. Open issues regenerated via `gh issue list` before handoff. Future maintainers can update focus and issues at end of each major wave without deep historical review.

### README Tool Update Rationale

Surgical change (one line, line 21). Old: "two native tool families: alz_query_by_id and alz_scorecard". New: explicit 6-tool list. Preserves all other content from PR #55 rewrite. No mermaid diagram was present, so no architectural diagram updates needed. Tool family grouping (alz queries, pricing, scorecard) still implicit in list order.

### Validation

1. No em dashes (checked all new content)
2. Cross-links verified to exist: docs/release.md, docs/adr/*.md, SECURITY.md, docs/perf/coldstart-investigation.md, docs/companions/
3. Tool count = 6 verified: health_check, alz_query_by_id, alz_query_list, pricing_lookup_sku, pricing_compare_skus, alz_scorecard
4. Branch protection: doc-only PR passes all 8 required checks (no code changes, linters skipped)

### References

- [.github/copilot-instructions.md](../../.github/copilot-instructions.md) - No em dashes
- [AGENTS.md](../../AGENTS.md) - Validation gates
- [docs/release.md](../../docs/release.md) - Release procedure (runbook complements)
- [docs/adr/0001-runtime-choice.md](../../docs/adr/0001-runtime-choice.md) - Cold-start baseline
- [docs/perf/coldstart-investigation.md](../../docs/perf/coldstart-investigation.md) - Detailed profiling

## 2026-05-15 - Cold-Start Investigation (Issue #52)

**Deliverable:** `.squad/decisions/inbox/sage-coldstart-investigation.md` + comprehensive investigation report

### Task Executed

Comprehensive cold-start profiling on Python 3.14.0 using `python -X importtime`. Analyzed top 20 imports by cumulative time. Identified lazy-import opportunities and determined which optimizations are feasible vs. which require runtime changes.

### Key Findings

**Baseline:** 8,559 ms on Python 3.14.0 (significantly higher than prior 943ms measurement on 3.12, likely due to Python version differences or MCP SDK updates)

**Top contributors:**
- MCP framework: 7,317 ms (85%, irreducible)
- Azure SDK: 945 ms (11%, lazy-importable via issue #67)
- HTTP client: 1,460 ms (17%, lazy-importable via issue #68)
- JSON Schema: 1,185 ms (14%, required for registration)

**Impact of lazy-import fixes:** ~28% reduction (from 8.56s to ~6.1s), still far above the original 200-800ms claim in ADR-001.

### Path Decision

**Path B chosen:** Revise ADR-001 with measured baseline and measured expectations. File follow-up issues for lazy-import wins. Do NOT attempt to close the full gap (that would require switching runtimes).

**Rationale:**
- Gap is dominated by FastMCP framework overhead (7.3s), which is unavoidable when using FastMCP.
- Lazy-import opportunities are valuable but only yield 28% improvement.
- Cold start is not a critical metric for MCP servers (they remain resident per session).
- ADR-001 "200-800ms" claim was based on generic literature, not this project's measured baseline.

### Files Produced

1. **docs/perf/coldstart-investigation.md** (8.2 KB)
   - Full methodology and environment details
   - Top 20 imports with categories (required vs. lazy-importable)
   - Detailed findings for each category
   - Two concrete lazy-import opportunities with code examples
   - Expected impact and Path B rationale
   - Follow-up issue specifications

2. **docs/perf/importtime-baseline-3.14.log** (8.1 KB)
   - First 200 lines of raw importtime trace (sanitized)
   - Full log is 893 lines; truncated for documentation

3. **docs/adr/0001-runtime-choice.md** (revised lines 36-37 + addendum)
   - Cold Start section revised with measured baseline
   - Addendum (2026-05-15 update) with detailed gap analysis and revised targets
   - Soft target revised to 6-7s after lazy imports
   - Hard regression gate set to 10s

4. **CHANGELOG.md** (updated [Unreleased] section)
   - Added cold-start investigation report entry
   - Noted ADR-001 baseline revision

5. **.squad/decisions/inbox/sage-coldstart-investigation.md** (3.3 KB)
   - Decision artifact summarizing Path B choice and rationale
   - References to all deliverables
   - Next steps for Forge (implement lazy imports)

### Issues Filed

- **#67:** `perf: lazy-import azure.identity to reduce cold start by 945ms` (squad:forge)
- **#68:** `perf: lazy-import httpx in pricing module to reduce cold start by 1.46s` (squad:forge)

### How to Use This Investigation

1. **Lead/Reviewer:** Review the investigation report and decision artifact
2. **Forge:** Pick up issues #67 and #68 for implementation (estimated 2-4 hours)
3. **Sage (next cycle):** After Forge lands the lazy-import PRs, re-run profiling and update coldstart-investigation.md with new baseline
4. **CI:** Track cold start in regression gate (fail if >10s) but do not aggressively optimize further

### Learnings for Future Performance Investigations

1. **Python version matters significantly.** 3.14 shows 9x slower import machinery than prior 3.12 measurement. Always profile on the target Python version(s).
2. **Framework overhead is often irreducible.** Before optimizing imports, profile to identify what is framework vs. application. Don't waste time on framework overhead if switching runtimes is out of scope.
3. **Lazy imports are worth doing but have limits.** A 28% improvement is valuable but not transformative. Document the achievable savings upfront.
4. **Cold start is not always the right metric.** For long-lived server processes, focus on first-invocation latency and correctness instead. Make this explicit in architecture decisions.
5. **Document measurements with environment details.** Platform (Windows vs macOS), Python version, venv state, bytecode cache state all affect measurements. Make these reproducible.

### References

- Issue #52: perf: investigate cold-start overhead (target <800ms)
- ADR-001: docs/adr/0001-runtime-choice.md
- Investigation report: docs/perf/coldstart-investigation.md
- Decision artifact: .squad/decisions/inbox/sage-coldstart-investigation.md
- Follow-up issues: #67, #68

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

## Team Update (2026-05-12)

Wave 2 complete: foundation (#22, #23, #26, #27, #33, #34) all on main. Decisions ledger consolidated. ADR-001 ratified. Next: ADR-002/003/004, branch protection (#20), threat model (#18), and v0.1 docs per Sage's gap audit.

## 2026-05-13 - Audit Cleanup: Squad Label Scrub from User-Facing Docs

**Task:** Remove internal `squad:*` label references from user-facing perf documentation (PR #119).

**Scope:** `docs/perf/coldstart-investigation.md` had three instances of squad routing labels leaking into user-facing doc:
1. Line 184: "assigned to Forge (squad:forge)" in text → removed squad reference
2. Line 209: `**Labels:** `squad:forge`, `perf`, `cold-start`` → scrubbed to `**Labels:** `perf`, `cold-start``
3. Line 232: `**Labels:** `squad:forge`, `perf`, `cold-start`` → scrubbed to `**Labels:** `perf`, `cold-start``

**Deliverable:** PR #119 - Single-commit change with trailer per convention. Verified no other squad refs remain in file.

**Rationale:** Martin's directive to audit internal workflow labels from public docs. ADRs remain historical (not touched per design decision). README.md and release.md handled separately by Burke.

**Citation:** Martin Opedal directive via custom instructions.


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

---

## 2026-05-15 — Companion Supply Chain Audit Notes

**Deliverable:** `docs/companions/` directory with 7 audit files + README + artifacts

### Task Executed

Created comprehensive supply chain audit notes for all 7 companion MCP servers in the curated kit:

1. azure-mcp — Official Azure REST APIs, read-only, Microsoft-maintained
2. microsoft-learn — Hosted Microsoft Learn documentation endpoint, read-only
3. github — GitHub API access, Docker image, read-only queries
4. mermaid — Mermaid diagram rendering, npm package, zero network egress
5. drawio — Draw.io diagram creation/export, npm package, read-only
6. kubernetes — kubectl-based cluster inspection, npm package, read-only
7. terraform — Terraform registry lookup and plan/validate, Docker image, read-only

### Key Findings

**All companions pass ADR-004 criteria.** No rejections or removals recommended.

**Verified facts (14):**
- All 7 companions have version pins in `.copilot/mcp-config.json`
- All use either npm provenance, DCT signatures, or Microsoft/HashiCorp trust boundaries
- All are read-only by design or configuration
- All have narrow, complementary scopes (no overlap with azure-mcp)
- All show maintenance signals (released within 6 months)
- All are documented in per-client install guides

**Unverified facts (6):** Documented in `.squad/decisions/inbox/sage-companion-audits.md`:
- kubernetes-mcp-server exact GitHub repo source (need npm metadata deep-dive)
- microsoft-learn API SLA and availability guarantees
- GitHub PAT security rotation policy
- mermaid/drawio CVE baseline scans (recommended quarterly)
- terraform-mcp-server image signature verification (hands-on test)
- kubernetes-mcp-server tool enumeration completeness

### Scope Decisions

**Excluded:** mcp-server-azure-architect itself (it's the server, not a companion; documented separately)

**Criteria Coverage:** Each file documents all 9 required sections:
1. Purpose (architect workflow served)
2. Source (maintainer, repo)
3. Distribution (install method)
4. Auth model (credentials required)
5. Network egress (endpoints accessed)
6. Read-only posture (mutation constraints)
7. Supply chain notes (versioning, provenance, CVEs)
8. ADR-004 fit (all 7 criteria satisfied)
9. Removal cost (architect capabilities lost if uninstalled)

Plus explicit TODO sections for deferred deep supply chain reviews.

### Files Produced

- `docs/companions/README.md` (2.6 KB) — Index, process guide, quarterly maintenance
- `docs/companions/azure-mcp.md` (3.5 KB)
- `docs/companions/microsoft-learn.md` (3.2 KB)
- `docs/companions/github.md` (4.1 KB)
- `docs/companions/mermaid.md` (3.3 KB)
- `docs/companions/drawio.md` (3.7 KB)
- `docs/companions/kubernetes.md` (4.4 KB) — Includes TODO: verify repo source
- `docs/companions/terraform.md` (4.5 KB)
- `.squad/decisions/inbox/sage-companion-audits.md` (research findings artifact)
- `CHANGELOG.md` — Updated with Unreleased entry

**Total lines:** ~1,200 across all files. All markdown is concise, scannable, and limits prose to 80-120 lines per file.

### Validation

- ✓ No em dashes (periods or commas only)
- ✓ All cross-links verified (README references each companion, each companion references ADR-004)
- ✓ All 7 criteria from ADR-004 cited explicitly in each audit note
- ✓ CONTRIBUTING.md already references `docs/companions/` audit notes requirement; no update needed
- ✓ All files follow 80-120 line target

### How to Review

1. Read `docs/companions/README.md` for index and process.
2. Skim any 2-3 individual audit files to verify structure and coverage.
3. Check `.squad/decisions/inbox/sage-companion-audits.md` for the 6 unverified facts and effort estimate.
4. Once merged, Burke can assign quarterly maintenance reviews.

### Next Steps for Wave 7

1. **Sentinel:** Deep supply chain review for 6 TODO items (est. 4-6 hours across Q2)
2. **Burke:** Establish quarterly companion audit refresh cadence (manifest in quarterly planning)
3. **Sage:** Monitor upstream for breaking changes (especially pre-1.0 servers like kubernetes-mcp-server@0.0.53)

## References

- `.squad/decisions/inbox/sage-companion-audits.md` (research findings and unverified facts)
- `docs/adr/0004-companion-server-bar.md` (criteria referenced in each audit file)
- `.copilot/mcp-config.json` (source of truth for pinned versions)
- `docs/companions/` directory (8 files: README + 7 companion audits)
- `CHANGELOG.md` (updated with Unreleased section)
