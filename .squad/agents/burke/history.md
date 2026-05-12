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
