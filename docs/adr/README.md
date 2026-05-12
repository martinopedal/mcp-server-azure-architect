# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the mcp-server-azure-architect project. ADRs document significant architectural choices, the context in which they were made, the options considered, and the consequences of the decisions.

## Index

- [ADR-001: MCP Server Runtime Choice](0001-runtime-choice.md) - Decision on the runtime (Python, TypeScript, or .NET) for the MCP server implementation, including evaluation of SDK maturity, Azure SDK quality, cold start performance, distribution, JSON Schema tooling, ecosystem fit, and contributor friction.
- [ADR-002: ALZ Query Vendoring Policy](0002-alz-query-vendoring-policy.md) - Decision to vendor ALZ checklist queries as a snapshot under `data/alz-queries/`, pinned by upstream commit SHA in `manifest.json`. Covers refresh procedure, citation requirements, and validation gates.
- [ADR-003: Read-Only Enforcement Mechanism](0003-read-only-enforcement.md) - Decision on defense-in-depth enforcement strategy for read-only guarantee, including AST-based import allowlist (CI gate), naming conventions, CODEOWNERS routing, and aspirational runtime guard.
- [ADR-004: Companion Server Selection Bar](0004-companion-server-bar.md) - Criteria for including companion MCP servers in the curated kit. Companions must meet all 7 criteria: stable upstream, signed releases, narrow scope, complementary to azure-mcp, maintenance signal, read-only by design or config, and documented install path. Includes triage process for new companions and examples of rejected candidates.
- [ADR-005: SemVer and Release Cadence](0005-semver-and-release-cadence.md) - SemVer 2.0.0 interpretation for the MCP tool surface. Pre-1.0: minor bumps for tool changes, patch for fixes. Public surface: tool names/params/returns, mcp-config.json schema, ALZ manifest pinning policy. Skills not part of public surface. As-needed release cadence pre-1.0.
