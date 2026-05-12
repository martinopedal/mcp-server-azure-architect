# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-05-15

### Added

#### MCP Tools (5)
- `health_check` - Server health and version check
- `alz_query_by_id` - Look up vendored ALZ checklist queries by ID
- `pricing_lookup_sku` - Azure retail pricing lookup for single SKU
- `pricing_compare_skus` - Compare retail pricing for multiple SKUs
- `alz_scorecard` - Run ALZ scorecard for a subscription

#### Skills (1)
- `alz-gap-check` - ALZ gap check orchestration skill (v0, prerequisite mode)

#### Architecture Decision Records (4)
- ADR-001: MCP Server Runtime Choice (Python + FastMCP)
- ADR-002: ALZ Query Vendoring Policy
- ADR-003: Read-Only Enforcement Mechanism
- ADR-004: Companion Server Selection Bar

#### Vendored ALZ Queries
- Vendored snapshot from `martinopedal/alz-checklist-queries` (commit `e7641be`) and `martinopedal/alz-graph-queries` (tag `v1.1.0`, commit `8a3fdda`)
- 4 queries total across checklist and graph pillars
- Manifest tracking at `data/alz-queries/manifest.json`

#### Companion Kit
- Curated `mcp-config.json` with 7 companion servers: azure-mcp, microsoft-learn, github, mermaid, drawio, kubernetes, terraform
- Per-client install docs for 5 clients: Copilot CLI, Claude Desktop, Cursor, VS Code Copilot, and compatibility matrix

#### Repository Infrastructure
- Branch protection with 6 required checks: test (ubuntu-latest, 3.11), test (ubuntu-latest, 3.12), scan, review, analyze (actions), CodeQL
- CI workflow with ruff, mypy, pytest validation
- Security threat model and read-only enforcement gates
- Hatchling build backend with uv distribution

### Changed
- N/A (initial release)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- Read-only enforcement via AST-based import allowlist
- DefaultAzureCredential-only auth (no PATs, no secrets in code)
- Token-scrubbing policy for all logging and persistence

[Unreleased]: https://github.com/martinopedal/mcp-server-azure-architect/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/martinopedal/mcp-server-azure-architect/releases/tag/v0.1.0
