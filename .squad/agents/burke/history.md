# Burke: Session History

## Session 1: mcp-config.json v0 audit and per-client install docs (2026-04-22)

Audited the curated `mcp-config.json` and pinned all companion versions where upstream supports it. Discovered incorrect package name for mermaid (`@mermaid-js/mermaid-mcp` does not exist; corrected to `mcp-mermaid@0.4.1`). Created four per-client install guides (Copilot CLI, Claude Desktop, Cursor, VS Code Copilot) with manual merge instructions for v0. Added compatibility matrix with version rationale and testing roadmap. No security findings. Decision document in `.squad/decisions/inbox/burke-mcp-config-audit-v0.md`.

## Session 2: PR #23 rebase against runtime scaffold (2026-05-12)

Rebased PR #23 against new main after PR #22 (Python/FastMCP scaffold) and PR #33 (docs ledger) merged. Rebase completed cleanly with zero conflicts. Git automatically reconciled identical scaffold files (pyproject.toml, src/*, tests/*) and non-overlapping docs. All validation gates passed locally (ruff, mypy, pytest) and in CI (7/8 checks green, 1 non-blocking label sync failure). Force-pushed rebased branch, requested @copilot review, added squad label. PR #23 now ready for code-owner merge. Decision artifact in `.squad/decisions/inbox/burke-pr23-rebase.md`.

## Learnings

### Rebase Strategy for Long-Lived Feature Branches
When a feature branch lags behind a major scaffold landing (runtime, CI, docs structure), prefer rebase over merge to maintain linear history. If the feature branch was created from an earlier scaffold attempt and main later lands the final scaffold, Git will often auto-resolve conflicts by recognizing identical content. Key pattern: if both branches converged on the same file content through independent work, rebase will succeed cleanly.

### MCP Client Config Parity
Across the four major MCP clients (Copilot CLI, Claude Desktop, Cursor, VS Code Copilot), config schema is similar but paths differ significantly. Per-client install docs are essential because users cannot share a single config file location. Future enhancement: install script that detects client and merges into the correct platform-specific path.

### Companion Server Pinning Rationale
Pin versions when: (1) upstream has stable releases with semver, (2) schema stability matters more than bleeding-edge features, (3) users need reproducible installs. Avoid pinning when: upstream moves fast and schema is experimental, or when latest is the only tested version. Document pinning rationale in compatibility matrix so future maintainers know why each version was chosen.

## Team Update (2026-05-12)

Wave 2 complete: foundation (#22, #23, #26, #27, #33, #34) all on main. Decisions ledger consolidated. ADR-001 ratified. Next: ADR-002/003/004, branch protection (#20), threat model (#18), and v0.1 docs per Sage's gap audit.

## Wave 3 Outcomes (2026-05-12)

**ADR-004 companion server selection bar merged (PR #37, closed #8).** Seven-criteria framework ratified: stable upstream, signed releases, narrow scope, complementary to azure-mcp, maintenance signal, read-only design, documented install path. All 8 current companions in `.copilot/mcp-config.json` audit-confirmed passing. Triage process documented for future candidates. Sentinel's ADR-003 threat model (criterion 6: read-only) and Forge's dependency tightening (supply chain discipline) inform ADR-004's evaluation framework.

**Pricing tools decision routed to issue #39.** ADR-004 body cites native pricing tools as worked example of future "value-add layer above companion kit." Issue #39 queued for wave 4. Burke will triage pricing candidates against ADR-004 bar + threat model supply-chain section. Demonstrates tight feedback loop: ADRs inform decision frameworks; frameworks guide future issues.

**Quarterly companion review cadence established.** Burke now owns quarterly maintenance signal audits (recommended 2026-08-12). All 8 companions must remain within 6-month maintenance threshold or flagged for action. ADR-004 triage process lightweight (15 minutes per candidate) prevents ad-hoc decisions.

## Session 3: Wave 5 Release Pipeline + SemVer Policy + v0.1.0 Cut (2026-05-15)

Shipped the v0.1.0 release pipeline to make `uvx mcp-server-azure-architect` promise real. Created `.github/workflows/release.yml` with tag-triggered workflow: version verification, full test matrix, sdist+wheel build via `python -m build`, PyPI publish via OIDC (zero secrets), GitHub Release creation with CHANGELOG excerpt. Documented one-time PyPI trusted publishing setup in `docs/release.md` operator runbook.

Ratified ADR-005 (SemVer and Release Cadence): public surface is MCP tool names/params/returns, `mcp-config.json` schema, and ALZ manifest pinning policy. Skills NOT part of public surface (free to evolve). Pre-1.0: minor bumps for tool changes or ALZ refreshes, patch for fixes. As-needed cadence.

Created `CHANGELOG.md` with Keep-a-changelog format, v0.1.0 entry listing 5 tools, 1 skill, 4 ADRs, vendored ALZ snapshot (commit SHAs `e7641be` + `8a3fdda`), 7 companion servers, 6 branch protection checks, 5 per-client install docs. Bumped `pyproject.toml` version to 0.1.0.

Validated locally: pytest (41 green), ruff (clean), mypy (clean), `python -m build` (sdist+wheel built successfully). No em dashes. Decision artifact in `.squad/decisions/inbox/burke-release-pipeline.md`.

## Learnings

### PyPI OIDC Trusted Publishing Pattern

GitHub Actions can publish to PyPI without secrets via OIDC trusted publishing. Requires one-time setup: (1) Add pending publisher on PyPI with repo details + workflow name + environment name. (2) Create matching GitHub environment. (3) Use `pypa/gh-action-pypi-publish@release/v1` with `id-token: write` permission. First publish claims the package name, subsequent publishes are automatic. Zero secret rotation burden. Document the setup in operator runbook so first-time releasers have self-service path.

### Tag-Triggered Workflow Design

Release workflows should trigger on tag push (`on: push: tags: ['v*']`), not on branch push. This keeps the workflow out of PR CI (no required check noise). Version verification should be the first job: extract tag (strip `refs/tags/v` prefix) and `pyproject.toml` version, fail loudly if mismatch. Prevents accidental publishes with wrong version. Test suite runs as a required predecessor to build (no point building if tests fail). Changelog extraction via `awk` pattern to isolate the right section for GitHub Release body.

### SemVer Public Surface for MCP Servers

MCP server public surface = tool names, parameter names/types, return shapes, docstrings (act as schema docs). Skills are orchestration logic, not part of the tool contract, so they can evolve freely without version implications. Pre-1.0, minor bumps are acceptable for tool changes (low friction for early adopters, fast iteration). ALZ query refreshes = minor bumps (query content changes alter scorecard results, user-visible). `mcp-config.json` schema is also public surface (users depend on the structure).

## Team Update (2026-05-15)

Wave 5 release pipeline shipped. v0.1.0 ready for tag cut once PR merges and Lead approves. Pipeline tested with local build smoke test. One-time PyPI trusted publishing setup documented for first release. PR #16 (kit installer) in separate worktree, low conflict risk (different pyproject.toml sections).
