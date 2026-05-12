# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Tool docstring style guide** (`docs/dev/tool-docstring-style.md`). Comprehensive pattern extracted from 5 working MCP tools. Covers required structure (summary, description, Args, Returns, Raises, Examples), parameter conventions (optionality, defaults, Literal types), common pitfalls, and test patterns. Google-style docstrings normalized across the project.
- Native MCP tool `alz_query_list` for enumerating vendored ALZ checklist queries with optional filters (pillar, source_repo). Returns metadata (checklist_id, pillar, source_repo, citation) for up to 200 queries per call. Pairs with `alz_query_by_id` for discovery-then-fetch workflow. (#51)

### Changed

- ADR-001 revised baseline expectations: measured cold start is 8.5-9.0 seconds on Python 3.12-3.14 (dominated by irreducible FastMCP framework overhead). See `docs/perf/coldstart-investigation.md` for detailed analysis.

### Fixed

- **Readonly-check workflow now runs on all PRs.** Removed `paths:` filter from `.github/workflows/readonly-check.yml` to fix doc-only PR blocking issue. The workflow always runs on every PR + push; it is a fast check (~30s) and correctly reports "no violations" for doc-only changes. This unblocks doc-only PRs while preserving the read-only enforcement gate as a required status check.

### Documentation

- `docs/companions/` - Supply chain audit notes for all 7 companion MCP servers in the curated kit
- `docs/perf/coldstart-investigation.md` - Comprehensive cold-start profiling report with import graph analysis and lazy-import recommendations
- `docs/runbook.md` - Operator runbook for daily operation, authentication, common errors, logging, and maintenance workflows
- `.squad/identity/now.md` - Cross-session continuity hint with current project focus, recent waves, next priorities, and open issues inventory
- `docs/perf/importtime-baseline-3.14.log` - Raw Python importtime trace (first 200 lines)

### Automation

- **ALZ snapshot refresh automation:** Weekly scheduled GitHub Actions workflow to detect upstream drift in `martinopedal/alz-checklist-queries` and `martinopedal/alz-graph-queries`, automatically opening PRs with updated manifests when changes detected. See `.github/workflows/refresh-alz-snapshot.yml` and `scripts/refresh_alz_snapshot.py`.

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
