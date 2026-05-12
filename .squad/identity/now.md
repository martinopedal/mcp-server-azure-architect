# Squad Identity / now.md

Current focus, team state, and next likely work for `mcp-server-azure-architect`.

## Current Focus

MCP server + Copilot CLI skills bundle for Azure architects, v0.1.1 in flight. Ships 7 native tools (health_check, alz_query_by_id, alz_query_list, pricing_lookup_sku, pricing_compare_skus, pricing_estimate_workload, alz_scorecard), 1 skill (alz-gap-check), 5 ADRs, curated mcp-config.json wiring read-only companion servers. Wave 9 closed v0.1.1 patch tier (#85, #86, #88, #89, #90, #91, #92, #97, #98, #101) and added MCP tool annotations + sovereign cloud endpoint support. Next: PyPI publish gates v0.1.1 release and #93 (MCP Registry listing).

## Recent Waves

- **Wave 5 (release pipeline + read-only gate):** Shipped release.md runbook, ADR-005 SemVer policy, AST-based read-only import allowlist, gitleaks and CodeQL CI gates, branch protection with 8 required checks.
- **Wave 6 (alz_query_list + companion audits + cold-start investigation):** Landed alz_query_list tool for catalog discovery (PR #70). Completed companion server audit (docs/companions/ with per-server guides for azure-mcp, microsoft-learn, mermaid, drawio, kubernetes, terraform). Finished cold-start investigation (8.5-9.0s baseline on Windows normal per ADR-001 budget).
- **Wave 7 (polish):** Operator runbook (docs/runbook.md), identity continuity hint (.squad/identity/now.md), README 5->6 tool update with alz_query_list, CHANGELOG entry.
- **Wave 8 (security hardening + 7th tool):** Threat-model T-R1 audit logging (#58), pricing_estimate_workload tool (#44, PR #87), OData escape consistency (PR #84), CI action SHA-pinning (#86 release.yml, PR #84 ci.yml).
- **Wave 9 (strategic research + v0.1.1 execution):** Sage MCP-ecosystem scan + Atlas KQL coverage audit produced Lead synthesis with ADR-004 reaffirm-with-addendum and 20-item v0.1.x/v0.2 roadmap. Filed issues #89-#102. Closed v0.1.1 tier in 2 batches (10 PRs: #103-#113, modulo #105 reassigned). Added MCP tool annotations to all 7 tools (PR #112), sovereign cloud endpoint via AZURE_CLOUD_NAME (PR #113), AKS-MCP mutation hazard docs (PR #110), microsoft/mcp companion repoint (PR #108), refresh-script JSON-key bug fix (PR #103).

## Next Likely Focus

1. **First PyPI publish (v0.1.1).** Manual trusted-publisher setup pending. Unblocks #93 (MCP Registry listing) and external adoption.
2. **v0.1.2 small wins.** #94 pillar->source field rename (breaking, schedule with migration note). #95 vendoring license + monthly cadence docs.
3. **v0.2 catalogue expansion.** Heavy data curation tier: #96 expand vendored snapshot to all 132 queryable items. #99 RBAC drift queries. #100 diagnostics_coverage and tag_audit queries. #102 CI breaking-change detector on refresh PRs.

## Open Issues

| # | Title |
|---|---|
| #102 | chore(ci): breaking-change detector on refresh PRs |
| #100 | feat(alz): diagnostics_coverage and tag_audit vendored queries |
| #99 | feat(alz): identity / RBAC drift queries |
| #96 | feat(alz): expand vendored graph snapshot to all 132 queryable items |
| #95 | chore(vendoring): monthly cadence, license field, third-party notices |
| #94 | feat(server): rename pillar -> source in alz_query_list / alz_scorecard |
| #93 | chore(release): list v0.1.1 in MCP Registry (blocked on PyPI) |
| #68 | perf: lazy-import httpx in pricing module to reduce cold start by 1.46s |
| #67 | perf: lazy-import azure.identity to reduce cold start by 945ms |
| #63 | security: T1 - Integrity Checks for Vendored Queries |
| #62 | security: D1 - Large Query Result Overwhelms MCP Channel |
| #61 | security: I3 - World-Readable Log Files |
| #60 | security: I2 - Sensitive Data in Query Results |
| #59 | security: R2 - Log Tampering |
| #57 | security: S1 - Confused-Deputy via Unvalidated subscription_id |

## Working Directory

`C:\git\mcp-server-azure-architect`

## Squad Coordinator Version

v0.9.1
