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
## Session 3: Kit installer script (Issue #16, PR #16, 2026-05-12)

Delivered cross-platform kit installer (`scripts/install_kit.py`) that automates the onboarding flow for architects: prerequisite checks, client detection (Copilot CLI, Claude Desktop, Cursor, VS Code), config merge with collision handling, and auth smoke tests. Key decisions: Python (stdlib only) for cross-platform portability, MERGE strategy that preserves existing servers with interactive prompts on collision, and run-from-repo distribution (no console_script entry yet). Supports `--dry-run` for preview and `--non-interactive` for CI. Comprehensive test coverage (23 tests, all green). Updated README to show installer as canonical quickstart path. Decision artifact in `.squad/decisions/inbox/burke-kit-installer.md`.

### Learnings

**Installer merge strategy must preserve existing work.** Architects may already have custom MCP servers configured. Overwriting their config files would delete existing work and break workflows. Solution: MERGE new servers into existing config, prompt on name collision (interactive), or skip (non-interactive). Backup invalid JSON configs before starting fresh. This pattern applies to any tool that modifies user-managed config files.

**Stdlib-only Python scripts age better than scripted installers with dependencies.** Using only Python stdlib (no pip installs needed) means the installer runs anywhere Python 3.11+ is installed, with zero setup. No version conflicts, no `pip install installer-deps` step. For v0.1 tools where we're still learning user needs, stdlib-only reduces friction and maintenance burden.

**Dry-run mode is essential for config-modifying tools.** Architects want to preview changes before committing, especially when merging into existing configs. `--dry-run` flag (prints merged JSON to stdout, touches no files) provides confidence and aids debugging. Standard pattern for infra tools (Terraform plan, Ansible check mode).

## Session 4: Azure MCP Repository Move and Read-Only Flag (Issue #92, PR #108, 2026-05-15)

Fixed live correctness defect: Microsoft archived `Azure/azure-mcp` on 2026-02-06 and consolidated development into `microsoft/mcp/servers/Azure.Mcp.Server`. Updated all docs to reference new canonical location. Added `--read-only` flag by default to `.copilot/mcp-config.json`, plus documented `--mode namespace` and `--namespace` whitelisting knobs for context-cost optimization.

Three files changed: `docs/companions/azure-mcp.md` (new "Recommended Client Flags" section with usage examples), `.copilot/mcp-config.json` (`--read-only` added to azure-mcp args), `docs/adr/0004-companion-server-bar.md` (addendum noting archive date and repository move). PR #108 created on branch `burke/92-azure-mcp-repoint-v2`. Per Lead synthesis 2026-05-15 section 1 (Bug 2.D) and Sage research finding B.2.

## Session 5: AKS-MCP Mutation Hazard Documentation (Issue #101, 2026-05-XX)

Closed issue #101 by documenting the AKS-MCP mutation hazard as a worked example of why Criterion 6 (Read-Only by Design or Config) is essential for companion selection.

**Changes:**
1. **docs/companions/kubernetes.md**: Added prominent ⚠️ "Hazard: Mutation-Capable Alternatives (AKS-MCP)" section explaining why Azure/aks-mcp is dangerous (arbitrary `call_az`/`call_kubectl` tools, configurable `--access-level` flag), why we deliberately chose the narrower `kubernetes-mcp-server` instead (read-only by design), and detailed mitigation steps if users choose to wire AKS-MCP anyway (explicit `--access-level readonly` flag + per-tool gating in MCP client).
2. **docs/companions/azure-mcp.md**: Added "Related Companions and Hazards" section with cross-link to the AKS-MCP hazard section, directing readers away from AKS-MCP and explaining our read-only choice.
3. **docs/adr/0004-companion-server-bar.md**: Added new addendum "Criterion 6 Worked Example: AKS-MCP Mutation Hazard" explaining that AKS-MCP is a real-world example of why read-only-by-default matters when wiring companion servers into AI-driven tools that may invoke tools without explicit confirmation.

**Validation:**
- Relative markdown links verified (cross-links use correct paths: `kubernetes.md#anchor` from azure-mcp.md, `../companions/kubernetes.md#anchor` from ADR-0004).
- No Python code blocks in changes (all documentation).
- Tone: factual, not alarmist. Hazard is real but mitigation is straightforward.

**Acceptance Criteria Met:**
1. ✅ Located kubernetes/AKS companion doc at `docs/companions/kubernetes.md`.
2. ✅ Added prominent ⚠️ hazard section near top with specific tool names (`call_az`, `call_kubectl`), ADR-003 citation, and detailed mitigation steps.
3. ✅ Added smaller note in ADR-0004 as worked example of Criterion 6 importance with cross-link.
4. ✅ Cross-linked from azure-mcp.md "Related Companions" section.
5. ✅ Validated markdown links (relative paths verified).

PR created on branch `burke/101-aks-mcp-hazard`.

## Session 6: Public-Surface Cleanup - Remove Squad Workflow Leakage (2026-05-13)

Executed audit-driven cleanup of user-facing docs to remove Squad internal workflow references. Martin Opedal flagged that squad-specific language was leaking onto PyPI / MCP Registry public surfaces. Completed four targeted edits per audit findings:

1. **README.md line 48 (Status section):** Dropped `squad` label mention and added link to [v0.2 roadmap](docs/planning/v0.2.md).
2. **README.md lines 61-63:** Removed entire "## Squad" section (Squad is internal workflow documented in AGENTS.md for maintainers only, not user-facing).
3. **README.md line 21 (What's in scope):** Fixed tool count from six to seven, adding `pricing_estimate_workload` (added in PR #87, Wave 8). Confirmed PR #87 commit history.
4. **docs/release.md line 165 (Contact section):** Removed `squad:burke` label reference from release runbook.

Validation: ruff lint passed (no Python touched, doc-only changes). Git workflow: created branch `chore/readme-public-surface`, committed with trailer, pushed, and opened PR #120. No AGENTS.md changes needed (already comprehensive for maintainers). All cleanup validated against audit findings. Decision: keep AGENTS.md Squad section as-is; it's authoritative for team internal workflow. User-facing surface now scrubbed.

