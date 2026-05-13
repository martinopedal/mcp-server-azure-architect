# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security

- **SHA-256 integrity verification for vendored ALZ queries** (Closes #63). Mitigates threat T1 (compromised vendored query / KQL injection). Each query file now has a SHA-256 hash recorded in `manifest.json`. CI validates hashes on every build before tests run. Any tampered query file triggers build failure. Hash regeneration is explicit via `python scripts/verify_query_integrity.py --update`. The weekly refresh workflow automatically regenerates hashes after pulling new queries from upstream. See `data/alz-queries/CONTRIBUTING.md` for workflow documentation.
- **Subscription scope validation** (`validate_caller_scope` in `azure_client.py`) defends against confused-deputy attacks (Threat S1, issue #57). All tools accepting `subscription_id` now validate that the requested subscription is in the caller's authorized scope by querying Azure Resource Manager. Out-of-scope subscription IDs are rejected with `PermissionError`. Validation results are cached per credential to avoid repeated ARM calls. Closes #57.
- **Pagination and timeouts on query tools** (#62, D1). `alz_scorecard` accepts `page_size` (default 1000, max 5000) and `page_token`; results expose `next_page_token`. All Azure Resource Graph queries time out after 60 seconds with actionable error. Pricing httpx timeout aligned to 60s. Defends against denial-of-service via large query results.
- **Audit logging for all MCP tool invocations** with rotating file handler (10MB max, 5 backups). Logs timestamp, tool name, redacted parameters, and result summaries. Sensitive values (subscription IDs, tenant IDs, API keys, tokens) are automatically redacted. Default location: `~/.mcp-server-azure-architect/logs/audit.log`. Overrideable via `MCP_AZURE_ARCHITECT_LOG_DIR` environment variable. (Closes #58)
- **Secure log file permissions** (0600 owner read/write only) and log directory permissions (0700 owner only) to prevent information disclosure. Cross-platform implementation with POSIX `chmod` and Windows `icacls` ACL enforcement. (Closes #61)

### Added

- Native MCP tool `pricing_estimate_workload` for structured workload cost estimation. Composes `pricing_lookup_sku` results into a multi-line estimate with VM count, region, hours per month, and storage. Returns total monthly cost (Decimal), currency, line items, assumptions, and warnings. Designed for sizing trade-off analysis and to feed `alz_scorecard` cost guardrail. Retail prices only (no EA/CSP). (#44)
- **Tool docstring style guide** (`docs/dev/tool-docstring-style.md`). Pattern extracted from 5 working MCP tools. Covers required structure (summary, description, Args, Returns, Raises, Examples), parameter conventions (optionality, defaults, Literal types), common pitfalls, and test patterns. Google-style docstrings normalized across the project.
- Native MCP tool `alz_query_list` for enumerating vendored ALZ checklist queries with optional filters (pillar, source_repo). Returns metadata (checklist_id, pillar, source_repo, citation) for up to 200 queries per call. Pairs with `alz_query_by_id` for discovery-then-fetch workflow. (#51)
- Cold-start canary test for azure.identity lazy import (regression guard for #67).
- Cold-start canary test documenting httpx as FastMCP-owned dependency (addresses #68).

### Changed

- **BREAKING (pre-1.0): `pillar` field renamed to `source` across MCP tool surface.** Affects `alz_query_list` (param + response items + filters_applied), `alz_scorecard` (param + per-result + aggregate `by_source` replacing `by_pillar`), and `alz_query_by_id` (response `source` field). The semantic was always "source dataset" (vendored from `data/alz-queries/checklist/` or `data/alz-queries/graph/`), not a WAF pillar. Consumers calling `alz_query_list(pillar="checklist")` must update to `source="checklist"`. No alias. Pre-1.0 we cut clean. (Closes #94)
- **Documentation style**: second-pass cleanup of banned punctuation, wrong glyph status indicators (replaced with the project-approved set, plus a text fallback for "pending"), AI-slop language in ADRs, and voice profile consistency. Scope: README, CHANGELOG, docs/ and ADRs. Exempt: .squad/, .copilot/skills/, vendored data, code. See `.copilot/skills/docs-style/SKILL.md` for the full ruleset.
- **Performance**: Lazy-imported `azure.identity` in `azure_client.get_credential()` to reduce cold-start overhead by 157ms (7.7% faster). See `docs/perf/lazy-import-results.md` for measurements. (Closes #67)
- ADR-001 revised baseline expectations: measured cold start is 8.5-9.0 seconds on Python 3.12-3.14 (dominated by irreducible FastMCP framework overhead). See `docs/perf/coldstart-investigation.md` for detailed analysis.

### Fixed

- **Readonly-check workflow now runs on all PRs.** Removed `paths:` filter from `.github/workflows/readonly-check.yml` to fix doc-only PR blocking issue. The workflow always runs on every PR + push; it is a fast check (~30s) and correctly reports "no violations" for doc-only changes. This unblocks doc-only PRs while preserving the read-only enforcement gate as a required status check.

### Documentation

- `docs/install/deployment-guide.md` - Audit logging configuration guide with log rotation settings, sensitive data redaction policies, immutable log storage upgrade paths (syslog, Azure Monitor), and cross-platform permission enforcement details

- `docs/companions/` - Supply chain audit notes for all 7 companion MCP servers in the curated kit
- `docs/perf/coldstart-investigation.md` - Cold-start profiling report with import graph analysis and lazy-import recommendations
- `docs/perf/lazy-import-results.md` - Before/after measurements and analysis for lazy-import refactors
- `docs/runbook.md` - Operator runbook for daily operation, authentication, common errors, logging, and maintenance workflows
- `.squad/identity/now.md` - Cross-session continuity hint with current project focus, recent waves, next priorities, and open issues inventory
- `docs/perf/importtime-baseline-3.14.log` - Raw Python importtime trace (first 200 lines)
- `docs/install/deployment-guide.md` - Deployment configuration and hardening guidance covering audit logging setup (append-only on Linux, Windows Event Log forwarding, cloud log ingestion to Azure Monitor Logs or syslog), log retention policy (90+ days minimum for compliance), and security best practices (non-privileged user, restricted permissions, network isolation, credential management). Addresses Threat R2 (log tampering). (#59)
- `docs/install/usage-guide.md` - End-user guide for safe invocation of query tools covering sensitive data handling (connection strings, resource tags, private IPs, role assignments), scope guidance (prefer resource group over subscription, one subscription per call), result handling best practices (local processing, redaction before sharing, archive with access controls), and organizational policy template. Addresses Threat I2 (sensitive data exposure). (#60)
- README.md: Removed inaccurate cold-start claim. Replaced with link to `docs/perf/coldstart-investigation.md` for measured baseline (8.5-9.0s on Python 3.12-3.14, dominated by FastMCP framework overhead). Fixes discrepancy between README claim and ADR-001 planning estimate.
- `.copilot/skills/docs-style/SKILL.md`: Fixed tool count drift. Updated from "six native tools" to "seven native tools" and added `pricing_estimate_workload` to the list (added in PR #87).

### Security

- Sensitive-data warnings added to `alz_scorecard`, `alz_query_by_id`, and `alz_query_list` tool docstrings warning users that results may contain sensitive data and should not be logged, shared, or persisted without review per organizational data handling policy. (#60)

### Automation

- **ALZ snapshot refresh automation:** Weekly scheduled GitHub Actions workflow to detect upstream drift in `martinopedal/alz-checklist-queries` and `martinopedal/alz-graph-queries`, automatically opening PRs with updated manifests when changes detected. See `.github/workflows/refresh-alz-snapshot.yml` and `scripts/refresh_alz_snapshot.py`.

### Security

- **Gitleaks allowlist tightened.** Added `tests/.*` and `data/alz-queries/manifest.json` to the global path allowlist. Test fixtures legitimately contain mock JWT and API key strings to exercise the `token_scrub()` redaction logic, and the ALZ query manifest contains 64-character hex SHA-256 hashes that the default `azure-tenant-or-subscription-id-in-non-doc` rule misclassified as Azure GUIDs. Both paths are non-shipping artifacts and are correctly excluded from secret scanning.

### Repository Infrastructure

- GitHub issue and PR templates with squad routing:
  - `.github/ISSUE_TEMPLATE/bug-report.md` - Bug report template with environment, pre-checks, credential scrubbing reminder
  - `.github/ISSUE_TEMPLATE/feature-request.md` - Feature request template with proposed surface, ADR-004 justification, acceptance criteria
  - `.github/ISSUE_TEMPLATE/security-finding.md` - Security finding template with threat, impact, evidence, mitigation, and disclosure policy reminder
  - `.github/ISSUE_TEMPLATE/config.yml` - GitHub issue template configuration: disables blank issues, adds security and squad routing contact links
  - `.github/pull_request_template.md` - PR template with validation gates (pytest, ruff, mypy, check_readonly.py, mcp_smoke.py, CHANGELOG.md)

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
