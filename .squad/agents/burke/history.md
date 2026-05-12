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

## Session 3: ADR-004 companion server selection bar (2026-05-13)

Formalized the 7-criterion companion selection bar used implicitly in PR #23. Wrote ADR-004 with detailed criteria, justification for all current companions, examples of rejected candidates (drawio-mcp, filesystem-mcp, azure-servicebus-mcp), triage process for new companions, and quarterly maintenance cadence. All companions in the kit pass the bar. Added worked example: azure-pricing-mcp evaluated against criteria and routed to native (issue #39) instead of companion, demonstrating the bar has bite. Validated ADR locally (ruff clean, pytest passing). Pushed to PR #37, added Copilot reviewer, decision artifact in `.squad/decisions/inbox/burke-adr-004.md`. Closes issue #8.

## Team Update (2026-05-13)

Wave 2 + Wave 3 foundation. Main: #22, #23, #26, #27, #33, #34 (Wave 2), PR #37 (ADR-004, pending merge). ADR-001 ratified. ADR-004 ready for approval. Remaining: ADR-002 (Atlas), ADR-003 + threat model (Sentinel), branch protection (#20), v0.1 docs (Sage).

## Learnings

### Formalized Companion Bar: The 7 Criteria

1. **Stable upstream:** semver tagged, no HEAD-only.
2. **Signed releases:** npm provenance, PyPI sigstore, Docker DCT, or GitHub checksums.
3. **Narrow scope:** single domain (diagrams, k8s, IaC, docs). No bloat, no general-purpose runtimes.
4. **Complementary to azure-mcp:** no duplication of ARG, Advisor, Monitor, Policy, RBAC, AKS, AppService, Key Vault, Storage.
5. **Maintenance signal:** last release ~6 months, or ALLOWED-VENDOR (Microsoft, HashiCorp, Google Cloud, AWS, Linux Foundation).
6. **Read-only by design or config:** mutations disabled in kit config.
7. **Documented install path:** user docs for at least one MCP client.

All current companions meet all 7 criteria. Rejection examples (drawio-mcp, filesystem-mcp, azure-servicebus-mcp) illustrate where candidates fail and why they are deferred.

### Lightweight Triage Process

Companion triage is 15 minutes per candidate: checklist against 7 criteria, post findings in issue, merge PR if all criteria pass. No ad-hoc decisions. Criterion failures are explicit (e.g., "Criterion 5 broken: last release 18 months ago; defer until upstream resumes").

### Supply Chain as a Decision Signal

Signed releases (npm provenance, Docker DCT) are not optional. They are a hard criterion. This filters out unsigned/unmaintained packages early and ensures reproducible user installs. Maintenance signals (6-month recency or ALLOWED-VENDOR status) prevent adoption of dormant upstreams.

### Read-Only Everywhere Requires Config Discipline

Even read-only-by-design companions (e.g., mermaid, drawio) must be audited: can a user accidentally configure them to mutate? Example: if a companion can be extended with custom tools that write, the kit config must not expose that. This discipline extends to all 8 companions in the curated kit.

### ADR Format: Pragmatic and Honest

Following ADR-001's format (context, decision, criteria scorecard, justification table, consequences, alternatives, references), ADR-004 is pragmatic and honest about trade-offs. Rejection examples are specific, not vague. Consequences name both benefits and costs. Alternatives are rejected with clear reasoning. This transparency builds trust in the bar and sets a precedent for future ADRs.

### Quarterly Maintenance Reviews are Non-Negotiable

Companion selection is not a one-time decision. Quarterly reviews of the compatibility matrix catch maintenance gaps early. If an upstream breaks the bar (e.g., no release in 6 months, security incident), the companion is flagged for update or removal. This requires standing commitment from Burke or designate.
