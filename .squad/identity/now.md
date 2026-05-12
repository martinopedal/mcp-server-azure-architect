# Squad Identity / now.md

Current focus, team state, and next likely work for `mcp-server-azure-architect`.

## Current Focus

MCP server + Copilot CLI skills bundle for Azure architects, v0.1.0 RC. Ships 6 native tools (health_check, alz_query_by_id, alz_query_list, pricing_lookup_sku, pricing_compare_skus, alz_scorecard), 1 skill (alz-gap-check), 5 ADRs, and curated mcp-config.json wiring 7 companion servers. Branch protection live with 8 required CI checks. Now in polish phase (operator runbook, identity continuity, README 6-tool refresh) before first PyPI publish.

## Recent Waves

- **Wave 4 (native tools):** Registered 5 tools (health_check, alz_query_by_id, pricing_lookup_sku, pricing_compare_skus, alz_scorecard). Added pricing retail API wrapping and ALZ scorecard composition engine.
- **Wave 5 (release pipeline + read-only gate):** Shipped release.md runbook, ADR-005 SemVer policy, AST-based read-only import allowlist, gitleaks and CodeQL CI gates, branch protection with 8 required checks.
- **Wave 6 (alz_query_list + companion audits + cold-start investigation):** Landed alz_query_list tool for catalog discovery (PR #70). Completed companion server audit (docs/companions/ with per-server guides for azure-mcp, microsoft-learn, mermaid, drawio, kubernetes, terraform). Finished cold-start investigation (8.5-9.0s baseline on Windows normal per ADR-001 budget).
- **Wave 7 (polish, current):** Operator runbook (docs/runbook.md), identity continuity hint (.squad/identity/now.md), README 5->6 tool update with alz_query_list, CHANGELOG entry.

## Next Likely Focus

1. **First PyPI publish (v0.1.0).** Cut tag, release workflow runs, package lands on PyPI. Blocks external adoption.
2. **Perf work (Forge):** Issues #67, #68. Lazy-import azure.identity and httpx to reduce cold start by 2.4s total. Re-measure.
3. **v0.2 planning.** Vendored catalogue expansion (graph bulk vendor for 132 items per Atlas roadmap). Threat model resolution for issues #57-63. Skill expansion (alz-gap-check, alz-quota-planner-compose as skill not tool).

## Open Issues

| # | Title |
|---|---|
| #68 | perf: lazy-import httpx in pricing module to reduce cold start by 1.46s |
| #67 | perf: lazy-import azure.identity to reduce cold start by 945ms |
| #63 | security: T1 - Integrity Checks for Vendored Queries (threat model T-T1) |
| #62 | security: D1 - Large Query Result Overwhelms MCP Channel (threat model T-D1) |
| #61 | security: I3 - World-Readable Log Files (threat model T-I3) |
| #60 | security: I2 - Sensitive Data in Query Results (threat model T-I2) |
| #59 | security: R2 - Log Tampering (threat model T-R2) |
| #58 | security: R1 - Tool Execution Not Logged (threat model T-R1) |
| #57 | security: S1 - Confused-Deputy via Unvalidated subscription_id (threat model T-S1) |
| #44 | feat(server): pricing_estimate_workload tool |

## Working Directory

`C:\git\mcp-server-azure-architect`

## Squad Coordinator Version

v0.9.1
